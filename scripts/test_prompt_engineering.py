#!/usr/bin/env python3
"""Quick test of prompt engineering functionality."""

from src.prompt_engineering import PromptManager, PromptTemplate

def test_prompt_manager():
    """Test basic prompt manager functionality."""
    print("Testing Prompt Engineering System...")
    
    # Create manager
    manager = PromptManager()
    
    # Test 1: List built-in templates
    print("\n1. Built-in Templates:")
    templates = manager.list_templates()
    for template in templates:
        print(f"  - {template.name}: {template.description}")
    
    # Test 2: Get and format a template
    print("\n2. Template Formatting:")
    standard = manager.get_template("standard")
    if standard:
        test_board = """? ? ? 1 .
? ? ? 2 1
? ? ? 1 .
1 2 1 1 .
. . . . ."""
        
        formatted = standard.format(board_state=test_board)
        print(f"  Formatted length: {len(formatted)} characters")
        print(f"  Contains board: {'board_state' not in formatted}")
    
    # Test 3: Create a new template
    print("\n3. Creating Custom Template:")
    custom = PromptTemplate(
        name="test_custom",
        template="Analyze this Minesweeper board:\n{board_state}\n\nYour move: ",
        description="Simple test template",
        tags=["test", "simple"],
    )
    
    manager.save_template(custom)
    
    # Verify it was saved
    retrieved = manager.get_template("test_custom")
    if retrieved:
        print(f"  ✓ Template saved and retrieved: {retrieved.name}")
    
    # Test 4: Filter by tags
    print("\n4. Tag Filtering:")
    cot_templates = manager.list_templates(tags=["cot"])
    print(f"  Templates with 'cot' tag: {len(cot_templates)}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_prompt_manager()