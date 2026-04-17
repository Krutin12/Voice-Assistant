"""
🔍 PREDICTIVE ACTION ENGINE
==============================
Analyzes active context continuously.
Triggers proactive intelligence based on:
  - Clipboard content (error detection)
  - Active window context (Excel → suggest formatting, LinkedIn → networking)
  - Repeated workflows (same app at same time 3+ days)
  - System state (battery, performance)

All triggers are confidence-weighted and respect the suggestion budget.
"""

import os
import json
import time
import re
from datetime import datetime, timedelta
from collections import Counter

try:
    import psutil
except ImportError:
    psutil = None


class PredictiveEngine:
    """
    Context-aware predictive action engine.
    Detects environmental triggers and generates intelligent predictions.
    """

    def __init__(self, behavior_profile=None, long_term_memory=None):
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory_logs')
        os.makedirs(self.data_dir, exist_ok=True)

        self.predictions_file = os.path.join(self.data_dir, 'predictions_log.json')
        self.behavior_profile = behavior_profile or {}
        self.long_term_memory = long_term_memory

        self._load_log()

    def _load_log(self):
        if os.path.exists(self.predictions_file):
            try:
                with open(self.predictions_file, 'r', encoding='utf-8') as f:
                    self.log = json.load(f)
            except Exception:
                self.log = self._default_log()
        else:
            self.log = self._default_log()

    def _save_log(self):
        try:
            with open(self.predictions_file, 'w', encoding='utf-8') as f:
                json.dump(self.log, f, indent=2, default=str)
        except Exception:
            pass

    def _default_log(self):
        return {
            "active_window_history": [],    # [{app, hour, weekday, ts}]
            "clipboard_errors": [],         # [{error, ts, fix_suggested}]
            "workflow_sequences": [],        # [{apps, hour, weekday, count}]
            "context_triggers_fired": 0,
            "last_prediction_ts": 0,
        }

    # ══════════════════════════════════════════
    #  CONTEXT OBSERVATION
    # ══════════════════════════════════════════

    def observe_context(self, command_text, response_text=""):
        """Observe the current context from command and system state."""
        now = datetime.now()
        text_lower = command_text.lower()

        # ── Track Active Window Context ──
        active_app = self._detect_active_app(text_lower)
        if active_app:
            entry = {
                "app": active_app,
                "hour": now.hour,
                "weekday": now.strftime("%A"),
                "ts": now.isoformat(),
            }
            self.log["active_window_history"].append(entry)
            # Keep last 200 entries
            self.log["active_window_history"] = self.log["active_window_history"][-200:]

        # ── Clipboard Error Detection ──
        self._check_for_error_context(text_lower, response_text)

        # ── Update Workflow Sequences ──
        self._update_workflow_sequences()

        self._save_log()

    # ══════════════════════════════════════════
    #  PREDICTIVE TRIGGERS
    # ══════════════════════════════════════════

    def get_prediction(self, command_text, response_text=""):
        """
        Evaluate all predictive triggers and return the best prediction.
        Returns None if no trigger fires or confidence is too low.
        """
        now = datetime.now()
        current_time = time.time()
        text_lower = command_text.lower()
        hour = now.hour
        weekday = now.strftime("%A")

        # Throttle: minimum 5 min between predictions
        if current_time - self.log.get("last_prediction_ts", 0) < 300:
            return None

        predictions = []

        # ── Trigger 1: Error in Command Context ──
        error_prediction = self._trigger_error_context(text_lower, response_text)
        if error_prediction:
            predictions.append(error_prediction)

        # ── Trigger 2: Excel Context ──
        if self._detect_app_in_context(text_lower, ['excel', 'spreadsheet', 'xlsx', 'csv']):
            predictions.append({
                "confidence": 50,
                "text_soft": "I see you're working with spreadsheets. Need help with data formatting, formulas, or creating a structured dataset?",
                "text_direct": "Working with Excel? I can help clean data, apply formatting, or build templates.",
                "category": "productivity",
            })

        # ── Trigger 3: LinkedIn / Professional Networking ──
        if self._detect_app_in_context(text_lower, ['linkedin']):
            linkedin_count = len([e for e in self.log["active_window_history"]
                                  if e.get("app") == "linkedin"])
            if linkedin_count >= 2:
                predictions.append({
                    "confidence": 55,
                    "text_soft": "I notice you check LinkedIn regularly. Want me to help draft a post or suggest networking tips?",
                    "text_direct": "LinkedIn is open — shall I help draft a professional update or connection message?",
                    "category": "communication",
                })

        # ── Trigger 4: Repeated Workflow Detection ──
        workflow_pred = self._trigger_repeated_workflow(hour, weekday)
        if workflow_pred:
            predictions.append(workflow_pred)

        # ── Trigger 5: Focus Session Detection ──
        coding_apps = ['vscode', 'visual studio', 'code', 'pycharm', 'intellij', 'sublime']
        if any(app in text_lower for app in coding_apps):
            peak_hours = self.behavior_profile.get("peak_productivity_hours", [])
            if hour in peak_hours:
                predictions.append({
                    "confidence": 60,
                    "text_soft": "Looks like this is usually your deep-focus time. Want to start your session?",
                    "text_direct": "Your productivity peaks around now. Ready to dive into coding?",
                    "category": "productivity",
                })

        # ── Trigger 6: Battery Prediction ──
        battery_pred = self._trigger_battery_prediction()
        if battery_pred:
            predictions.append(battery_pred)

        # ── Trigger 7: Break Reminder (health) ──
        break_pred = self._trigger_break_reminder()
        if break_pred:
            predictions.append(break_pred)

        if not predictions:
            return None

        # Sort by confidence, pick the best
        best = max(predictions, key=lambda p: p["confidence"])

        # Confidence-based delivery
        if best["confidence"] >= 75:
            message = best.get("text_direct", best.get("text_soft", ""))
        elif best["confidence"] >= 40:
            message = best.get("text_soft", best.get("text_direct", ""))
        else:
            return None  # Observe silently

        if not message:
            return None

        self.log["last_prediction_ts"] = current_time
        self.log["context_triggers_fired"] = self.log.get("context_triggers_fired", 0) + 1
        self._save_log()

        return f"🎯 {message}"

    # ══════════════════════════════════════════
    #  INDIVIDUAL TRIGGERS
    # ══════════════════════════════════════════

    def _trigger_error_context(self, text, response):
        """Trigger: User mentions an error → check Mistake Memory for previous fix."""
        error_indicators = [
            'error', 'exception', 'traceback', 'failed', 'bug', 'crash',
            'not working', 'broken', 'issue', 'problem', 'stuck',
        ]

        if not any(ind in text for ind in error_indicators):
            return None

        # Check if LongTermMemory has a previous fix
        if self.long_term_memory:
            fix_result = self.long_term_memory.find_previous_fix(text)
            if fix_result.get("found"):
                return {
                    "confidence": 85,
                    "text_direct": f"I've seen this before — last time, '{fix_result['fix']}' solved it. Want to try that approach?",
                    "text_soft": f"This looks familiar. Previously, '{fix_result['fix']}' worked. Shall we try that?",
                    "category": "debugging",
                }

        # Generic debugging suggestion
        return {
            "confidence": 45,
            "text_soft": "Having trouble? I can search for solutions or check if we've encountered this before.",
            "category": "debugging",
        }

    def _trigger_repeated_workflow(self, hour, weekday):
        """Trigger: Same app opens at same time for 3+ days → suggest session init."""
        history = self.log.get("active_window_history", [])
        if len(history) < 3:
            return None

        # Group by app and check if same app appears at similar hour on 3+ different days
        app_time_groups = {}
        for entry in history:
            app = entry.get("app", "")
            h = entry.get("hour", -1)
            day = entry.get("ts", "")[:10]  # YYYY-MM-DD

            key = f"{app}_{h}"
            if key not in app_time_groups:
                app_time_groups[key] = set()
            app_time_groups[key].add(day)

        for key, days in app_time_groups.items():
            if len(days) >= 3:
                app_name = key.split("_")[0]
                app_hour = int(key.split("_")[1])
                if abs(app_hour - hour) <= 1:
                    confidence = min(90, 50 + len(days) * 10)
                    return {
                        "confidence": confidence,
                        "text_direct": f"Ready to begin your {app_name.title()} session? You've been using it at this time for {len(days)} days.",
                        "text_soft": f"You seem to use {app_name.title()} around this time regularly. Need it now?",
                        "category": "habits",
                    }
        return None

    def _trigger_battery_prediction(self):
        """Trigger: Battery heading low based on usage patterns."""
        if not psutil:
            return None
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return None

            if battery.percent <= 25 and not battery.power_plugged:
                return {
                    "confidence": 80,
                    "text_direct": f"Battery is at {battery.percent}%. Based on your usage, you might want to plug in soon.",
                    "text_soft": f"Just a note — battery is at {battery.percent}% and dropping.",
                    "category": "system",
                }
            elif battery.percent <= 40 and not battery.power_plugged:
                # Check if pattern shows it usually drops fast from here
                battery_history = [e.get("battery", 100) for e in self.log.get("active_window_history", [])
                                   if "battery" in e and not e.get("plugged", True)]
                if len(battery_history) >= 3:
                    avg_drop = battery_history[0] - battery_history[-1] if len(battery_history) > 1 else 0
                    if avg_drop > 20:
                        return {
                            "confidence": 60,
                            "text_soft": f"Your battery drops quickly in the evening. Currently at {battery.percent}% — consider plugging in.",
                            "category": "system",
                        }
        except Exception:
            pass
        return None

    def _trigger_break_reminder(self):
        """Trigger: Continuous usage for 90+ min → suggest break."""
        history = self.log.get("active_window_history", [])
        if len(history) < 10:
            return None

        # Check if last 10 entries are all within the last 90 minutes
        try:
            recent = history[-10:]
            first_ts = datetime.fromisoformat(recent[0]["ts"])
            last_ts = datetime.fromisoformat(recent[-1]["ts"])
            duration = (last_ts - first_ts).total_seconds() / 60.0

            if 60 <= duration <= 120:
                return {
                    "confidence": 50,
                    "text_soft": "You've been working for a while now. A short break might help refresh your focus.",
                    "category": "health",
                }
        except Exception:
            pass
        return None

    # ══════════════════════════════════════════
    #  HELPER METHODS
    # ══════════════════════════════════════════

    def _detect_active_app(self, text):
        """Detect which app the user is interacting with from command text."""
        app_keywords = {
            'vscode': ['vscode', 'visual studio code', 'vs code'],
            'chrome': ['chrome', 'browser'],
            'excel': ['excel', 'spreadsheet', 'xlsx'],
            'word': ['word', 'document', 'docx'],
            'powerpoint': ['powerpoint', 'presentation', 'pptx', 'slides'],
            'spotify': ['spotify', 'music'],
            'youtube': ['youtube', 'video'],
            'whatsapp': ['whatsapp', 'message'],
            'linkedin': ['linkedin'],
            'github': ['github', 'repo', 'repository'],
            'notepad': ['notepad'],
            'terminal': ['terminal', 'cmd', 'powershell', 'command prompt'],
        }

        for app, keywords in app_keywords.items():
            if any(kw in text for kw in keywords):
                return app
        return None

    def _detect_app_in_context(self, text, keywords):
        """Check if any keyword is present in the text."""
        return any(kw in text for kw in keywords)

    def _check_for_error_context(self, text, response):
        """Check if an error was mentioned and log it."""
        error_indicators = ['error', 'exception', 'traceback', 'failed', 'bug', 'crash', 'not working']
        if any(ind in text for ind in error_indicators) or any(ind in response.lower() for ind in error_indicators):
            self.log["clipboard_errors"].append({
                "error": text[:150],
                "ts": datetime.now().isoformat(),
                "fix_suggested": False,
            })
            # Keep last 50
            self.log["clipboard_errors"] = self.log["clipboard_errors"][-50:]

    def _update_workflow_sequences(self):
        """Analyze recent app launches to detect workflow patterns."""
        history = self.log.get("active_window_history", [])
        if len(history) < 5:
            return

        # Group by (weekday, hour) and find app sequences
        recent = history[-20:]
        sequences = []
        for entry in recent:
            sequences.append(f"{entry.get('app', '?')}@{entry.get('hour', 0)}")

        # Store most common sequence pattern
        if len(sequences) >= 3:
            # Just track the frequency of app-hour pairs (simple approach)
            pair_counts = Counter(sequences)
            top_pairs = pair_counts.most_common(5)
            self.log["workflow_sequences"] = [
                {"pattern": p[0], "count": p[1]} for p in top_pairs
            ]
