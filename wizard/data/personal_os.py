"""
🧠 AI PERSONAL OPERATING SYSTEM — MASTER ORCHESTRATOR
=======================================================
You are not a simple voice assistant.
You are an AI Personal Operating System embedded within a desktop environment.

This module orchestrates:
  • BehaviorLearningEngine  — Pattern detection, habits, routines, interests
  • LongTermMemory          — Projects, tech stack, mistakes, deadlines
  • PredictiveEngine        — Context triggers, workflow predictions

It unifies observation, memory, prediction, and suggestion into a single
coherent intelligence layer that improves continuously.

Safety:
  • Suggestions only — no forced actions
  • Maximum 3 proactive suggestions per day (unless critical)
  • Never modifies user data autonomously
  • Respects suppression and dismissal history
"""

import os
import json
import time
from datetime import datetime, timedelta


class PersonalOS:
    """
    AI Personal Operating System — Master Intelligence Layer.

    Usage:
        pos = PersonalOS()
        pos.observe(command_text, response_text)
        suggestion = pos.think(command_text, response_text)
    """

    _instance = None  # Singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory_logs')
        os.makedirs(self.data_dir, exist_ok=True)
        self.os_state_file = os.path.join(self.data_dir, 'personal_os_state.json')

        # ── Initialize Subsystems ──
        self._init_subsystems()
        self._load_state()

    def _init_subsystems(self):
        """Lazy-load all subsystem modules."""
        try:
            from wizard.data.behavior_learning import BehaviorLearningEngine
            self.behavior = BehaviorLearningEngine()
        except Exception:
            self.behavior = None

        try:
            from wizard.data.memory_store import LongTermMemory
            self.memory = LongTermMemory()
        except Exception:
            self.memory = None

        try:
            from wizard.data.predictive_engine import PredictiveEngine
            profile = self.behavior.profile if self.behavior else {}
            self.predictor = PredictiveEngine(
                behavior_profile=profile,
                long_term_memory=self.memory
            )
        except Exception:
            self.predictor = None

    def _load_state(self):
        """Load the OS-level persistent state."""
        if os.path.exists(self.os_state_file):
            try:
                with open(self.os_state_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
            except Exception:
                self.state = self._default_state()
        else:
            self.state = self._default_state()

    def _save_state(self):
        try:
            with open(self.os_state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception:
            pass

    def _default_state(self):
        return {
            "boot_count": 0,
            "total_observations": 0,
            "total_suggestions_delivered": 0,
            "suggestions_today": 0,
            "suggestions_today_date": "",
            "last_suggestion_ts": 0,
            "evolution_level": 1,       # Increases as data accumulates
            "last_evolution_check": "",
            "monthly_report_date": "",
            "created": datetime.now().isoformat(),
        }

    # ══════════════════════════════════════════
    #  MAIN API: observe() + think()
    # ══════════════════════════════════════════

    def observe(self, command_text, response_text=""):
        """
        OBSERVATION PHASE — Called on every user command.
        Silently feeds data into all subsystems.
        Does NOT generate suggestions. Only observes.
        """
        self.state["total_observations"] = self.state.get("total_observations", 0) + 1

        # ── Feed Behavior Engine ──
        if self.behavior:
            try:
                self.behavior.record_action(command_text)
            except Exception:
                pass

        # ── Feed Long-Term Memory ──
        if self.memory:
            try:
                self.memory.detect_project_context(command_text)
                self.memory.update_tech_stack(command_text)
                self.memory.detect_error_in_text(command_text)
                self.memory.detect_deadline(command_text)
            except Exception:
                pass

        # ── Feed Predictive Engine ──
        if self.predictor:
            try:
                self.predictor.observe_context(command_text, response_text)
            except Exception:
                pass

        self._save_state()

    def think(self, command_text, response_text=""):
        """
        THINKING PHASE — Called after observe().
        Evaluates all subsystems and returns the BEST proactive suggestion.
        Returns None if nothing to suggest.

        Budget: Max 3 per day, minimum 5-min gap.
        """
        now = datetime.now()
        current_time = time.time()

        # ── Daily counter reset ──
        today_str = now.strftime("%Y-%m-%d")
        if self.state.get("suggestions_today_date") != today_str:
            self.state["suggestions_today"] = 0
            self.state["suggestions_today_date"] = today_str

        # ── Budget check ──
        if self.state.get("suggestions_today", 0) >= 3:
            # Allow critical suggestions (battery < 15%) to bypass limit
            if not self._is_critical_context():
                return None

        # ── Minimum gap: 5 minutes ──
        if current_time - self.state.get("last_suggestion_ts", 0) < 300:
            return None

        # ── Collect candidates from all subsystems ──
        candidates = []

        # 1. Behavior Learning Engine suggestions
        if self.behavior:
            try:
                beh_suggestion = self.behavior.get_proactive_suggestion(command_text)
                if beh_suggestion:
                    candidates.append(("behavior", beh_suggestion))
            except Exception:
                pass

        # 2. Predictive Engine triggers
        if self.predictor:
            try:
                pred_suggestion = self.predictor.get_prediction(command_text, response_text)
                if pred_suggestion:
                    candidates.append(("prediction", pred_suggestion))
            except Exception:
                pass

        # 3. Deadline warnings (from LongTermMemory)
        if self.memory:
            try:
                deadline_warning = self.memory.get_deadline_warning()
                if deadline_warning:
                    candidates.append(("deadline", f"📅 {deadline_warning}"))
            except Exception:
                pass

        # 4. Historical fix reference (if error detected)
        if self.memory:
            try:
                fix = self.memory.find_previous_fix(command_text)
                if fix.get("found"):
                    msg = f"💡 I remember this issue — last time, '{fix['fix']}' resolved it."
                    candidates.append(("fix_memory", msg))
            except Exception:
                pass

        if not candidates:
            # ── Check for evolution milestone ──
            self._check_evolution()
            return None

        # ── Select the best candidate ──
        # Priority: fix_memory > deadline > prediction > behavior
        priority = {"fix_memory": 4, "deadline": 3, "prediction": 2, "behavior": 1}
        best = max(candidates, key=lambda c: priority.get(c[0], 0))

        suggestion_text = best[1]

        # ── Record delivery ──
        self.state["suggestions_today"] = self.state.get("suggestions_today", 0) + 1
        self.state["last_suggestion_ts"] = current_time
        self.state["total_suggestions_delivered"] = self.state.get("total_suggestions_delivered", 0) + 1
        self._save_state()

        # ── Check for evolution milestone ──
        self._check_evolution()

        return suggestion_text

    # ══════════════════════════════════════════
    #  EVOLUTION PROTOCOL
    # ══════════════════════════════════════════

    def _check_evolution(self):
        """
        Weekly & Monthly evolution checks.
        Increases evolution_level as the system accumulates knowledge.
        """
        now = datetime.now()
        last_check = self.state.get("last_evolution_check", "")

        if last_check:
            try:
                last_dt = datetime.fromisoformat(last_check)
                if (now - last_dt).days < 7:
                    return
            except Exception:
                pass

        obs = self.state.get("total_observations", 0)

        # Evolution levels based on total observations
        if obs >= 500:
            self.state["evolution_level"] = 5  # Strategic Partner
        elif obs >= 200:
            self.state["evolution_level"] = 4  # Deep Personalization
        elif obs >= 100:
            self.state["evolution_level"] = 3  # Pattern Expert
        elif obs >= 30:
            self.state["evolution_level"] = 2  # Active Learner
        else:
            self.state["evolution_level"] = 1  # Observer

        # Trigger weekly recalc in behavior engine
        if self.behavior:
            try:
                self.behavior._weekly_recalculate()
            except Exception:
                pass

        self.state["last_evolution_check"] = now.isoformat()
        self._save_state()

    def get_evolution_status(self):
        """Return the current evolution level and its meaning."""
        level = self.state.get("evolution_level", 1)
        level_names = {
            1: "🌱 Observer — Learning your patterns",
            2: "📊 Active Learner — Detecting habits",
            3: "🧩 Pattern Expert — Predicting needs",
            4: "🎯 Deep Personalization — Strategic suggestions",
            5: "🧠 Strategic Partner — Full workflow optimization",
        }
        obs = self.state.get("total_observations", 0)
        suggestions = self.state.get("total_suggestions_delivered", 0)
        return f"Evolution: {level_names.get(level, 'Unknown')} | Observations: {obs} | Suggestions: {suggestions}"

    # ══════════════════════════════════════════
    #  FULL INTELLIGENCE REPORT
    # ══════════════════════════════════════════

    def get_intelligence_report(self):
        """
        Generate a comprehensive intelligence report combining all subsystems.
        Called when user asks "show my profile" or "intelligence report".
        """
        parts = [
            "╔══════════════════════════════════════════╗",
            "║   🧠 AI PERSONAL OS — INTELLIGENCE REPORT ║",
            "╚══════════════════════════════════════════╝",
            "",
        ]

        # Evolution status
        parts.append(self.get_evolution_status())
        parts.append("")

        # Behavioral profile
        if self.behavior:
            try:
                parts.append(self.behavior.get_profile_summary())
                parts.append("")
            except Exception:
                pass

        # Long-term memory
        if self.memory:
            try:
                parts.append(self.memory.get_full_report())
                parts.append("")
            except Exception:
                pass

        # System stats
        parts.append(f"📈 System Stats:")
        parts.append(f"  Total Observations: {self.state.get('total_observations', 0)}")
        parts.append(f"  Total Suggestions: {self.state.get('total_suggestions_delivered', 0)}")
        parts.append(f"  Today's Suggestions: {self.state.get('suggestions_today', 0)}/3")

        return "\n".join(parts)

    # ══════════════════════════════════════════
    #  USER CONTROL API
    # ══════════════════════════════════════════

    def stop_suggesting(self, category):
        """User says 'stop suggesting this' → permanently suppress."""
        if self.behavior:
            try:
                self.behavior.suppress_category(category)
            except Exception:
                pass

    def accept_last_suggestion(self):
        """User accepted the last suggestion."""
        if self.behavior:
            try:
                self.behavior.accept_suggestion("last")
            except Exception:
                pass

    def dismiss_last_suggestion(self):
        """User dismissed the last suggestion."""
        if self.behavior:
            try:
                self.behavior.dismiss_suggestion("last")
            except Exception:
                pass

    # ══════════════════════════════════════════
    #  SAFETY CHECKS
    # ══════════════════════════════════════════

    def _is_critical_context(self):
        """Check if current context is critical enough to bypass suggestion limits."""
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery and battery.percent <= 15 and not battery.power_plugged:
                return True
        except Exception:
            pass
        return False
