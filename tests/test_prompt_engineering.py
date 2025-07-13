"""Tests for prompt engineering functionality."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from src.prompt_engineering import PromptManager, PromptTemplate


class TestPromptManager:
    """Test prompt template management."""
    
    @pytest.fixture
    def temp_prompts_dir(self):
        """Create temporary directory for prompts."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def prompt_manager(self, temp_prompts_dir):
        """Create prompt manager with temp directory."""
        return PromptManager(prompts_dir=temp_prompts_dir)
    
    def test_builtin_templates(self, prompt_manager):
        """Test that built-in templates are loaded."""
        templates = prompt_manager.list_templates()
        assert len(templates) >= 4  # At least 4 built-in templates
        
        # Check standard template exists
        standard = prompt_manager.get_template("standard")
        assert standard is not None
        assert standard.name == "standard"
        assert "{board_state}" in standard.template
    
    def test_create_and_save_template(self, prompt_manager, temp_prompts_dir):
        """Test creating and saving a template."""
        template = PromptTemplate(
            name="test_template",
            template="Test {board_state} template",
            description="Test template",
            tags=["test"],
        )
        
        prompt_manager.save_template(template)
        
        # Check it was saved
        saved = prompt_manager.get_template("test_template")
        assert saved is not None
        assert saved.name == "test_template"
        assert saved.template == "Test {board_state} template"
        
        # Check file exists
        assert (temp_prompts_dir / "test_template.json").exists()
    
    def test_template_formatting(self, prompt_manager):
        """Test template formatting with parameters."""
        template = PromptTemplate(
            name="format_test",
            template="Board:\n{board_state}\n\nHint: {hint}",
            description="Formatting test",
            parameters={"board_state": "", "hint": "Think carefully"},
        )
        
        # Format with custom values
        formatted = template.format(
            board_state="? ? ?\n1 2 1\n. . .",
            hint="Check patterns",
        )
        
        assert "? ? ?" in formatted
        assert "Check patterns" in formatted
    
    def test_template_with_examples(self, prompt_manager):
        """Test template with few-shot examples."""
        template = PromptTemplate(
            name="example_test",
            template="Make your move:\n{board_state}",
            description="Template with examples",
            few_shot_examples=[
                {
                    "board": "? 1 .\n? 2 1\n? 1 .",
                    "action": "reveal (0, 0)",
                    "reasoning": "Corner with 1 adjacent mine",
                },
            ],
        )
        
        formatted = template.format(board_state="test board")
        assert "Examples:" in formatted
        assert "Example 1:" in formatted
        assert "reveal (0, 0)" in formatted
    
    def test_list_templates_by_tag(self, prompt_manager):
        """Test filtering templates by tag."""
        # Add custom template with specific tag
        template = PromptTemplate(
            name="tagged_test",
            template="Test",
            description="Tagged template",
            tags=["special", "test"],
        )
        prompt_manager.save_template(template)
        
        # Filter by tag
        special_templates = prompt_manager.list_templates(tags=["special"])
        assert len(special_templates) >= 1
        assert any(t.name == "tagged_test" for t in special_templates)
        
        # Filter by non-existent tag
        empty = prompt_manager.list_templates(tags=["nonexistent"])
        assert len(empty) == 0
    
    def test_create_variation(self, prompt_manager):
        """Test creating template variations."""
        # Create variation of standard template
        variation = prompt_manager.create_variation(
            base_template="standard",
            name="standard_v2",
            modifications={
                "description": "Modified standard template",
                "tags": ["modified"],
            },
        )
        
        assert variation.name == "standard_v2"
        assert "modified" in variation.tags
        assert variation.description == "Modified standard template"
        
        # Template content should be from base by default
        base = prompt_manager.get_template("standard")
        assert variation.template == base.template
    
    def test_update_performance_metrics(self, prompt_manager):
        """Test updating template performance metrics."""
        template = PromptTemplate(
            name="perf_test",
            template="Test template",
            description="Performance test",
        )
        prompt_manager.save_template(template)
        
        # Update metrics
        prompt_manager.update_performance(
            "perf_test",
            {"win_rate": 0.75, "avg_moves": 25.3},
        )
        
        # Check metrics were saved
        updated = prompt_manager.get_template("perf_test")
        assert updated.performance_metrics["win_rate"] == 0.75
        assert updated.performance_metrics["avg_moves"] == 25.3
    
    def test_template_hash(self):
        """Test template content hashing."""
        template1 = PromptTemplate(
            name="hash1",
            template="Test template content",
            description="Hash test",
        )
        
        template2 = PromptTemplate(
            name="hash2",
            template="Test template content",  # Same content
            description="Hash test 2",
        )
        
        template3 = PromptTemplate(
            name="hash3",
            template="Different content",
            description="Hash test 3",
        )
        
        # Same content should have same hash
        assert template1.hash == template2.hash
        
        # Different content should have different hash
        assert template1.hash != template3.hash
    
    def test_invalid_template_name(self, prompt_manager):
        """Test handling of invalid template names."""
        result = prompt_manager.get_template("nonexistent")
        assert result is None
        
        # Test creating variation of non-existent base
        with pytest.raises(ValueError, match="not found"):
            prompt_manager.create_variation(
                base_template="nonexistent",
                name="new_variation",
                modifications={},
            )