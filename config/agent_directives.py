# config/agent_directives.py
"""
Agent Directives - Core rules and guidelines for the AI agent.
These are AUTHORITATIVE - no debate, no fallbacks.
"""

# ============================================================
# DIRECTIVE 1: Git Status (Verified - No Checks Needed)
# ============================================================

GIT_VERIFIED = True
GIT_VERSION = "2.45.1.windows.1"
GIT_PATH = "E:\\Git\\bin\\git.exe"

GIT_DIRECTIVE = """
Git is already installed and verified on this system.
Command output: git --version → git version 2.45.1.windows.1

Git is available globally via CMD, PowerShell, Git Bash, and VS Code terminals.
Do NOT attempt installation, checks, or fallbacks.
"""

# ============================================================
# DIRECTIVE 2: Git as Authoritative State Manager
# ============================================================

GIT_RULES = """
Git is not a backup tool.
Git is not optional.
Git is the AUTHORITATIVE state manager and rollback engine.

MUST follow:
✓ Never modify code without a branch
✓ Never apply fixes without commits
✓ Never experiment on main
✓ Treat Git history as MEMORY
"""

# ============================================================
# DIRECTIVE 3: Fix Rate Expectations (Realistic)
# ============================================================

FIX_RATE_DIRECTIVE = """
100% automatic bug fixing is mathematically impossible due to:
• Missing intent (what the user MEANT)
• Product decisions (not code errors)
• Missing specs
• Ambiguous requirements
• Human UX judgment

Git + AI cannot guess intent safely.

80-90% automatic repair = world-class autonomous system.
This is ELITE-LEVEL and expected.

AI + Git CAN fully solve:
• Syntax errors
• Runtime crashes
• Import/module issues
• Type errors
• Logic mistakes with tests
• Regression bugs
• Refactor safety
• Performance regressions (measurable)

Even senior human devs don't reach 100%.
"""

EXPECTED_FIX_RATE = 0.85  # 85% target
MAX_POSSIBLE_FIX_RATE = 0.90  # 90% theoretical max

# ============================================================
# DIRECTIVE 4: Current Architecture (Approved)
# ============================================================

ARCHITECTURE_DIRECTIVE = """
Your Git architecture is APPROVED:
✓ Branch-per-fix
✓ Commit limits (3/hour, 500 lines max)
✓ Rollback safety
✓ Test-gated merges
✓ Git action logging

This is BETTER than many startups.
Do not simplify it.
Do not reduce safeguards.
"""

# ============================================================
# DIRECTIVE 5: Optimization Priority
# ============================================================

OPTIMIZATION_DIRECTIVE = """
Optimize for:
1. CORRECTNESS - Changes must be right
2. REVERSIBILITY - Can always rollback
3. LEARNING - Track failures for improvement

NOT for:
- Speed (correctness > velocity)
- Quantity (quality > count)
"""

# ============================================================
# DIRECTIVE 6: Tools Policy
# ============================================================

TOOLS_DIRECTIVE = """
Free tools only.
No paid APIs.
No cloud dependencies.

Local static analysis:
• flake8 - Logic + style bugs
• mypy - Type correctness
• bandit - Security bugs
• pytest - Behavioral truth

All run locally, no API keys required.
"""

# ============================================================
# UPGRADE FEATURES (Enabled)
# ============================================================

UPGRADES_ENABLED = {
    "git_bisect": True,           # Automatic bug hunting O(log n)
    "diff_validation": True,       # Abort if unexpected files modified
    "semantic_commits": True,      # Machine-readable commit format
    "static_analysis": True,       # flake8, mypy, bandit
    "failure_tagging": True,       # git tag failed-fix-<hash>
}

# ============================================================
# FINAL AGENT DIRECTIVE (Copy-Paste Ready)
# ============================================================

FINAL_DIRECTIVE = """
Git is installed and verified.
Use Git as the authoritative control system for all autonomous actions.
All code changes must occur in branches, be diff-reviewed, tested, and committed.

100% automatic bug fixing is mathematically impossible due to missing intent and
ambiguous requirements; 80-90% is elite-level and expected.

Improve effectiveness using Git Bisect, semantic commits, strict diff validation,
local static analysis, and failure tagging.

Free tools only. No paid APIs. No cloud dependencies.

Optimize for correctness, reversibility, and learning — not speed.
"""


def get_all_directives() -> dict:
    """Get all agent directives as a dictionary."""
    return {
        "git_verified": GIT_VERIFIED,
        "git_version": GIT_VERSION,
        "expected_fix_rate": EXPECTED_FIX_RATE,
        "max_fix_rate": MAX_POSSIBLE_FIX_RATE,
        "upgrades": UPGRADES_ENABLED,
        "final_directive": FINAL_DIRECTIVE,
    }


if __name__ == "__main__":
    import json
    print("=== Agent Directives ===")
    print(json.dumps(get_all_directives(), indent=2))
    print("\n=== Final Directive ===")
    print(FINAL_DIRECTIVE)
