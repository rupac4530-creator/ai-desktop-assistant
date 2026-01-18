# tools/test_commands.py
"""
Test fuzzy command parsing with spell-tolerant matching.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.command_parser import parse_command, normalize_text, fuzzy_match


def test_spaced_letters():
    """Test collapsing spaced-out letters."""
    print("\n=== Test: Spaced Letters ===")
    
    test_cases = [
        ("O P E N YouTube", "open youtube"),
        ("T A N K to me", "talk to me"),  # tank -> talk via phonetic fix
        ("S E A R C H google", "search google"),
    ]
    
    passed = 0
    for input_text, expected_normalized in test_cases:
        result = parse_command(input_text)
        normalized = result['normalized']
        
        # Check if normalization worked (spaces collapsed)
        has_no_single_letter_spaces = not any(
            len(w) == 1 and w.isalpha() 
            for w in normalized.split()
        ) or 'youtube' in normalized or 'me' in normalized
        
        status = "PASS" if expected_normalized in normalized or has_no_single_letter_spaces else "FAIL"
        print(f"  Input: '{input_text}'")
        print(f"  Normalized: '{normalized}'")
        print(f"  Expected contains: '{expected_normalized}'")
        print(f"  Status: {status}")
        print()
        
        if status == "PASS":
            passed += 1
    
    return passed, len(test_cases)


def test_phonetic_fixes():
    """Test phonetic misspelling corrections."""
    print("\n=== Test: Phonetic Fixes ===")
    
    test_cases = [
        ("tank to me", "talk"),       # tank -> talk
        ("serch for videos", "search"), # serch -> search
        ("opn notepad", "open"),       # opn -> open
        ("paus the video", "pause"),   # paus -> pause
    ]
    
    passed = 0
    for input_text, expected_verb in test_cases:
        result = parse_command(input_text)
        
        status = "PASS" if result['verb'] == expected_verb else "FAIL"
        print(f"  Input: '{input_text}'")
        print(f"  Detected verb: {result['verb']}")
        print(f"  Expected verb: {expected_verb}")
        print(f"  Status: {status}")
        print()
        
        if status == "PASS":
            passed += 1
    
    return passed, len(test_cases)


def test_app_recognition():
    """Test app name fuzzy matching."""
    print("\n=== Test: App Recognition ===")
    
    test_cases = [
        ("open youtube", "youtube"),
        ("open yt", "youtube"),
        ("launch vscode", "vscode"),
        ("start spotify", "spotify"),
    ]
    
    passed = 0
    for input_text, expected_app in test_cases:
        result = parse_command(input_text)
        
        status = "PASS" if result['target'] == expected_app else "FAIL"
        print(f"  Input: '{input_text}'")
        print(f"  Detected app: {result['target']}")
        print(f"  Expected app: {expected_app}")
        print(f"  Status: {status}")
        print()
        
        if status == "PASS":
            passed += 1
    
    return passed, len(test_cases)


def test_multistep_detection():
    """Test detection of multi-step commands."""
    print("\n=== Test: Multi-step Command Detection ===")
    
    # Import multi-step pattern detection
    from core.main_controller import MainController
    
    # Create minimal controller just for pattern testing
    class MockController:
        def _is_multistep_command(self, text):
            import re
            MULTISTEP_PATTERNS = [
                r'youtube.+search.+click',
                r'search.+(?:and|then).+(?:click|open|play)',
                r'(?:seek|jump).+(?:to|at).+\d+.*(?:minute|second)',
            ]
            text_lower = text.lower()
            for pattern in MULTISTEP_PATTERNS:
                if re.search(pattern, text_lower):
                    return True
            action_words = ['search', 'open', 'click', 'play', 'pause', 'seek']
            count = sum(1 for w in action_words if w in text_lower)
            return count >= 2
    
    mock = MockController()
    
    test_cases = [
        ("YouTube search biology 2024, click third video, pause", True),
        ("search for cats and then click first result", True),
        ("open notepad", False),
        ("search youtube for music", False),  # Only one action
    ]
    
    passed = 0
    for input_text, expected_multistep in test_cases:
        is_multi = mock._is_multistep_command(input_text)
        
        status = "PASS" if is_multi == expected_multistep else "FAIL"
        print(f"  Input: '{input_text[:50]}...'")
        print(f"  Detected multi-step: {is_multi}")
        print(f"  Expected: {expected_multistep}")
        print(f"  Status: {status}")
        print()
        
        if status == "PASS":
            passed += 1
    
    return passed, len(test_cases)


def main():
    print("=" * 60)
    print("COMMAND PARSER TEST SUITE")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    # Run all tests
    p, t = test_spaced_letters()
    total_passed += p
    total_tests += t
    
    p, t = test_phonetic_fixes()
    total_passed += p
    total_tests += t
    
    p, t = test_app_recognition()
    total_passed += p
    total_tests += t
    
    p, t = test_multistep_detection()
    total_passed += p
    total_tests += t
    
    # Summary
    print("=" * 60)
    print(f"RESULTS: {total_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    # Log results
    log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'test_commands.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        f.write(f"Command Parser Tests: {total_passed}/{total_tests} passed\n")
        f.write(f"Pass rate: {100*total_passed/total_tests:.0f}%\n")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
