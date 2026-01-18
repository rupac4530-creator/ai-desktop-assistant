# confirmation.py — typed confirmation dialog for dangerous actions
# Import and call require_confirmation() before executing risky commands

import os

DANGEROUS_ACTIONS_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'dangerous_actions.txt')

def load_dangerous_patterns():
    patterns = []
    if os.path.exists(DANGEROUS_ACTIONS_FILE):
        with open(DANGEROUS_ACTIONS_FILE, 'r') as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns

DANGEROUS_PATTERNS = load_dangerous_patterns()

def is_dangerous(action_text):
    """Check if an action matches any dangerous pattern."""
    text_lower = action_text.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in text_lower:
            return True
    return False

def require_confirmation(action_description, timeout_seconds=30):
    """
    Require typed confirmation for a dangerous action.
    Returns True if user confirms, False otherwise.
    Voice-only confirmation is NOT accepted for safety.
    """
    print("\n" + "="*60)
    print("⚠️  DANGEROUS ACTION DETECTED")
    print("="*60)
    print(f"Action: {action_description}")
    print("\nThis action requires TYPED confirmation.")
    print("Type 'YES I CONFIRM' exactly to proceed, or anything else to cancel.")
    print("="*60)
    
    try:
        response = input("Confirm: ").strip()
        if response == "YES I CONFIRM":
            print("✓ Confirmation accepted. Proceeding...")
            return True
        else:
            print("✗ Confirmation denied or invalid. Action cancelled.")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n✗ Confirmation cancelled.")
        return False

def check_and_confirm(action_json):
    """
    Check if an action requires confirmation and prompt if needed.
    Returns True if safe to proceed, False if blocked.
    """
    action = action_json.get('action', '')
    params = action_json.get('parameters', {})
    explain = action_json.get('explain', '')
    
    # Build a text representation to check
    check_text = f"{action} {explain} {str(params)}"
    
    # Also check if LLM explicitly set confirm: true
    if params.get('confirm') is True:
        return require_confirmation(explain or action)
    
    # Check against dangerous patterns
    if is_dangerous(check_text):
        return require_confirmation(explain or check_text)
    
    return True  # Safe to proceed

if __name__ == "__main__":
    # Test the confirmation system
    print("Testing confirmation system...\n")
    
    # Safe action
    safe = {"action": "open_app", "parameters": {"app_name": "youtube"}, "explain": "Open YouTube"}
    print(f"Safe action: {safe}")
    print(f"Requires confirmation: {is_dangerous(str(safe))}\n")
    
    # Dangerous action
    dangerous = {"action": "run_code", "parameters": {"code": "os.system('del /f')"}, "explain": "Delete files"}
    print(f"Dangerous action: {dangerous}")
    print(f"Requires confirmation: {is_dangerous(str(dangerous))}\n")
    
    # Test interactive confirmation
    print("Testing interactive confirmation...")
    result = require_confirmation("Delete all files in C:\\Windows")
    print(f"Result: {'Confirmed' if result else 'Denied'}")
