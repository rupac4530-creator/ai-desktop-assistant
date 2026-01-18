# core/self_heal_planner.py
"""
Self-Heal Planner - Converts diagnostic reports into ordered repair plans.
Determines which actions can run automatically vs require user approval.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.watchdog import DiagnosticReport, HealthStatus, log_self_heal


@dataclass
class RepairPlanItem:
    action: str
    reason: str
    auto: bool  # Can run without user approval
    priority: int  # Lower = run first


class SelfHealPlanner:
    """
    Converts diagnostic reports into executable repair plans.
    Respects auto-repair rules and user approval requirements.
    """

    # Actions that can run automatically (non-destructive)
    AUTO_SAFE_ACTIONS = {
        "reset_ptt_state",
        "rebind_hotkeys",
        "restart_tts",
        "restart_audio_device",
        "switch_asr_to_cpu",
        "restart_asr",
        "reconnect_avatar",
        "repair_mic_routine",
    }

    # Actions requiring user approval (potentially destructive)
    REQUIRE_APPROVAL = {
        "run_git_self_update",
        "restart_assistant_process",
        "factory_reset",
        "modify_code",
    }

    # Maximum auto-actions per run (safety limit)
    MAX_AUTO_ACTIONS = 5

    def __init__(self):
        log_self_heal("SelfHealPlanner initialized")

    def create_plan(self, report: DiagnosticReport) -> List[RepairPlanItem]:
        """Create a repair plan from diagnostic report."""
        plan = []

        # Map recommendations to plan items with priorities
        priority_map = {
            "reset_ptt_state": 1,
            "rebind_hotkeys": 2,
            "restart_audio_device": 3,
            "switch_asr_to_cpu": 4,
            "restart_asr": 5,
            "restart_tts": 6,
            "reconnect_avatar": 7,
            "repair_mic_routine": 0,  # Highest priority if suggested
        }

        for rec in report.recommendations:
            is_auto = rec in self.AUTO_SAFE_ACTIONS
            priority = priority_map.get(rec, 10)

            # Find the issue that triggered this recommendation
            reason = "Detected issue"
            for issue in report.issues:
                if rec.replace("_", " ") in issue.lower() or self._matches_issue(rec, issue):
                    reason = issue
                    break

            plan.append(RepairPlanItem(
                action=rec,
                reason=reason,
                auto=is_auto,
                priority=priority
            ))

        # Sort by priority
        plan.sort(key=lambda x: x.priority)

        # Limit auto-actions
        auto_count = sum(1 for p in plan if p.auto)
        if auto_count > self.MAX_AUTO_ACTIONS:
            log_self_heal(f"Limiting auto-actions from {auto_count} to {self.MAX_AUTO_ACTIONS}")
            count = 0
            for p in plan:
                if p.auto:
                    count += 1
                    if count > self.MAX_AUTO_ACTIONS:
                        p.auto = False  # Require approval for excess

        log_self_heal(f"Created repair plan with {len(plan)} steps")
        return plan

    def _matches_issue(self, action: str, issue: str) -> bool:
        """Check if action matches the issue description."""
        mappings = {
            "restart_asr": ["asr", "transcription", "speech recognition", "cublas"],
            "switch_asr_to_cpu": ["cuda", "cublas", "gpu", "latency"],
            "restart_tts": ["tts", "speech", "playback", "audio"],
            "restart_audio_device": ["microphone", "mic", "audio frame", "recording"],
            "rebind_hotkeys": ["hotkey", "keyboard", "listener"],
            "reset_ptt_state": ["ptt", "recording", "stuck"],
            "reconnect_avatar": ["avatar", "vtube", "websocket"],
        }

        keywords = mappings.get(action, [])
        issue_lower = issue.lower()
        return any(kw in issue_lower for kw in keywords)

    def get_auto_plan(self, report: DiagnosticReport) -> List[Dict[str, Any]]:
        """Get only auto-executable actions as dict list (for repair engine)."""
        plan = self.create_plan(report)
        return [
            {"action": p.action, "reason": p.reason, "auto": p.auto}
            for p in plan if p.auto
        ]

    def get_approval_needed(self, report: DiagnosticReport) -> List[Dict[str, Any]]:
        """Get actions that need user approval."""
        plan = self.create_plan(report)
        return [
            {"action": p.action, "reason": p.reason, "auto": p.auto}
            for p in plan if not p.auto
        ]

    def summarize_plan(self, plan: List[RepairPlanItem]) -> str:
        """Generate human-readable summary for TTS."""
        if not plan:
            return "No repairs needed."

        auto_actions = [p for p in plan if p.auto]
        approval_actions = [p for p in plan if not p.auto]

        summary_parts = []

        if auto_actions:
            action_names = ", ".join(p.action.replace("_", " ") for p in auto_actions[:3])
            if len(auto_actions) > 3:
                summary_parts.append(f"I'll automatically run {len(auto_actions)} repairs including {action_names}")
            else:
                summary_parts.append(f"I'll automatically {action_names}")

        if approval_actions:
            summary_parts.append(f"{len(approval_actions)} actions need your approval")

        return ". ".join(summary_parts) + "."

    def plan_for_command(self, command: str) -> List[RepairPlanItem]:
        """Create repair plan from user command (voice/text)."""
        command_lower = command.lower()

        # Direct mappings
        if any(kw in command_lower for kw in ["fix mic", "repair mic", "microphone"]):
            return [RepairPlanItem("repair_mic_routine", "User requested mic repair", True, 0)]

        if any(kw in command_lower for kw in ["fix speech", "repair speech", "asr", "transcription"]):
            return [
                RepairPlanItem("switch_asr_to_cpu", "User requested ASR fix", True, 1),
                RepairPlanItem("restart_asr", "User requested ASR fix", True, 2),
            ]

        if any(kw in command_lower for kw in ["fix tts", "repair tts", "voice", "speaking"]):
            return [RepairPlanItem("restart_tts", "User requested TTS fix", True, 0)]

        if any(kw in command_lower for kw in ["fix hotkey", "repair hotkey", "keyboard"]):
            return [RepairPlanItem("rebind_hotkeys", "User requested hotkey fix", True, 0)]

        if any(kw in command_lower for kw in ["fix ptt", "reset ptt", "recording stuck"]):
            return [RepairPlanItem("reset_ptt_state", "User requested PTT reset", True, 0)]

        if any(kw in command_lower for kw in ["fix yourself", "repair yourself", "self repair", "heal"]):
            # Run full diagnostics and create plan
            from core.watchdog import get_watchdog
            report = get_watchdog().run_diagnostics()
            return self.create_plan(report)

        if any(kw in command_lower for kw in ["update", "self update", "upgrade"]):
            return [RepairPlanItem("run_git_self_update", "User requested update", False, 0)]

        # Default: run diagnostics
        if any(kw in command_lower for kw in ["diagnose", "diagnostic", "status", "health"]):
            return []  # Just run diagnostics, no repairs

        return []


# Singleton
_planner: Optional[SelfHealPlanner] = None

def get_planner() -> SelfHealPlanner:
    global _planner
    if _planner is None:
        _planner = SelfHealPlanner()
    return _planner
