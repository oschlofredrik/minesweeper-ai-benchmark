"""
Dynamic Evaluation Engine for Tilts Platform

This engine interprets evaluation definitions from the database and executes them
dynamically, supporting multiple scoring types and normalization methods.
"""

import re
import json
import math
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import numpy as np
from abc import ABC, abstractmethod


class ScoringType(Enum):
    """Types of scoring methods available"""
    BINARY = "binary"
    PROPORTIONAL = "proportional"
    CUMULATIVE = "cumulative"


class RuleType(Enum):
    """Types of evaluation rules"""
    PATTERN_DETECTION = "pattern_detection"
    METRIC_THRESHOLD = "metric_threshold"
    CROSS_ROUND_ANALYSIS = "cross_round_analysis"
    CUSTOM_EXPRESSION = "custom_expression"
    PENALTY = "penalty"


@dataclass
class EvaluationResult:
    """Result of an evaluation execution"""
    evaluation_id: str
    raw_score: float
    normalized_score: float
    rule_breakdown: Dict[str, Any]
    dimension_scores: Dict[str, float]
    metadata: Dict[str, Any]


@dataclass
class EvaluationContext:
    """Context provided to evaluation engine"""
    prompt: str
    response: str
    metadata: Dict[str, Any]
    round_history: List[Dict[str, Any]]
    game_config: Dict[str, Any]
    player_info: Dict[str, Any]
    session_id: str
    custom_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}


class Rule(ABC):
    """Abstract base class for evaluation rules"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.type = RuleType(config.get("type"))
    
    @abstractmethod
    def evaluate(self, context: EvaluationContext) -> Dict[str, Any]:
        """Evaluate the rule against the context"""
        pass


class PatternDetectionRule(Rule):
    """Detects patterns in text using regex or keywords"""
    
    def evaluate(self, context: EvaluationContext) -> Dict[str, Any]:
        total_score = 0
        matches = []
        
        patterns = self.config.get("patterns", [])
        
        for pattern in patterns:
            pattern_score = 0
            pattern_matches = []
            
            # Check regex patterns
            if "regex" in pattern:
                regex = re.compile(pattern["regex"], re.IGNORECASE)
                found = regex.findall(context.response)
                if found:
                    pattern_score = pattern.get("score", 0) * len(found)
                    pattern_matches.extend(found)
            
            # Check keywords
            if "keywords" in pattern:
                for keyword in pattern["keywords"]:
                    if keyword.lower() in context.response.lower():
                        pattern_score += pattern.get("score", 0)
                        pattern_matches.append(keyword)
            
            if pattern_matches:
                matches.append({
                    "name": pattern.get("name", "unnamed"),
                    "matches": pattern_matches,
                    "score": pattern_score,
                    "category": pattern.get("category", "general")
                })
                total_score += pattern_score
        
        return {
            "score": total_score,
            "matches": matches,
            "type": "pattern_detection"
        }


class MetricThresholdRule(Rule):
    """Evaluates metrics against thresholds"""
    
    def evaluate(self, context: EvaluationContext) -> Dict[str, Any]:
        metric_name = self.config.get("metric")
        metric_value = context.metadata.get(metric_name, 0)
        
        thresholds = self.config.get("thresholds", [])
        score = 0
        applied_threshold = None
        
        for threshold in thresholds:
            if "default" in threshold and threshold["default"]:
                score = threshold.get("score", 0)
                applied_threshold = "default"
                continue
                
            operator = threshold.get("operator")
            value = threshold.get("value")
            
            if self._check_threshold(metric_value, operator, value):
                if "score" in threshold:
                    score = threshold["score"]
                elif "score_formula" in threshold:
                    # Evaluate formula with metric value in context
                    score = self._evaluate_formula(
                        threshold["score_formula"], 
                        {metric_name: metric_value}
                    )
                applied_threshold = f"{operator} {value}"
                break
        
        return {
            "score": score,
            "metric": metric_name,
            "value": metric_value,
            "threshold_applied": applied_threshold,
            "type": "metric_threshold"
        }
    
    def _check_threshold(self, value: float, operator: str, threshold: float) -> bool:
        """Check if value meets threshold condition"""
        operators = {
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
            ">": lambda x, y: x > y,
            ">=": lambda x, y: x >= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y
        }
        return operators.get(operator, lambda x, y: False)(value, threshold)
    
    def _evaluate_formula(self, formula: str, variables: Dict[str, float]) -> float:
        """Safely evaluate a mathematical formula"""
        # Replace variables in formula
        for var, value in variables.items():
            formula = formula.replace(var, str(value))
        
        # Safe evaluation using only math operations
        allowed_names = {
            k: v for k, v in math.__dict__.items() 
            if not k.startswith("__")
        }
        allowed_names.update({"min": min, "max": max, "abs": abs})
        
        try:
            return eval(formula, {"__builtins__": {}}, allowed_names)
        except:
            return 0


class CrossRoundAnalysisRule(Rule):
    """Analyzes patterns across multiple rounds"""
    
    def evaluate(self, context: EvaluationContext) -> Dict[str, Any]:
        track_field = self.config.get("track", "entities")
        scoring = self.config.get("scoring", {})
        
        current_entities = self._extract_entities(context.response, track_field)
        callbacks = []
        escalations = []
        consistency_score = 0
        
        # Analyze against history
        for round_data in context.round_history:
            historical_entities = round_data.get(track_field, [])
            
            # Check for callbacks
            for entity in current_entities:
                if entity in historical_entities:
                    callbacks.append({
                        "entity": entity,
                        "round": round_data["round_number"],
                        "score": scoring.get("callback_detected", 0)
                    })
            
            # Check for escalation (building on previous)
            if len(current_entities) > len(historical_entities):
                escalations.append({
                    "round": round_data["round_number"],
                    "score": scoring.get("escalation_detected", 0)
                })
        
        # Calculate consistency
        if context.round_history:
            entity_counts = [len(r.get(track_field, [])) for r in context.round_history]
            entity_counts.append(len(current_entities))
            consistency_score = scoring.get("consistency_bonus", 0) * (
                1 - np.std(entity_counts) / (np.mean(entity_counts) + 1)
            )
        
        total_score = (
            sum(cb["score"] for cb in callbacks) +
            sum(esc["score"] for esc in escalations) +
            consistency_score
        )
        
        return {
            "score": total_score,
            "callbacks": callbacks,
            "escalations": escalations,
            "consistency_score": consistency_score,
            "current_entities": current_entities,
            "type": "cross_round_analysis"
        }
    
    def _extract_entities(self, text: str, entity_type: str) -> List[str]:
        """Extract entities from text based on type"""
        # Simple extraction - can be enhanced with NLP
        if entity_type == "entity_mentions":
            # Extract capitalized words as potential entities
            return list(set(re.findall(r'\b[A-Z][a-z]+\b', text)))
        elif entity_type == "year_mentions":
            return re.findall(r'\b\d{4}\b', text)
        else:
            return []


class PenaltyRule(Rule):
    """Applies penalties for certain patterns"""
    
    def evaluate(self, context: EvaluationContext) -> Dict[str, Any]:
        total_penalty = 0
        penalties_applied = []
        
        patterns = self.config.get("patterns", [])
        
        for pattern in patterns:
            if "keywords" in pattern:
                for keyword in pattern["keywords"]:
                    if keyword.lower() in context.response.lower():
                        penalty = pattern.get("penalty", 0)
                        total_penalty += penalty
                        penalties_applied.append({
                            "keyword": keyword,
                            "penalty": penalty,
                            "reason": pattern.get("reason", "Penalty applied")
                        })
        
        return {
            "score": total_penalty,  # Negative score
            "penalties": penalties_applied,
            "type": "penalty"
        }


class DynamicEvaluationEngine:
    """Main evaluation engine that orchestrates rule execution"""
    
    def __init__(self):
        self.rule_classes = {
            RuleType.PATTERN_DETECTION: PatternDetectionRule,
            RuleType.METRIC_THRESHOLD: MetricThresholdRule,
            RuleType.CROSS_ROUND_ANALYSIS: CrossRoundAnalysisRule,
            RuleType.PENALTY: PenaltyRule
        }
    
    def evaluate(
        self, 
        evaluation_config: Dict[str, Any], 
        context: EvaluationContext
    ) -> EvaluationResult:
        """Execute an evaluation against the provided context"""
        
        scoring_type = ScoringType(evaluation_config.get("scoring_type", "proportional"))
        rules = evaluation_config.get("rules", [])
        
        # Execute all rules
        rule_results = []
        total_raw_score = 0
        
        for rule_config in rules:
            rule_type = RuleType(rule_config["type"])
            if rule_type in self.rule_classes:
                rule = self.rule_classes[rule_type](rule_config)
                result = rule.evaluate(context)
                rule_results.append(result)
                total_raw_score += result["score"]
        
        # Apply scoring type logic
        if scoring_type == ScoringType.BINARY:
            success_condition = evaluation_config.get("success_condition", "score > 0")
            score_mapping = evaluation_config.get(
                "score_mapping", 
                {"success": 1.0, "failure": 0.0}
            )
            # Evaluate condition
            final_score = score_mapping["success"] if total_raw_score > 0 else score_mapping["failure"]
        
        elif scoring_type == ScoringType.PROPORTIONAL:
            max_score = evaluation_config.get("max_score", 100)
            final_score = min(total_raw_score / max_score, 1.0) if max_score > 0 else 0
        
        else:  # CUMULATIVE
            max_score = evaluation_config.get("max_score", 100)
            final_score = min(total_raw_score, max_score)
        
        # Apply normalization
        normalized_score = self._normalize_score(
            final_score, 
            evaluation_config.get("normalization_config", {})
        )
        
        # Extract dimension scores
        dimension_scores = self._calculate_dimension_scores(
            rule_results, 
            evaluation_config.get("dimensions", {})
        )
        
        return EvaluationResult(
            evaluation_id=evaluation_config.get("id", "unknown"),
            raw_score=total_raw_score,
            normalized_score=normalized_score,
            rule_breakdown=rule_results,
            dimension_scores=dimension_scores,
            metadata={
                "scoring_type": scoring_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "context_metadata": context.metadata
            }
        )
    
    def _normalize_score(self, score: float, config: Dict[str, Any]) -> float:
        """Apply normalization to score based on KORGym approach"""
        method = config.get("method", "none")
        
        if method == "none":
            return score
        
        # Log transformation for scores > 1
        if config.get("apply_log", True) and score > 1:
            score = math.log(1 + score)
        
        if method == "min_max":
            # Would need historical scores for proper min-max
            # For now, assume 0-100 range
            min_score = config.get("min", 0)
            max_score = config.get("max", 100)
            if max_score > min_score:
                return (score - min_score) / (max_score - min_score)
            return 0.5
        
        elif method == "percentage_of_max":
            max_possible = config.get("max_possible", 100)
            return min(score / max_possible, 1.0) if max_possible > 0 else 0
        
        return score
    
    def _calculate_dimension_scores(
        self, 
        rule_results: List[Dict[str, Any]], 
        dimension_config: Dict[str, Any]
    ) -> Dict[str, float]:
        """Map rule results to evaluation dimensions"""
        dimensions = {}
        
        for result in rule_results:
            # Map based on rule type or category
            if "category" in result:
                category = result["category"]
                if category not in dimensions:
                    dimensions[category] = 0
                dimensions[category] += result["score"]
        
        return dimensions
    
    def test_evaluation(
        self, 
        evaluation_config: Dict[str, Any], 
        test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test an evaluation with sample data"""
        # Create a test context
        context = EvaluationContext(
            prompt=test_data.get("prompt", "Test prompt"),
            response=test_data.get("response", "Test response"),
            metadata=test_data.get("metadata", {"response_time": 15}),
            round_history=test_data.get("round_history", []),
            game_config={},
            player_info={},
            session_id="test-session"
        )
        
        result = self.evaluate(evaluation_config, context)
        
        return {
            "success": True,
            "result": {
                "raw_score": result.raw_score,
                "normalized_score": result.normalized_score,
                "rule_breakdown": result.rule_breakdown,
                "dimension_scores": result.dimension_scores
            }
        }


# Example usage
if __name__ == "__main__":
    # Create engine
    engine = DynamicEvaluationEngine()
    
    # Load evaluation config (would come from database)
    evaluation_config = {
        "id": "speed-demon",
        "name": "Speed Demon",
        "scoring_type": "proportional",
        "rules": [
            {
                "type": "metric_threshold",
                "metric": "response_time",
                "thresholds": [
                    {"operator": "<", "value": 10, "score": 100},
                    {"operator": "<", "value": 30, "score_formula": "100 * (1 - (response_time - 10) / 20)"},
                    {"default": True, "score": 0}
                ]
            }
        ],
        "max_score": 100,
        "normalization_config": {
            "method": "percentage_of_max",
            "max_possible": 100
        }
    }
    
    # Create test context
    test_context = EvaluationContext(
        prompt="Analyze this data",
        response="Here's my analysis...",
        metadata={"response_time": 15},
        round_history=[],
        game_config={},
        player_info={},
        session_id="test-123"
    )
    
    # Run evaluation
    result = engine.evaluate(evaluation_config, test_context)
    print(f"Score: {result.normalized_score}")
    print(f"Breakdown: {json.dumps(result.rule_breakdown, indent=2)}")