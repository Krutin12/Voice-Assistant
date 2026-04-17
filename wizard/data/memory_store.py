"""
🗂 LONG-TERM MEMORY SYSTEM
============================
Persistent structured memory across sessions.

Categories:
  1. Projects Memory       — names, tech, deadlines, progress, issues
  2. Technical Stack       — languages, frameworks, tools, IDE, libs
  3. Mistake & Fix Memory  — recurring errors, solutions, fix success rate
  4. Deadline & Commitment — deadlines, postponements, missed tasks, priorities
  5. Behavioral Pattern    — delegated to BehaviorLearningEngine

Storage: JSON file on disk, loaded lazily.
"""

import os
import json
import re
from datetime import datetime, timedelta


class LongTermMemory:
    """Persistent structured memory that survives across sessions."""

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory_logs')
        os.makedirs(self.data_dir, exist_ok=True)
        self.memory_file = os.path.join(self.data_dir, 'long_term_memory.json')
        self._load()

    # ══════════════════════════════════════════
    #  PERSISTENCE
    # ══════════════════════════════════════════

    def _load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            except Exception:
                self.memory = self._default()
        else:
            self.memory = self._default()

    def _save(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, default=str)
        except Exception:
            pass

    def _default(self):
        return {
            "projects": [],
            "tech_stack": {
                "languages": [],
                "frameworks": [],
                "tools": [],
                "ide_preferences": [],
                "deployment_platforms": [],
                "libraries": [],
            },
            "mistakes": [],
            "deadlines": [],
            "meta": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
        }

    # ══════════════════════════════════════════
    #  1️⃣ PROJECTS MEMORY
    # ══════════════════════════════════════════

    def detect_project_context(self, text):
        """Auto-detect project references from commands and store them."""
        text_lower = text.lower()
        updated = False

        # Detect project-related keywords
        project_patterns = [
            r'(?:working on|building|developing|creating|my)\s+(?:a\s+)?([a-zA-Z0-9\s\-_]+?)(?:\s+project|\s+app|\s+application|\s+website|\s+system|\s+tool)',
            r'(?:project|app|application)\s+(?:called|named)\s+([a-zA-Z0-9\s\-_]+)',
            r'(?:open|launch)\s+(?:my\s+)?([a-zA-Z0-9\-_]+)\s+(?:project|repo|repository)',
        ]

        for pattern in project_patterns:
            match = re.search(pattern, text_lower)
            if match:
                project_name = match.group(1).strip()
                if project_name and len(project_name) > 2:
                    self._add_or_update_project(project_name, text_lower)
                    updated = True

        # Detect technologies mentioned → link to active project
        techs = self._extract_technologies(text_lower)
        if techs:
            active = self._get_most_recent_project()
            if active:
                for tech in techs:
                    if tech not in active.get("technologies", []):
                        active.setdefault("technologies", []).append(tech)
                        updated = True

        if updated:
            self.memory["meta"]["last_updated"] = datetime.now().isoformat()
            self._save()

    def _add_or_update_project(self, name, context=""):
        """Add a new project or update existing one."""
        # Check if project exists
        for p in self.memory["projects"]:
            if p["name"].lower() == name.lower():
                p["last_seen"] = datetime.now().isoformat()
                p["mention_count"] = p.get("mention_count", 0) + 1
                return p

        # New project
        project = {
            "name": name,
            "created": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "technologies": [],
            "status": "active",
            "issues": [],
            "mention_count": 1,
        }
        self.memory["projects"].append(project)
        return project

    def _get_most_recent_project(self):
        """Get the most recently active project."""
        if not self.memory["projects"]:
            return None
        return max(self.memory["projects"], key=lambda p: p.get("last_seen", ""))

    def get_project_summary(self):
        """Return a brief summary of tracked projects."""
        projects = self.memory["projects"]
        if not projects:
            return "No projects tracked yet."
        lines = []
        for p in sorted(projects, key=lambda x: x.get("last_seen", ""), reverse=True)[:5]:
            techs = ", ".join(p.get("technologies", [])[:5]) or "—"
            lines.append(f"  • {p['name'].title()} [{p.get('status', 'active')}] — Tech: {techs}")
        return "📂 Projects:\n" + "\n".join(lines)

    # ══════════════════════════════════════════
    #  2️⃣ TECHNICAL STACK MEMORY
    # ══════════════════════════════════════════

    def update_tech_stack(self, text):
        """Detect and memorize technical tools, languages, frameworks."""
        text_lower = text.lower()
        techs = self._extract_technologies(text_lower)
        stack = self.memory["tech_stack"]
        updated = False

        for tech in techs:
            category = self._classify_tech(tech)
            if tech not in stack.get(category, []):
                stack.setdefault(category, []).append(tech)
                updated = True

        # Detect IDE preferences
        ide_map = {
            'vscode': 'VS Code', 'visual studio code': 'VS Code', 'pycharm': 'PyCharm',
            'intellij': 'IntelliJ', 'sublime': 'Sublime Text', 'atom': 'Atom',
            'vim': 'Vim', 'neovim': 'NeoVim', 'eclipse': 'Eclipse', 'android studio': 'Android Studio',
        }
        for key, name in ide_map.items():
            if key in text_lower and name not in stack.get("ide_preferences", []):
                stack.setdefault("ide_preferences", []).append(name)
                updated = True

        if updated:
            self.memory["meta"]["last_updated"] = datetime.now().isoformat()
            self._save()

    def get_tech_stack_summary(self):
        """Return formatted tech stack."""
        s = self.memory["tech_stack"]
        parts = []
        if s.get("languages"): parts.append(f"  🔤 Languages: {', '.join(s['languages'][:8])}")
        if s.get("frameworks"): parts.append(f"  📦 Frameworks: {', '.join(s['frameworks'][:8])}")
        if s.get("tools"): parts.append(f"  🔧 Tools: {', '.join(s['tools'][:8])}")
        if s.get("ide_preferences"): parts.append(f"  💻 IDE: {', '.join(s['ide_preferences'][:4])}")
        if s.get("libraries"): parts.append(f"  📚 Libraries: {', '.join(s['libraries'][:8])}")
        if not parts:
            return "No technical stack data yet."
        return "🛠️ Tech Stack:\n" + "\n".join(parts)

    # ══════════════════════════════════════════
    #  3️⃣ MISTAKE & FIX MEMORY
    # ══════════════════════════════════════════

    def record_error(self, error_text, fix_text=""):
        """Track a recurring error and its solution."""
        error_key = self._normalize_error(error_text)

        for mistake in self.memory["mistakes"]:
            if mistake["error_key"] == error_key:
                mistake["occurrences"] += 1
                mistake["last_seen"] = datetime.now().isoformat()
                if fix_text and fix_text not in mistake["fixes"]:
                    mistake["fixes"].append(fix_text)
                    mistake["fix_success_rate"] = len(mistake["fixes"]) / max(mistake["occurrences"], 1)
                self._save()
                return mistake

        # New error
        entry = {
            "error_key": error_key,
            "error_text": error_text[:200],
            "fixes": [fix_text] if fix_text else [],
            "occurrences": 1,
            "fix_success_rate": 0.0,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
        }
        self.memory["mistakes"].append(entry)
        self._save()
        return entry

    def find_previous_fix(self, error_text):
        """Check if we've seen this error before and have a fix."""
        error_key = self._normalize_error(error_text)
        for mistake in self.memory["mistakes"]:
            if mistake["error_key"] == error_key and mistake["fixes"]:
                best_fix = mistake["fixes"][-1]  # Most recent fix
                return {
                    "found": True,
                    "fix": best_fix,
                    "occurrences": mistake["occurrences"],
                    "success_rate": mistake.get("fix_success_rate", 0),
                }
        return {"found": False}

    def detect_error_in_text(self, text):
        """Auto-detect error patterns in user speech and log them."""
        text_lower = text.lower()
        error_indicators = [
            'error', 'exception', 'traceback', 'failed', 'bug', 'crash',
            'not working', 'broken', 'issue', 'problem', 'stuck',
            'modulenotfounderror', 'importerror', 'syntaxerror', 'typeerror',
            'keyerror', 'valueerror', 'attributeerror', 'indentationerror',
        ]

        if any(ind in text_lower for ind in error_indicators):
            # Extract the error essence
            error_match = re.search(r'(?:error|exception|bug|issue|problem)[:\s]+(.+?)(?:\.|$)', text_lower)
            if error_match:
                self.record_error(error_match.group(1).strip())
                return True
        return False

    def _normalize_error(self, error_text):
        """Create a normalized key for an error for deduplication."""
        # Remove numbers, paths, and normalize whitespace
        key = re.sub(r'[0-9]+', 'N', error_text.lower())
        key = re.sub(r'[/\\][\w./\\]+', 'PATH', key)
        key = re.sub(r'\s+', ' ', key).strip()
        return key[:100]

    # ══════════════════════════════════════════
    #  4️⃣ DEADLINE & COMMITMENT MEMORY
    # ══════════════════════════════════════════

    def detect_deadline(self, text):
        """Auto-detect deadline mentions and store them."""
        text_lower = text.lower()

        deadline_patterns = [
            r'(?:deadline|due|submit|submission)\s+(?:is\s+)?(?:on\s+|by\s+)?(.+?)(?:\.|$)',
            r'(?:have to|need to|must)\s+(?:finish|complete|submit)\s+(.+?)\s+(?:by|before|until)\s+(.+?)(?:\.|$)',
            r'(?:remind me|reminder)\s+(?:about|to|for)\s+(.+?)\s+(?:by|on|at|before)\s+(.+?)(?:\.|$)',
        ]

        for pattern in deadline_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                task = groups[0].strip() if len(groups) >= 1 else text_lower
                deadline_str = groups[1].strip() if len(groups) >= 2 else ""

                entry = {
                    "task": task,
                    "deadline_raw": deadline_str,
                    "created": datetime.now().isoformat(),
                    "status": "pending",
                    "postponed_count": 0,
                }
                self.memory["deadlines"].append(entry)
                self._save()
                return entry
        return None

    def get_upcoming_deadlines(self):
        """Return pending deadlines."""
        pending = [d for d in self.memory["deadlines"] if d.get("status") == "pending"]
        if not pending:
            return None
        lines = []
        for d in pending[-5:]:
            postpone_note = f" (postponed {d['postponed_count']}x)" if d.get('postponed_count', 0) > 0 else ""
            lines.append(f"  ⏰ {d['task'].title()}{postpone_note}")
        return "📅 Upcoming Commitments:\n" + "\n".join(lines)

    def get_deadline_warning(self):
        """Check if any deadline needs an escalated reminder."""
        pending = [d for d in self.memory["deadlines"] if d.get("status") == "pending"]
        for d in pending:
            if d.get("postponed_count", 0) >= 2:
                return f"⚠️ You've postponed '{d['task'].title()}' {d['postponed_count']} times. This might need your attention today."
        return None

    # ══════════════════════════════════════════
    #  EXTRACTION HELPERS
    # ══════════════════════════════════════════

    def _extract_technologies(self, text):
        """Extract programming languages, frameworks, tools from text."""
        tech_keywords = {
            # Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'rust', 'golang', 'go',
            'ruby', 'php', 'swift', 'kotlin', 'dart', 'scala', 'r language', 'matlab',
            # Frameworks
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'express',
            'nextjs', 'next.js', 'nuxt', 'svelte', 'flutter', 'react native', 'electron',
            'tailwind', 'bootstrap', 'laravel', 'rails', 'asp.net', '.net',
            # Tools
            'docker', 'kubernetes', 'git', 'github', 'gitlab', 'jenkins', 'terraform',
            'ansible', 'nginx', 'apache', 'redis', 'mongodb', 'postgresql', 'mysql',
            'sqlite', 'firebase', 'supabase', 'aws', 'azure', 'gcp',
            # Libraries
            'numpy', 'pandas', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
            'matplotlib', 'opencv', 'selenium', 'beautifulsoup', 'requests',
            'pyautogui', 'pyttsx3', 'speechrecognition', 'openai', 'langchain',
        }
        found = []
        for tech in tech_keywords:
            if tech in text:
                found.append(tech)
        return found

    def _classify_tech(self, tech):
        """Classify a tech into the right stack category."""
        languages = {'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'rust',
                     'golang', 'go', 'ruby', 'php', 'swift', 'kotlin', 'dart', 'scala', 'matlab'}
        frameworks = {'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring',
                      'express', 'nextjs', 'next.js', 'nuxt', 'svelte', 'flutter',
                      'react native', 'electron', 'tailwind', 'bootstrap', 'laravel',
                      'rails', 'asp.net', '.net'}
        tools = {'docker', 'kubernetes', 'git', 'github', 'gitlab', 'jenkins', 'terraform',
                 'ansible', 'nginx', 'apache', 'redis', 'mongodb', 'postgresql', 'mysql',
                 'sqlite', 'firebase', 'supabase', 'aws', 'azure', 'gcp'}

        if tech in languages: return "languages"
        if tech in frameworks: return "frameworks"
        if tech in tools: return "tools"
        return "libraries"

    # ══════════════════════════════════════════
    #  FULL MEMORY REPORT
    # ══════════════════════════════════════════

    def get_full_report(self):
        """Generate a complete memory report."""
        parts = ["🧠 Long-Term Memory Report:"]
        parts.append(self.get_project_summary())
        parts.append(self.get_tech_stack_summary())

        # Mistakes summary
        mistakes = self.memory["mistakes"]
        if mistakes:
            top = sorted(mistakes, key=lambda m: m["occurrences"], reverse=True)[:3]
            m_lines = [f"  • {m['error_text'][:60]}... ({m['occurrences']}x)" for m in top]
            parts.append("🐛 Top Recurring Issues:\n" + "\n".join(m_lines))

        # Deadlines
        dl = self.get_upcoming_deadlines()
        if dl:
            parts.append(dl)

        return "\n\n".join(parts)
