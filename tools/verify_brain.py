import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

def verify_autonomous_brain():
    errors = []
    checks = []
    
    # 1. Check AUTONOMOUS_CODING_ENABLED in env
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')
    if os.getenv('AUTONOMOUS_CODING_ENABLED', '').lower() == 'true':
        checks.append('AUTONOMOUS_CODING_ENABLED=true')
    else:
        errors.append('AUTONOMOUS_CODING_ENABLED not set')
    
    # 2. Check modules import
    try:
        from core.llm_brain import llm_generate, get_brain_status
        from core.model_selector import select_model
        from core.autonomous_coder import analyze_and_fix
        from core.task_planner import create_plan, quick_command
        from core.autonomous_review import generate_daily_digest
        checks.append('All modules import successfully')
    except Exception as e:
        errors.append(f'Module import failed: {e}')
        get_brain_status = None
    
    # 3. Check Ollama connection
    try:
        import ollama
        models = ollama.list()
        model_list = models.get('models', [])
        checks.append(f'Ollama connected: {len(model_list)} models')
    except Exception as e:
        errors.append(f'Ollama connection failed: {e}')
    
    # 4. Check prompt templates
    prompts_dir = PROJECT_ROOT / 'core' / 'prompts'
    if (prompts_dir / 'code_fix.system.txt').exists():
        checks.append('Prompt templates exist')
    else:
        errors.append('Prompt templates missing')
    
    # 5. Check logs directory
    logs_dir = PROJECT_ROOT / 'logs'
    if logs_dir.exists():
        checks.append('Logs directory exists')
    else:
        errors.append('Logs directory missing')
    
    # 6. Quick LLM test
    try:
        if get_brain_status:
            status = get_brain_status()
            checks.append(f"Brain: device={status['device']}, code={status['code_model']}")
    except Exception as e:
        errors.append(f'Brain status failed: {e}')
    
    print('=== AUTONOMOUS BRAIN VERIFICATION ===')
    print()
    for check in checks:
        print(f'  [OK] {check}')
    for error in errors:
        print(f'  [FAIL] {error}')
    print()
    
    if not errors:
        print('AUTONOMOUS_BRAIN=ENABLED')
        return True
    else:
        print(f'AUTONOMOUS_BRAIN=FAILED ({len(errors)} errors)')
        return False

if __name__ == '__main__':
    verify_autonomous_brain()
