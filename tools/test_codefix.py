# tools/test_codefix.py
"""Test code analysis and file editing with safety confirmations."""

import os
import sys
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.editor import FileEditor


def test_file_editor_basic():
    """Test basic file operations."""
    print("\n=== Test: File Editor - Basic Operations ===")
    
    editor = FileEditor(auto_backup=True)
    
    # Create temp directory for tests
    test_dir = os.path.join(tempfile.gettempdir(), "ai_assistant_test")
    os.makedirs(test_dir, exist_ok=True)
    
    test_file = os.path.join(test_dir, "test_file.py")
    
    try:
        # Test write
        content = '''def hello():
    print("Hello, World!")
    
def add(a, b):
    return a + b
'''
        success = editor.write_file(test_file, content, backup=False)
        print(f"Write file: {'OK' if success else 'FAILED'}")
        
        # Test read
        read_content = editor.read_file(test_file)
        print(f"Read file: {'OK' if read_content == content else 'FAILED'}")
        
        # Test backup and edit
        new_content = content.replace("Hello, World!", "Hello, AI!")
        success, msg, diff = editor.apply_patch(test_file, new_content)
        print(f"Apply patch: {msg}")
        if diff:
            print(f"Diff preview:\n{diff[:200]}...")
        
        # Test backup history
        history = editor.get_backup_history()
        print(f"Backup history: {len(history)} entries")
        
        # Test rollback
        if history:
            success = editor.rollback(test_file)
            print(f"Rollback: {'OK' if success else 'FAILED'}")
            
            rolled_back = editor.read_file(test_file)
            print(f"Rollback verification: {'OK' if 'Hello, World!' in rolled_back else 'FAILED'}")
        
        # Test search
        matches = editor.search_in_file(test_file, "def")
        print(f"Search 'def': Found {len(matches)} matches")
        
        # Test replace
        num_replaced = editor.replace_in_file(test_file, "World", "Universe")
        print(f"Replace 'World' -> 'Universe': {num_replaced} replacements")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)


def test_code_analysis():
    """Test code analysis with diff generation."""
    print("\n=== Test: Code Analysis & Diff ===")
    
    editor = FileEditor()
    
    # Simulate buggy code
    buggy_code = '''def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)  # Bug: crashes on empty list

def greet(name):
    print("Hello " + name)  # Works but could be f-string
'''

    # Simulated fix
    fixed_code = '''def calculate_average(numbers):
    if not numbers:
        return 0
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)

def greet(name):
    print(f"Hello {name}")
'''

    diff = editor.generate_diff(buggy_code, fixed_code, "example.py")
    print("Generated diff:")
    print(diff)
    
    return True


def test_safety_confirmation():
    """Test safety confirmation flow."""
    print("\n=== Test: Safety Confirmation ===")
    
    try:
        from safety.confirmations import (
            ConfirmationManager, 
            ConfirmationResult,
            is_dangerous_action,
            contains_dangerous_keywords
        )
        
        # Test dangerous action detection
        dangerous_types = ['delete_file', 'run_command', 'shutdown', 'edit_file']
        safe_types = ['read_file', 'screenshot', 'open_url', 'search']
        
        print("Dangerous action detection:")
        for t in dangerous_types:
            result = is_dangerous_action(t)
            print(f"  {t}: {'DANGEROUS' if result else 'safe'}")
        
        for t in safe_types:
            result = is_dangerous_action(t)
            print(f"  {t}: {'DANGEROUS' if result else 'safe'}")
        
        # Test keyword detection
        print("\nDangerous keyword detection:")
        test_texts = [
            "delete all files",
            "open notepad",
            "shutdown the computer",
            "search for cats",
            "rm -rf /",
        ]
        for text in test_texts:
            result = contains_dangerous_keywords(text)
            print(f"  '{text}': {'DANGEROUS' if result else 'safe'}")
        
        # Test confirmation manager (quick, non-blocking)
        print("\nConfirmation manager:")
        manager = ConfirmationManager(default_timeout=2.0)
        
        # Simulate immediate response
        manager.request_confirmation("test action")
        result = manager.respond("yes")
        print(f"  Response 'yes': {result.value}")
        
        manager.request_confirmation("another action")
        result = manager.respond("no")
        print(f"  Response 'no': {result.value}")
        
        manager.request_confirmation("unclear action")
        result = manager.respond("maybe")
        print(f"  Response 'maybe': {result.value} (should be denied)")
        
        return True
        
    except ImportError as e:
        print(f"Safety module not available: {e}")
        return False


def run_all_tests():
    """Run all code fix tests."""
    print("=" * 60)
    print("AI Desktop Assistant - Code Fix System Tests")
    print("=" * 60)
    
    results = {}
    
    results['file_editor'] = test_file_editor_basic()
    results['code_analysis'] = test_code_analysis()
    results['safety'] = test_safety_confirmation()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return all_passed


if __name__ == "__main__":
    run_all_tests()
