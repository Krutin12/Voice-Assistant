"""
🔮 UNIVERSAL SELF-IMPROVING BEHAVIOR INTELLIGENCE ENGINE
=========================================================
A continuously learning, behavior-adaptive intelligence system designed to
optimize the user's workflow, habits, and performance across all aspects
of digital interaction.

Transforms:  User Behavior → Pattern Detection → Prediction → Intelligent Suggestion → Optimization

Safety:  Suggestions only — no forced actions. Never modifies user data autonomously.
"""

import os
import json
import time
import re
import math
from datetime import datetime, timedelta
from collections import Counter, defaultdict

try:
    import psutil
except ImportError:
    psutil = None


# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────
HABIT_THRESHOLD       = 3      # Action repeats 3+ times in similar time → Habit
ROUTINE_WEEKLY_THRESH = 3      # Behavior repeats 3+ weeks → Routine
INTEREST_THRESHOLD    = 3      # Topic appears 3+ times in queries → Interest Area
ACCEPT_BOOST         = 2       # Accept suggestion 2+ times → increase confidence
DISMISS_SUPPRESS     = 3       # Dismiss suggestion 3 times → suppress
MAX_SUGGESTIONS_DAY  = 3       # Maximum proactive suggestions per day
SUGGESTION_GAP_SECS  = 1800    # Minimum 30 minutes between suggestions
CONFIDENCE_DIRECT    = 75      # confidence > 75% → Direct suggestion
CONFIDENCE_SOFT      = 40      # confidence 40–75% → Soft question
HOUR_WINDOW          = 2       # Hours ± to consider "similar time window"
WEEKLY_DECAY         = 0.95    # Weekly weight decay factor


class BehaviorLearningEngine:
    """
    Autonomous Behavior Learning Engine.
    Observes, analyzes, detects patterns, and generates proactive suggestions.
    """

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory_logs')
        os.makedirs(self.data_dir, exist_ok=True)

        self.profile_file = os.path.join(self.data_dir, 'user_profile.json')
        self.events_file  = os.path.join(self.data_dir, 'event_log.json')

        self._load_profile()
        self._load_events()

    # ══════════════════════════════════════════
    #  PERSISTENCE
    # ══════════════════════════════════════════

    def _load_profile(self):
        """Load the user behavioral profile."""
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    self.profile = json.load(f)
            except Exception:
                self.profile = self._default_profile()
        else:
            self.profile = self._default_profile()

    def _load_events(self):
        """Load the raw event log (last 30 days kept)."""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    self.events = json.load(f)
            except Exception:
                self.events = []
        else:
            self.events = []

    def _save_profile(self):
        try:
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=2, default=str)
        except Exception:
            pass

    def _save_events(self):
        try:
            # Keep only last 30 days of events to avoid unbounded growth
            cutoff = (datetime.now() - timedelta(days=30)).isoformat()
            self.events = [e for e in self.events if e.get("ts", "") >= cutoff]
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, indent=2, default=str)
        except Exception:
            pass

    def _default_profile(self):
        return {
            # ── Tracked Patterns ──
            "app_usage":            {},   # {app: [{hour, weekday, count}]}
            "search_topics":        {},   # {topic_cluster: count}
            "command_frequency":    {},   # {command_stem: count}
            "website_domains":      {},   # {domain: count}

            # ── Detected Patterns ──
            "habits":               [],   # [{action, typical_hour, confidence, domain}]
            "routines":             [],   # [{action, weekday, hour, confidence}]
            "interest_areas":       [],   # [{topic, strength, first_seen, last_seen}]
            "system_patterns":      [],   # [{metric, pattern_desc, confidence}]

            # ── Behavioral Profile ──
            "peak_productivity_hours": [],
            "energy_cycles":        {},   # {morning/afternoon/evening/night: activity_count}
            "suggestion_acceptance": {},  # {suggestion_id: {accepted: N, dismissed: N}}
            "suppressed_categories": [],  # Categories user said "stop suggesting"

            # ── Meta ──
            "suggestions_today":    0,
            "suggestions_today_date": "",
            "last_suggestion_ts":   0,
            "last_weekly_recalc":   "",
            "total_commands":       0,
            "first_seen":           datetime.now().isoformat(),
        }

    # ══════════════════════════════════════════
    #  OBSERVATION — record_action()
    # ══════════════════════════════════════════

    def record_action(self, text):
        """
        Silently observe and record user behavior from a command string.
        This is called on EVERY command the user issues.
        """
        text_lower = text.lower().strip()
        now = datetime.now()
        hour = now.hour
        weekday = now.strftime("%A")   # Monday, Tuesday, ...

        self.profile["total_commands"] = self.profile.get("total_commands", 0) + 1

        # Reset daily suggestion counter
        today_str = now.strftime("%Y-%m-%d")
        if self.profile.get("suggestions_today_date") != today_str:
            self.profile["suggestions_today"] = 0
            self.profile["suggestions_today_date"] = today_str

        # ── Track Energy Cycles ──
        period = self._get_period(hour)
        if period not in self.profile["energy_cycles"]:
            self.profile["energy_cycles"][period] = 0
        self.profile["energy_cycles"][period] += 1

        # ── Log raw event ──
        event = {
            "ts": now.isoformat(),
            "hour": hour,
            "weekday": weekday,
            "text": text_lower,
            "period": period,
        }

        # ── 1. Application Usage ──
        app_name = self._extract_app_name(text_lower)
        if app_name:
            event["type"] = "app_launch"
            event["app"] = app_name
            if app_name not in self.profile["app_usage"]:
                self.profile["app_usage"][app_name] = []
            self.profile["app_usage"][app_name].append({"hour": hour, "weekday": weekday})
            # Keep only last 100 entries per app
            self.profile["app_usage"][app_name] = self.profile["app_usage"][app_name][-100:]

        # ── 2. Search / Query Topics ──
        topics = self._extract_topics(text_lower)
        if topics:
            event["type"] = event.get("type", "query")
            event["topics"] = topics
            for topic in topics:
                self.profile["search_topics"][topic] = self.profile["search_topics"].get(topic, 0) + 1

        # ── 3. Website / Domain Access ──
        domain = self._extract_domain(text_lower)
        if domain:
            event["type"] = "web_access"
            event["domain"] = domain
            self.profile["website_domains"][domain] = self.profile["website_domains"].get(domain, 0) + 1

        # ── 4. Command Stem Frequency ──
        stem = self._extract_command_stem(text_lower)
        if stem:
            self.profile["command_frequency"][stem] = self.profile["command_frequency"].get(stem, 0) + 1

        # ── 5. System Metrics Snapshot ──
        if psutil:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    event["battery"] = battery.percent
                    event["plugged"] = battery.power_plugged
                event["cpu"] = psutil.cpu_percent(interval=0)
                event["ram"] = psutil.virtual_memory().percent
            except Exception:
                pass

        self.events.append(event)

        # ── Run Pattern Detection (lightweight, every 10 commands) ──
        if self.profile["total_commands"] % 10 == 0:
            self._detect_patterns()

        # ── Weekly Recalculation ──
        last_recalc = self.profile.get("last_weekly_recalc", "")
        if not last_recalc or (now - datetime.fromisoformat(last_recalc)).days >= 7:
            self._weekly_recalculate()
            self.profile["last_weekly_recalc"] = now.isoformat()

        self._save_profile()
        self._save_events()

    # ══════════════════════════════════════════
    #  PATTERN DETECTION
    # ══════════════════════════════════════════

    def _detect_patterns(self):
        """Analyze accumulated data to detect habits, routines, and interests."""

        # ── Habit Detection: action repeats 3+ times in similar time windows ──
        new_habits = []
        for app, entries in self.profile["app_usage"].items():
            if len(entries) < HABIT_THRESHOLD:
                continue
            # Group by approximate hour
            hour_counts = Counter(e["hour"] for e in entries)
            for peak_hour, count in hour_counts.most_common(3):
                if count >= HABIT_THRESHOLD:
                    confidence = min(100, int((count / len(entries)) * 100) + 10)
                    new_habits.append({
                        "action": f"open {app}",
                        "typical_hour": peak_hour,
                        "confidence": confidence,
                        "domain": self._classify_domain(app),
                        "count": count,
                    })

        self.profile["habits"] = new_habits

        # ── Routine Detection: weekly recurring patterns ──
        new_routines = []
        for app, entries in self.profile["app_usage"].items():
            weekday_counts = Counter(e["weekday"] for e in entries)
            for day, count in weekday_counts.most_common(3):
                if count >= ROUTINE_WEEKLY_THRESH:
                    # Find typical hour for this day
                    day_hours = [e["hour"] for e in entries if e["weekday"] == day]
                    typical_hour = Counter(day_hours).most_common(1)[0][0] if day_hours else 12
                    confidence = min(100, int((count / max(len(entries), 1)) * 100) + 15)
                    new_routines.append({
                        "action": f"open {app}",
                        "weekday": day,
                        "hour": typical_hour,
                        "confidence": confidence,
                    })

        self.profile["routines"] = new_routines

        # ── Interest Area Detection: topic appears frequently ──
        new_interests = []
        for topic, count in self.profile["search_topics"].items():
            if count >= INTEREST_THRESHOLD:
                strength = min(100, int(math.log2(count + 1) * 25))
                new_interests.append({
                    "topic": topic,
                    "strength": strength,
                    "query_count": count,
                })

        self.profile["interest_areas"] = new_interests

        # ── System Pattern Detection ──
        self._detect_system_patterns()

        # ── Peak Productivity Hours ──
        hour_activity = Counter()
        for event in self.events:
            hour_activity[event.get("hour", 12)] += 1
        if hour_activity:
            top_hours = [h for h, _ in hour_activity.most_common(4)]
            self.profile["peak_productivity_hours"] = sorted(top_hours)

    def _detect_system_patterns(self):
        """Detect battery/CPU/RAM patterns tied to time of day."""
        patterns = []
        battery_events = [(e["hour"], e["battery"]) for e in self.events
                          if "battery" in e and not e.get("plugged", True)]

        if len(battery_events) >= 5:
            # Group by hour, find hours where battery is consistently low
            hour_battery = defaultdict(list)
            for hour, pct in battery_events:
                hour_battery[hour].append(pct)

            for hour, values in hour_battery.items():
                avg = sum(values) / len(values)
                if avg < 30 and len(values) >= 2:
                    confidence = min(100, len(values) * 20)
                    patterns.append({
                        "metric": "battery",
                        "pattern_desc": f"Battery tends to be low (~{int(avg)}%) around {hour}:00",
                        "hour": hour,
                        "confidence": confidence,
                    })

        self.profile["system_patterns"] = patterns

    # ══════════════════════════════════════════
    #  SUGGESTION GENERATION
    # ══════════════════════════════════════════

    def get_proactive_suggestion(self, current_text=""):
        """
        Evaluate detected patterns and generate a proactive suggestion.
        Respects: max 3/day, gap timer, confidence thresholds, suppression list.
        """
        now = datetime.now()
        current_time = time.time()
        current_text = current_text.lower().strip()
        hour = now.hour
        weekday = now.strftime("%A")

        # ── Guard: max suggestions per day ──
        if self.profile.get("suggestions_today", 0) >= MAX_SUGGESTIONS_DAY:
            return None

        # ── Guard: minimum gap between suggestions ──
        last_ts = self.profile.get("last_suggestion_ts", 0)
        if current_time - last_ts < SUGGESTION_GAP_SECS:
            return None

        suppressed = self.profile.get("suppressed_categories", [])
        candidates = []

        # ── Strategy 1: Habit-based Suggestion ──
        if "habits" not in suppressed:
            for habit in self.profile.get("habits", []):
                if abs(habit["typical_hour"] - hour) <= HOUR_WINDOW:
                    app = habit["action"].replace("open ", "")
                    # Only suggest if the current command is related or the user just started a session
                    if app in current_text or self.profile["total_commands"] % 5 == 1:
                        candidates.append({
                            "category": "habits",
                            "confidence": habit["confidence"],
                            "text_direct": f"Looks like this is usually your {app.title()} time. Ready to start your session?",
                            "text_soft": f"I noticed you often use {app.title()} around now. Would you like me to open it?",
                        })

        # ── Strategy 2: Routine-based Suggestion ──
        if "routines" not in suppressed:
            for routine in self.profile.get("routines", []):
                if routine["weekday"] == weekday and abs(routine["hour"] - hour) <= HOUR_WINDOW:
                    app = routine["action"].replace("open ", "")
                    candidates.append({
                        "category": "routines",
                        "confidence": routine["confidence"],
                        "text_direct": f"It's {weekday} — you usually work with {app.title()} around now. Shall I set things up?",
                        "text_soft": f"Just checking — it's your typical {app.title()} time on {weekday}s. Need it?",
                    })

        # ── Strategy 3: Interest Area Suggestion ──
        if "learning" not in suppressed:
            for interest in self.profile.get("interest_areas", []):
                topic = interest["topic"]
                # Trigger only when the user is searching something related
                if topic in current_text or any(kw in current_text for kw in topic.split("_")):
                    candidates.append({
                        "category": "learning",
                        "confidence": interest["strength"],
                        "text_direct": f"You've been exploring '{topic.replace('_', ' ').title()}' quite a lot. Want me to create a structured learning roadmap for you?",
                        "text_soft": f"I see you keep coming back to '{topic.replace('_', ' ').title()}'. Would a curated resource list help?",
                    })

        # ── Strategy 4: Battery Prediction ──
        if "system" not in suppressed:
            for pattern in self.profile.get("system_patterns", []):
                if pattern["metric"] == "battery" and abs(pattern.get("hour", 99) - hour) <= HOUR_WINDOW:
                    candidates.append({
                        "category": "system",
                        "confidence": pattern["confidence"],
                        "text_direct": "Heads-up: based on your usage patterns, your battery usually gets low around now. Consider plugging in.",
                        "text_soft": "Your battery might run low soon based on past patterns. Just letting you know.",
                    })

        # ── Strategy 5: Peak Productivity Nudge ──
        if "productivity" not in suppressed:
            peak_hours = self.profile.get("peak_productivity_hours", [])
            if hour in peak_hours and self.profile["total_commands"] > 20:
                # Only suggest occasionally, not every time
                if self.profile["total_commands"] % 15 == 0:
                    candidates.append({
                        "category": "productivity",
                        "confidence": 55,
                        "text_direct": f"This is typically one of your most productive hours. Make the most of it!",
                        "text_soft": f"Looks like this is usually your deep-focus time. Want to start your session?",
                    })

        # ── Strategy 6: Energy Pattern Awareness ──
        if "health" not in suppressed:
            energy = self.profile.get("energy_cycles", {})
            period = self._get_period(hour)
            total = sum(energy.values()) if energy else 0
            if total > 50 and energy.get(period, 0) / max(total, 1) > 0.4:
                # User is heavily concentrated in one period
                if self.profile["total_commands"] % 25 == 0:
                    candidates.append({
                        "category": "health",
                        "confidence": 45,
                        "text_soft": f"You seem to use your computer mostly during the {period}. Consider taking breaks to maintain focus.",
                    })

        if not candidates:
            return None

        # ── Select best candidate by confidence ──
        best = max(candidates, key=lambda c: c["confidence"])

        # ── Check suppression history ──
        cat = best["category"]
        acceptance = self.profile.get("suggestion_acceptance", {}).get(cat, {"accepted": 0, "dismissed": 0})
        if acceptance.get("dismissed", 0) >= DISMISS_SUPPRESS:
            return None

        # ── Confidence-based delivery ──
        confidence = best["confidence"]
        if confidence >= CONFIDENCE_DIRECT:
            message = best.get("text_direct", best.get("text_soft", ""))
        elif confidence >= CONFIDENCE_SOFT:
            message = best.get("text_soft", best.get("text_direct", ""))
        else:
            # Confidence too low — continue observing silently
            return None

        if not message:
            return None

        # ── Record suggestion delivery ──
        self.profile["suggestions_today"] = self.profile.get("suggestions_today", 0) + 1
        self.profile["last_suggestion_ts"] = current_time
        self._save_profile()

        return f" 🔮 {message}"

    # ══════════════════════════════════════════
    #  SUGGESTION FEEDBACK
    # ══════════════════════════════════════════

    def accept_suggestion(self, category):
        """User accepted a suggestion — boost confidence."""
        if category not in self.profile["suggestion_acceptance"]:
            self.profile["suggestion_acceptance"][category] = {"accepted": 0, "dismissed": 0}
        self.profile["suggestion_acceptance"][category]["accepted"] += 1
        self._save_profile()

    def dismiss_suggestion(self, category):
        """User dismissed a suggestion — track for potential suppression."""
        if category not in self.profile["suggestion_acceptance"]:
            self.profile["suggestion_acceptance"][category] = {"accepted": 0, "dismissed": 0}
        self.profile["suggestion_acceptance"][category]["dismissed"] += 1
        self._save_profile()

    def suppress_category(self, category):
        """User said 'stop suggesting this' — permanently suppress."""
        if category not in self.profile.get("suppressed_categories", []):
            self.profile["suppressed_categories"].append(category)
            self._save_profile()

    # ══════════════════════════════════════════
    #  WEEKLY RECALCULATION
    # ══════════════════════════════════════════

    def _weekly_recalculate(self):
        """Recalculate behavioral weights, decay old data, adjust predictions."""

        # ── Decay old app usage entries ──
        for app in self.profile["app_usage"]:
            entries = self.profile["app_usage"][app]
            # Keep only last 50 entries (roughly 2 months of daily use)
            self.profile["app_usage"][app] = entries[-50:]

        # ── Decay search topic counts ──
        decayed = {}
        for topic, count in self.profile["search_topics"].items():
            new_count = max(0, int(count * WEEKLY_DECAY))
            if new_count > 0:
                decayed[topic] = new_count
        self.profile["search_topics"] = decayed

        # ── Re-detect patterns with fresh weights ──
        self._detect_patterns()

    # ══════════════════════════════════════════
    #  BEHAVIORAL PROFILE REPORT
    # ══════════════════════════════════════════

    def get_profile_summary(self):
        """Generate a human-readable summary of the user's behavioral profile."""
        p = self.profile
        lines = ["📊 Your Behavioral Profile:"]

        # Top apps
        if p["app_usage"]:
            top_apps = sorted(p["app_usage"].items(), key=lambda x: len(x[1]), reverse=True)[:5]
            app_list = ", ".join(f"{a[0].title()} ({len(a[1])}x)" for a in top_apps)
            lines.append(f"  🖥️ Frequent Apps: {app_list}")

        # Peak hours
        if p["peak_productivity_hours"]:
            hours_str = ", ".join(f"{h}:00" for h in p["peak_productivity_hours"])
            lines.append(f"  ⏰ Peak Hours: {hours_str}")

        # Interests
        if p["interest_areas"]:
            topics = ", ".join(i["topic"].replace("_", " ").title() for i in p["interest_areas"][:5])
            lines.append(f"  📚 Interests: {topics}")

        # Habits
        if p["habits"]:
            hab_list = ", ".join(f"{h['action'].title()} ~{h['typical_hour']}:00 ({h['confidence']}%)"
                                 for h in p["habits"][:3])
            lines.append(f"  🔄 Habits: {hab_list}")

        # Energy pattern
        if p["energy_cycles"]:
            peak_period = max(p["energy_cycles"], key=p["energy_cycles"].get)
            lines.append(f"  ⚡ Peak Energy Period: {peak_period.title()}")

        # Stats
        lines.append(f"  📈 Total Commands Tracked: {p.get('total_commands', 0)}")

        return "\n".join(lines)

    # ══════════════════════════════════════════
    #  EXTRACTION HELPERS
    # ══════════════════════════════════════════

    def _extract_app_name(self, text):
        """Extract application name from command text."""
        match = re.search(r'\b(?:open|launch|start|run)\s+([a-zA-Z0-9\s]+?)(?:\s+and|\s+in|\s+on|$)', text)
        if match:
            app = match.group(1).strip()
            # Filter out non-app words
            noise = ['a', 'the', 'my', 'this', 'that', 'it', 'some', 'any', 'new', 'folder',
                     'file', 'tab', 'page', 'website', 'browser', 'google', 'search']
            if app and app not in noise and len(app) > 1:
                return app
        return None

    def _extract_topics(self, text):
        """Extract knowledge topics from queries and searches."""
        topics = []

        # ── Topic clusters ──
        topic_map = {
            "artificial_intelligence": ['ai', 'artificial intelligence', 'machine learning', 'ml',
                                        'deep learning', 'neural network', 'nlp', 'computer vision',
                                        'tensorflow', 'pytorch', 'gpt', 'llm', 'transformer'],
            "web_development":         ['html', 'css', 'javascript', 'react', 'angular', 'vue',
                                        'nodejs', 'node js', 'frontend', 'backend', 'fullstack',
                                        'api', 'rest api', 'webpack', 'typescript'],
            "data_science":            ['data science', 'pandas', 'numpy', 'matplotlib',
                                        'data analysis', 'statistics', 'visualization', 'big data',
                                        'hadoop', 'spark', 'kaggle', 'dataset'],
            "cybersecurity":           ['cybersecurity', 'hacking', 'penetration testing', 'firewall',
                                        'encryption', 'malware', 'phishing', 'vpn', 'security'],
            "mobile_development":      ['android', 'ios', 'flutter', 'kotlin', 'swift',
                                        'react native', 'mobile app', 'apk'],
            "cloud_computing":         ['aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes',
                                        'devops', 'ci cd', 'serverless', 'microservices'],
            "programming":             ['python', 'java', 'c++', 'rust', 'golang', 'ruby',
                                        'programming', 'coding', 'algorithm', 'dsa',
                                        'data structure', 'leetcode', 'competitive'],
            "design":                  ['ui design', 'ux', 'figma', 'photoshop', 'illustrator',
                                        'canva', 'graphic design', 'wireframe', 'prototype'],
            "business":                ['startup', 'marketing', 'finance', 'stock market',
                                        'investment', 'crypto', 'bitcoin', 'entrepreneur',
                                        'business plan', 'revenue'],
            "health_fitness":          ['workout', 'exercise', 'meditation', 'yoga', 'diet',
                                        'nutrition', 'mental health', 'sleep', 'wellness'],
            "entertainment":           ['movie', 'music', 'gaming', 'anime', 'netflix',
                                        'spotify', 'youtube', 'podcast', 'series'],
        }

        query_indicators = ['search', 'what is', 'tell me about', 'research', 'write about',
                            'information about', 'learn', 'explain', 'how to', 'tutorial',
                            'wikipedia', 'define']

        is_query = any(ind in text for ind in query_indicators)

        for cluster, keywords in topic_map.items():
            if any(kw in text for kw in keywords):
                if is_query or any(kw in text for kw in keywords[:3]):
                    topics.append(cluster)

        return topics

    def _extract_domain(self, text):
        """Extract website domain from command."""
        match = re.search(r'open\s+(\w+(?:\.\w+)?)\s*(?:in|on|website|site)?', text)
        if match:
            domain = match.group(1).lower()
            known_sites = ['youtube', 'facebook', 'twitter', 'instagram', 'github',
                           'linkedin', 'reddit', 'stackoverflow', 'gmail', 'amazon',
                           'netflix', 'wikipedia', 'google', 'spotify']
            if domain in known_sites:
                return domain
        return None

    def _extract_command_stem(self, text):
        """Extract the action verb/stem from a command."""
        stems = ['open', 'close', 'search', 'play', 'pause', 'set',
                 'check', 'increase', 'decrease', 'navigate', 'write',
                 'research', 'create', 'type', 'send', 'translate']
        for stem in stems:
            if text.startswith(stem) or f" {stem} " in text:
                return stem
        return None

    def _classify_domain(self, app_name):
        """Classify an app into a behavioral domain."""
        app = app_name.lower()
        domain_map = {
            "productivity": ['vscode', 'visual studio', 'code', 'word', 'excel',
                             'powerpoint', 'notepad', 'sublime', 'atom', 'pycharm',
                             'intellij', 'eclipse', 'terminal', 'cmd', 'powershell'],
            "entertainment": ['spotify', 'netflix', 'youtube', 'vlc', 'media player',
                              'steam', 'epic games', 'discord'],
            "communication": ['whatsapp', 'telegram', 'slack', 'teams', 'zoom',
                              'skype', 'outlook', 'gmail', 'mail'],
            "learning":      ['browser', 'chrome', 'firefox', 'edge', 'pdf',
                              'reader', 'kindle'],
            "system":        ['task manager', 'settings', 'control panel',
                              'file explorer', 'calculator'],
        }
        for domain, apps in domain_map.items():
            if any(a in app for a in apps):
                return domain
        return "general"

    def _get_period(self, hour):
        """Classify hour into time period."""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
