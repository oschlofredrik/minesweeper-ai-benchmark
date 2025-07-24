# Dynamic Evaluation System for Tilts Platform

## Overview
A fully dynamic, database-driven evaluation system that allows administrators to create, modify, and compose evaluation metrics without code changes. Incorporates best practices from AI evaluation research, including KORGym's multi-dimensional scoring approach.

## Core Components

### 1. Evaluation Engine Framework
The heart of the system - interprets evaluation definitions from the database and executes them dynamically.

### 2. Scoring Types (KORGym-Inspired)
- **Binary Scoring**: Win/lose conditions (e.g., accuracy >= 0.9)
- **Proportional Scoring**: Partial success metrics (e.g., correct_items / total_items)
- **Cumulative Scoring**: Point accumulation with rules

### 3. Normalization System
Implements KORGym's normalization approach for fair cross-game comparison:
- Log transformation for scores > 1
- Min-max normalization
- Dimension-based aggregation

### 4. Multi-Dimensional Evaluation
Support for multiple evaluation dimensions:
- Accuracy
- Reasoning quality
- Speed
- Token efficiency
- Creativity
- Consistency
- Safety compliance
- Custom dimensions (e.g., "architectural absurdity" for Norm mode)

### 5. Rule Types
- **Pattern-Based Rules**: Detect specific behaviors using regex or keywords
- **Metric-Based Rules**: Threshold scoring based on metrics
- **Cross-Round Analysis**: Track evolution across rounds
- **Custom Expressions**: Mathematical formulas for complex scoring

## Database Schema

```sql
-- Core evaluation definitions
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0',
    scoring_type VARCHAR(50) CHECK (scoring_type IN ('binary', 'proportional', 'cumulative')),
    rules JSONB NOT NULL,
    normalization_config JSONB,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT false,
    category VARCHAR(100),
    tags TEXT[]
);

-- Evaluation templates for marketplace
CREATE TABLE evaluation_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID REFERENCES evaluations(id),
    downloads INTEGER DEFAULT 0,
    rating DECIMAL(3,2),
    featured BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game session evaluation configuration
CREATE TABLE game_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_session_id UUID NOT NULL,
    evaluation_id UUID REFERENCES evaluations(id),
    weight DECIMAL(3,2) CHECK (weight >= 0 AND weight <= 1),
    dimension VARCHAR(100),
    config_overrides JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evaluation results with detailed breakdown
CREATE TABLE evaluation_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_session_id UUID NOT NULL,
    player_id UUID NOT NULL,
    evaluation_id UUID REFERENCES evaluations(id),
    round_number INTEGER,
    raw_score DECIMAL,
    normalized_score DECIMAL,
    rule_breakdown JSONB,
    dimension_scores JSONB,
    context_snapshot JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evaluation ratings and reviews
CREATE TABLE evaluation_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID REFERENCES evaluations(id),
    user_id UUID NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Example Evaluation Definitions

### Speed Demon Evaluation
```json
{
  "name": "Speed Demon",
  "scoring_type": "proportional",
  "rules": [
    {
      "type": "metric_threshold",
      "metric": "response_time",
      "thresholds": [
        {"operator": "<", "value": 10, "score": 100},
        {"operator": "<", "value": 30, "score_formula": "100 * (1 - (response_time - 10) / 20)"},
        {"default": true, "score": 0}
      ]
    }
  ],
  "normalization_config": {
    "method": "min_max",
    "apply_log": false
  }
}
```

### Norm MacDonald Classic Evaluation
```json
{
  "name": "Norm MacDonald Classic",
  "scoring_type": "cumulative",
  "rules": [
    {
      "type": "pattern_detection",
      "patterns": [
        {
          "name": "year_mention_1970s",
          "regex": "\\b197[0-9]\\b",
          "score": 10,
          "category": "temporal_specificity"
        },
        {
          "name": "medical_reference",
          "keywords": ["podiatrist", "medical", "doctor", "physician"],
          "score": 15,
          "category": "professional_absurdity"
        }
      ]
    },
    {
      "type": "cross_round_analysis",
      "track": "entity_mentions",
      "scoring": {
        "callback_detected": 25,
        "escalation_detected": 30,
        "consistency_bonus": 20
      }
    },
    {
      "type": "penalty",
      "patterns": [
        {
          "keywords": ["funny", "humor", "joke", "comedy"],
          "penalty": -50,
          "reason": "Breaking character"
        }
      ]
    }
  ],
  "max_score": 100,
  "normalization_config": {
    "method": "percentage_of_max"
  }
}
```

### Scientific Rigor Evaluation
```json
{
  "name": "Scientific Rigor Pro",
  "scoring_type": "cumulative",
  "rules": [
    {
      "type": "pattern_detection",
      "patterns": [
        {
          "name": "confidence_interval",
          "regex": "\\b\\d+%\\s*(confidence|CI)\\b",
          "score": 20
        },
        {
          "name": "methodology_mention",
          "keywords": ["methodology", "method", "approach", "technique"],
          "score": 15
        }
      ]
    },
    {
      "type": "custom_expression",
      "name": "assumption_ratio",
      "expression": "min(assumptions_stated / expected_assumptions, 1) * 30",
      "required_context": ["assumptions_stated", "expected_assumptions"]
    }
  ]
}
```

## Evaluation Context Structure

```python
evaluation_context = {
    # Current round data
    "prompt": str,
    "response": str,
    "metadata": {
        "response_time": float,
        "token_count": int,
        "model_used": str,
        "timestamp": datetime,
        "round_number": int
    },
    
    # Historical data
    "round_history": [
        {
            "round_number": int,
            "prompt": str,
            "response": str,
            "scores": dict,
            "entities_mentioned": list,
            "patterns_detected": dict
        }
    ],
    
    # Game context
    "game_config": dict,
    "player_info": dict,
    "session_id": str,
    
    # Custom metrics (game-specific)
    "custom_metrics": dict
}
```

## Implementation Phases

### Phase 1: Core Framework (Week 1-2)
1. Build evaluation engine with rule interpreter
2. Implement KORGym-style normalization
3. Create context system
4. Set up database schema

### Phase 2: Builder Interface (Week 3-4)
1. Visual rule builder
2. Expression language parser
3. Testing sandbox
4. Import/export functionality

### Phase 3: Advanced Features (Week 5-6)
1. Cross-round analysis engine
2. Multi-dimensional aggregation
3. Performance visualizations
4. Marketplace infrastructure

### Phase 4: Community Features (Week 7-8)
1. Evaluation sharing system
2. Forking and versioning
3. Rating and review system
4. Documentation generator

## Key Features

### No Hardcoded Metrics
Everything is database-driven, allowing complete flexibility without code changes.

### Scientific Rigor
Incorporates proven normalization methods from academic research.

### Community-Driven
Marketplace for sharing and discovering evaluation templates.

### Transparent Scoring
Detailed breakdowns showing exactly how scores are calculated.

### Version Control
Track evaluation evolution over time with full version history.

## API Endpoints

```
# Evaluation Management
POST   /api/evaluations                    # Create new evaluation
GET    /api/evaluations                    # List evaluations
GET    /api/evaluations/{id}               # Get evaluation details
PUT    /api/evaluations/{id}               # Update evaluation
DELETE /api/evaluations/{id}               # Delete evaluation

# Evaluation Execution
POST   /api/evaluations/{id}/test          # Test evaluation with sample data
POST   /api/evaluations/{id}/execute       # Execute evaluation in game context

# Marketplace
GET    /api/marketplace/evaluations        # Browse marketplace
POST   /api/marketplace/{id}/import        # Import evaluation
POST   /api/marketplace/{id}/rate          # Rate evaluation
GET    /api/marketplace/trending           # Get trending evaluations

# Game Integration
POST   /api/games/{id}/evaluations         # Attach evaluations to game
GET    /api/games/{id}/evaluations         # Get game evaluations
POST   /api/games/{id}/evaluate            # Run evaluations for game session
```

## Benefits

1. **Flexibility**: Create any evaluation type without touching code
2. **Standardization**: Based on proven AI evaluation research
3. **Community**: Share and discover evaluation strategies
4. **Transparency**: Players understand exactly how they're scored
5. **Evolution**: Evaluations can be updated without breaking games
6. **Analytics**: Rich data for understanding AI model performance