# orchestrator/planner.py
"""Natural language to JSON plan conversion using LLM."""

import json
import re
import time
from typing import Optional, List, Dict, Any

# Step types that require confirmation
DANGEROUS_STEP_TYPES = {
    'delete_file', 'delete_folder', 'run_command', 'install_package',
    'fill_credentials', 'login', 'shutdown', 'restart', 'edit_file',
    'format_drive', 'uninstall'
}

# System prompt for plan generation
PLANNER_SYSTEM_PROMPT = """You are a task planner for a desktop AI assistant. Convert user requests into executable JSON plans.

OUTPUT FORMAT (JSON only, no explanation):
{
  "id": "job-<timestamp>",
  "description": "Brief description of what this plan does",
  "steps": [
    {"type": "step_type", "param1": "value1", ...}
  ],
  "requires_confirmation": true/false
}

AVAILABLE STEP TYPES:

Browser/YouTube:
- {"type": "open_url", "url": "https://..."}
- {"type": "youtube_search", "query": "search terms"}
- {"type": "youtube_click_result", "n": 1}  // 1-indexed
- {"type": "youtube_seek", "seconds": 180}
- {"type": "youtube_pause"}
- {"type": "youtube_play"}
- {"type": "browser_click", "selector": "css selector"}
- {"type": "browser_fill", "selector": "input selector", "text": "value"}
- {"type": "browser_screenshot", "save": "path/to/save.png"}

System:
- {"type": "open_app", "name": "notepad"}
- {"type": "run_command", "command": "dir /b"}  // REQUIRES CONFIRMATION
- {"type": "screenshot", "save": "path.png"}
- {"type": "wait", "seconds": 2}

File Operations:
- {"type": "read_file", "path": "file.py"}
- {"type": "edit_file", "path": "file.py", "changes": "description"}  // REQUIRES CONFIRMATION
- {"type": "create_file", "path": "file.py", "content": "..."}

Vision:
- {"type": "ocr_screen"}
- {"type": "find_template", "template": "button.png"}
- {"type": "click_template", "template": "button.png"}

RULES:
1. Set "requires_confirmation": true if ANY step is in: delete, edit_file, run_command, install, login, shutdown, restart
2. Break complex requests into sequential atomic steps
3. Add wait steps between UI actions that need time to load
4. For YouTube: youtube_search → wait → youtube_click_result → wait → youtube_seek/pause
5. Output ONLY valid JSON, no markdown or explanation

EXAMPLES:

User: "Open YouTube and search for biology 2024"
{
  "id": "job-1",
  "description": "Search YouTube for biology 2024",
  "steps": [
    {"type": "youtube_search", "query": "biology 2024"}
  ],
  "requires_confirmation": false
}

User: "Open YouTube, search biology 2024, click third video, seek to 3 minutes, pause and screenshot"
{
  "id": "job-2",
  "description": "YouTube: search, play third result at 3:00, screenshot",
  "steps": [
    {"type": "youtube_search", "query": "biology 2024"},
    {"type": "wait", "seconds": 2},
    {"type": "youtube_click_result", "n": 3},
    {"type": "wait", "seconds": 3},
    {"type": "youtube_seek", "seconds": 180},
    {"type": "wait", "seconds": 1},
    {"type": "youtube_pause"},
    {"type": "browser_screenshot", "save": "logs/snapshots/bio_video.png"}
  ],
  "requires_confirmation": false
}

User: "Fix the bug in main.py"
{
  "id": "job-3",
  "description": "Analyze and fix bug in main.py",
  "steps": [
    {"type": "read_file", "path": "main.py"},
    {"type": "edit_file", "path": "main.py", "changes": "Fix identified bug"}
  ],
  "requires_confirmation": true
}
"""


class Planner:
    """Convert natural language commands to executable plans."""
    
    def __init__(self, llm_func=None):
        """
        Initialize planner.
        
        Args:
            llm_func: Function to call LLM. Signature: llm_func(prompt, system_prompt) -> str
        """
        self.llm_func = llm_func
    
    def parse(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Parse user input into a job plan.
        
        Args:
            user_input: Natural language command
        
        Returns:
            Job plan dict or None if parsing failed
        """
        if self.llm_func is None:
            # Fallback to simple pattern matching
            return self._simple_parse(user_input)
        
        try:
            response = self.llm_func(user_input, PLANNER_SYSTEM_PROMPT)
            return self._extract_json(response)
        except Exception as e:
            print(f"[Planner] LLM parsing failed: {e}")
            return self._simple_parse(user_input)
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response."""
        # Try to find JSON in the response
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in text
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _simple_parse(self, user_input: str) -> Optional[Dict]:
        """Simple pattern-based parsing as fallback."""
        text = user_input.lower()
        steps = []
        
        # YouTube patterns
        if 'youtube' in text:
            # Extract search query
            search_match = re.search(r'search(?:\s+for)?\s+["\']?([^"\']+)["\']?', text, re.IGNORECASE)
            if search_match:
                query = search_match.group(1).strip()
                steps.append({"type": "youtube_search", "query": query})
                steps.append({"type": "wait", "seconds": 2})
            
            # Click result
            result_match = re.search(r'(?:click|open|play)\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+(?:video|result)?', text)
            if result_match:
                n = int(result_match.group(1))
                steps.append({"type": "youtube_click_result", "n": n})
                steps.append({"type": "wait", "seconds": 3})
            elif 'first' in text or 'click' in text:
                steps.append({"type": "youtube_click_result", "n": 1})
                steps.append({"type": "wait", "seconds": 3})
            
            # Seek
            seek_match = re.search(r'seek\s+(?:to\s+)?(\d+)(?::(\d+))?(?:\s*(?:minutes?|min|m))?', text)
            if seek_match:
                mins = int(seek_match.group(1))
                secs = int(seek_match.group(2)) if seek_match.group(2) else 0
                total_secs = mins * 60 + secs if 'minute' in text or 'min' in text else mins
                steps.append({"type": "youtube_seek", "seconds": total_secs})
            
            # Pause
            if 'pause' in text:
                steps.append({"type": "youtube_pause"})
            
            # Screenshot
            if 'screenshot' in text:
                steps.append({"type": "browser_screenshot", "save": f"logs/snapshots/youtube_{int(time.time())}.png"})
        
        # Open app patterns
        elif 'open' in text:
            app_match = re.search(r'open\s+(\w+)', text)
            if app_match:
                app = app_match.group(1)
                if app in ['youtube', 'browser', 'chrome', 'firefox', 'edge']:
                    steps.append({"type": "open_url", "url": "https://www.youtube.com" if app == 'youtube' else "https://www.google.com"})
                else:
                    steps.append({"type": "open_app", "name": app})
        
        # Screenshot
        elif 'screenshot' in text:
            steps.append({"type": "screenshot", "save": f"logs/snapshots/screen_{int(time.time())}.png"})
        
        if not steps:
            return None
        
        return {
            "id": f"job-{int(time.time())}",
            "description": user_input[:50],
            "steps": steps,
            "requires_confirmation": any(s.get('type') in DANGEROUS_STEP_TYPES for s in steps)
        }
    
    def validate_plan(self, plan: Dict) -> tuple[bool, str]:
        """
        Validate a plan structure.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(plan, dict):
            return False, "Plan must be a dictionary"
        
        if 'steps' not in plan:
            return False, "Plan must have 'steps' array"
        
        if not isinstance(plan['steps'], list):
            return False, "'steps' must be an array"
        
        if len(plan['steps']) == 0:
            return False, "Plan has no steps"
        
        for i, step in enumerate(plan['steps']):
            if 'type' not in step:
                return False, f"Step {i+1} missing 'type'"
        
        return True, ""
    
    def summarize_plan(self, plan: Dict) -> str:
        """Generate human-readable summary of plan."""
        if not plan or 'steps' not in plan:
            return "Empty plan"
        
        desc = plan.get('description', 'Execute plan')
        steps_summary = []
        
        for i, step in enumerate(plan['steps'], 1):
            step_type = step.get('type', 'unknown')
            
            if step_type == 'youtube_search':
                steps_summary.append(f"{i}. Search YouTube: {step.get('query', '?')}")
            elif step_type == 'youtube_click_result':
                steps_summary.append(f"{i}. Click result #{step.get('n', 1)}")
            elif step_type == 'youtube_seek':
                secs = step.get('seconds', 0)
                mins, secs = divmod(secs, 60)
                steps_summary.append(f"{i}. Seek to {mins}:{secs:02d}")
            elif step_type == 'youtube_pause':
                steps_summary.append(f"{i}. Pause video")
            elif step_type == 'browser_screenshot':
                steps_summary.append(f"{i}. Take screenshot")
            elif step_type == 'open_url':
                steps_summary.append(f"{i}. Open {step.get('url', 'URL')}")
            elif step_type == 'open_app':
                steps_summary.append(f"{i}. Open {step.get('name', 'app')}")
            elif step_type == 'wait':
                steps_summary.append(f"{i}. Wait {step.get('seconds', 1)}s")
            elif step_type == 'edit_file':
                steps_summary.append(f"{i}. Edit {step.get('path', 'file')}")
            elif step_type == 'run_command':
                steps_summary.append(f"{i}. Run: {step.get('command', '?')[:30]}")
            else:
                steps_summary.append(f"{i}. {step_type}")
        
        confirmation = " ⚠️ REQUIRES CONFIRMATION" if plan.get('requires_confirmation') else ""
        return f"{desc}{confirmation}\n" + "\n".join(steps_summary)


def parse_plan_from_text(text: str, llm_func=None) -> Optional[Dict]:
    """Convenience function to parse text into plan."""
    planner = Planner(llm_func)
    return planner.parse(text)
