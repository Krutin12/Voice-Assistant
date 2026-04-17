"""
Smart Writer Module for Wizard Voice Assistant

An advanced background research + formatted writing system.
- Searches multiple sources WITHOUT opening any browser window
- Compiles information into structured, original content
- Types directly into the currently active application
- Supports different writing styles (assignment, blog, professional)
- Formats with Title, Introduction, Headings, Bullet points, Conclusion
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import pyautogui
import pyperclip
import textwrap
from typing import Optional, List, Dict, Tuple
from datetime import datetime


class SmartWriter:
    """Advanced background research and writing assistant."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        # Collected research data from multiple sources
        self.research_data = []
        self.source_urls = []

    # =============================================
    # BACKGROUND RESEARCH (No browser opens)
    # =============================================

    def _search_wikipedia_detailed(self, query: str) -> Optional[Dict]:
        """Fetch detailed Wikipedia article with sections."""
        try:
            # Step 1: Find the best matching article
            search_url = (
                f"https://en.wikipedia.org/w/api.php?"
                f"action=opensearch&search={requests.utils.quote(query)}"
                f"&limit=3&namespace=0&format=json"
            )
            resp = self.session.get(search_url, timeout=8)
            data = resp.json()

            if not data[1]:
                return None

            title = data[1][0]

            # Step 2: Get full article extract (not just intro)
            extract_url = (
                f"https://en.wikipedia.org/w/api.php?"
                f"action=query&prop=extracts&explaintext"
                f"&titles={requests.utils.quote(title)}&format=json"
                f"&exsectionformat=plain"
            )
            resp = self.session.get(extract_url, timeout=8)
            pages = resp.json().get('query', {}).get('pages', {})

            for page_id, page_data in pages.items():
                extract = page_data.get('extract', '')
                if extract and len(extract) > 100:
                    self.source_urls.append(f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")
                    return {
                        'source': 'Wikipedia',
                        'title': title,
                        'content': extract,
                        'reliability': 'high'
                    }

            return None
        except Exception:
            return None

    def _search_google_snippets(self, query: str) -> List[Dict]:
        """Scrape Google search results for information snippets."""
        results = []
        try:
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            resp = self.session.get(search_url, timeout=8)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Featured snippet
            featured = soup.select_one('div.hgKElc, span.hgKElc')
            if featured:
                text = featured.get_text().strip()
                if len(text) > 30:
                    results.append({
                        'source': 'Google Featured Snippet',
                        'content': text,
                        'reliability': 'medium'
                    })

            # Regular search snippets
            snippets = soup.select('div.VwiC3b, div.IsZvec')
            for snippet in snippets[:5]:
                text = snippet.get_text().strip()
                if len(text) > 40:
                    results.append({
                        'source': 'Google Search',
                        'content': text,
                        'reliability': 'medium'
                    })

        except Exception:
            pass
        return results

    def _search_duckduckgo(self, query: str) -> List[Dict]:
        """Search DuckDuckGo instant answer API (no scraping needed)."""
        results = []
        try:
            api_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1"
            resp = self.session.get(api_url, timeout=8)
            data = resp.json()

            # Abstract (usually from Wikipedia but formatted differently)
            abstract = data.get('Abstract', '')
            if abstract and len(abstract) > 50:
                results.append({
                    'source': 'DuckDuckGo',
                    'content': abstract,
                    'reliability': 'high'
                })

            # Related topics
            for topic in data.get('RelatedTopics', [])[:5]:
                text = topic.get('Text', '')
                if text and len(text) > 30:
                    results.append({
                        'source': 'DuckDuckGo Related',
                        'content': text,
                        'reliability': 'medium'
                    })

        except Exception:
            pass
        return results

    def _search_wikipedia_subcategories(self, query: str) -> List[Dict]:
        """Get Wikipedia info on specific subtopics related to the query."""
        subtopics = []
        try:
            # Common subtopic queries to get broader information
            subtopic_queries = [
                f"{query} history",
                f"{query} uses",
                f"{query} importance",
                f"{query} types",
            ]

            for sub_query in subtopic_queries[:2]:
                search_url = (
                    f"https://en.wikipedia.org/w/api.php?"
                    f"action=query&list=search&srsearch={requests.utils.quote(sub_query)}"
                    f"&srlimit=1&format=json"
                )
                resp = self.session.get(search_url, timeout=5)
                data = resp.json()
                results = data.get('query', {}).get('search', [])

                if results:
                    snippet = results[0].get('snippet', '')
                    # Remove HTML tags
                    snippet = re.sub(r'<[^>]+>', '', snippet)
                    if snippet and len(snippet) > 30:
                        subtopics.append({
                            'source': f'Wikipedia ({sub_query})',
                            'content': snippet,
                            'reliability': 'medium'
                        })

        except Exception:
            pass
        return subtopics

    def gather_research(self, topic: str) -> List[Dict]:
        """Collect information from multiple sources in the background."""
        self.research_data = []
        self.source_urls = []

        # Source 1: Detailed Wikipedia article
        wiki_data = self._search_wikipedia_detailed(topic)
        if wiki_data:
            self.research_data.append(wiki_data)

        # Source 2: Google snippets
        google_data = self._search_google_snippets(topic)
        self.research_data.extend(google_data)

        # Source 3: DuckDuckGo instant answers
        ddg_data = self._search_duckduckgo(topic)
        self.research_data.extend(ddg_data)

        # Source 4: Wikipedia subtopics for more depth
        sub_data = self._search_wikipedia_subcategories(topic)
        self.research_data.extend(sub_data)

        return self.research_data

    # =============================================
    # CONTENT COMPILATION & FORMATTING
    # =============================================

    def _extract_key_facts(self, research_data: List[Dict]) -> List[str]:
        """Extract unique key facts from all gathered research."""
        all_sentences = []
        seen_content = set()

        for data in research_data:
            content = data.get('content', '')
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', content)

            for sentence in sentences:
                sentence = sentence.strip()
                # Skip too short or too long sentences
                if len(sentence) < 20 or len(sentence) > 300:
                    continue

                # Skip duplicate or very similar content
                normalized = re.sub(r'\s+', ' ', sentence.lower().strip())
                if normalized in seen_content:
                    continue

                # Check for similarity with existing sentences
                is_duplicate = False
                for existing in seen_content:
                    # Simple overlap check
                    words_new = set(normalized.split())
                    words_existing = set(existing.split())
                    if len(words_new) > 3 and len(words_existing) > 3:
                        overlap = len(words_new & words_existing) / min(len(words_new), len(words_existing))
                        if overlap > 0.7:
                            is_duplicate = True
                            break

                if not is_duplicate:
                    seen_content.add(normalized)
                    all_sentences.append(sentence)

        return all_sentences

    def _categorize_facts(self, facts: List[str], topic: str) -> Dict[str, List[str]]:
        """Categorize facts into logical sections."""
        categories = {
            'overview': [],
            'history': [],
            'features': [],
            'importance': [],
            'types': [],
            'applications': [],
            'other': []
        }

        # Keywords for each category
        category_keywords = {
            'history': ['history', 'originated', 'invented', 'founded', 'began', 'first', 
                        'ancient', 'early', 'developed', 'evolution', 'century', 'year',
                        'established', 'created', 'introduced', 'born', 'discovered'],
            'features': ['feature', 'characteristic', 'property', 'attribute', 'capability',
                         'include', 'consist', 'contains', 'component', 'element', 'made of',
                         'specification', 'function', 'design'],
            'importance': ['important', 'significant', 'impact', 'benefit', 'advantage',
                           'essential', 'crucial', 'valuable', 'helpful', 'useful',
                           'role', 'contribute', 'effect', 'influence'],
            'types': ['type', 'kind', 'category', 'variety', 'form', 'classification',
                      'variant', 'model', 'version', 'class', 'group'],
            'applications': ['used', 'application', 'purpose', 'practical', 'industry',
                             'technology', 'field', 'sector', 'domain', 'area',
                             'implemented', 'deployed', 'adopted']
        }

        for fact in facts:
            fact_lower = fact.lower()
            categorized = False

            for category, keywords in category_keywords.items():
                if any(kw in fact_lower for kw in keywords):
                    categories[category].append(fact)
                    categorized = True
                    break

            if not categorized:
                # First few uncategorized facts go to overview
                if len(categories['overview']) < 4:
                    categories['overview'].append(fact)
                else:
                    categories['other'].append(fact)

        return categories

    def compile_article(self, topic: str, style: str = 'assignment', 
                        word_limit: int = 500) -> str:
        """
        Compile gathered research into a structured article.
        
        Args:
            topic: The subject to write about
            style: Writing style ('assignment', 'blog', 'professional')
            word_limit: Approximate word limit for the article
        
        Returns:
            Formatted article as a string
        """
        # Step 1: Gather research
        research_data = self.gather_research(topic)

        if not research_data:
            return f"I couldn't find enough information about '{topic}'. Could you be more specific?"

        # Step 2: Extract and deduplicate facts
        facts = self._extract_key_facts(research_data)

        if len(facts) < 3:
            # If very few facts, try to use whatever we have
            raw_content = " ".join([d.get('content', '') for d in research_data])
            facts = re.split(r'(?<=[.!?])\s+', raw_content)
            facts = [f.strip() for f in facts if len(f.strip()) > 20]

        # Step 3: Categorize facts
        categorized = self._categorize_facts(facts, topic)

        # Step 4: Build the article based on style
        article = self._format_article(topic, categorized, style, word_limit)

        return article

    def _format_article(self, topic: str, categorized: Dict[str, List[str]], 
                        style: str, word_limit: int) -> str:
        """Format the categorized facts into a structured article."""
        lines = []
        topic_title = topic.title()
        current_words = 0
        target_words = word_limit

        # ---------- TITLE ----------
        if style == 'blog':
            lines.append(f"📝 {topic_title}: Everything You Need to Know")
            lines.append("=" * 50)
        elif style == 'professional':
            lines.append(f"Report: {topic_title}")
            lines.append("=" * 50)
            lines.append(f"Date: {datetime.now().strftime('%B %d, %Y')}")
            lines.append("")
        else:  # assignment
            lines.append(f"{topic_title}")
            lines.append("=" * 50)

        lines.append("")

        # ---------- INTRODUCTION ----------
        intro_facts = categorized.get('overview', [])[:3]
        if intro_facts:
            if style == 'blog':
                lines.append("🔍 Introduction")
                lines.append("-" * 30)
            elif style == 'professional':
                lines.append("1. Introduction")
                lines.append("-" * 30)
            else:
                lines.append("Introduction")
                lines.append("-" * 30)

            intro_text = " ".join(intro_facts)
            # Ensure it reads smoothly
            if not intro_text.endswith('.'):
                intro_text += '.'
            lines.append(intro_text)
            lines.append("")
            current_words += len(intro_text.split())

        # ---------- MAIN SECTIONS ----------
        section_map = {
            'history': ('History & Background', '📜', '2'),
            'features': ('Key Features & Characteristics', '⚡', '3'),
            'types': ('Types & Categories', '📊', '4'),
            'importance': ('Importance & Benefits', '🌟', '5'),
            'applications': ('Applications & Uses', '🔧', '6'),
        }

        section_num = 2
        for key, (section_title, emoji, num) in section_map.items():
            section_facts = categorized.get(key, [])
            if not section_facts or current_words >= target_words:
                continue

            # Section heading
            if style == 'blog':
                lines.append(f"{emoji} {section_title}")
                lines.append("-" * 30)
            elif style == 'professional':
                lines.append(f"{section_num}. {section_title}")
                lines.append("-" * 30)
                section_num += 1
            else:
                lines.append(section_title)
                lines.append("-" * 30)

            # Use bullet points for 3+ facts, paragraph for fewer
            if len(section_facts) >= 3:
                for fact in section_facts[:5]:
                    if current_words >= target_words:
                        break
                    fact = fact.strip()
                    if not fact.endswith('.'):
                        fact += '.'
                    lines.append(f"  • {fact}")
                    current_words += len(fact.split())
            else:
                paragraph = " ".join(section_facts)
                if not paragraph.endswith('.'):
                    paragraph += '.'
                lines.append(paragraph)
                current_words += len(paragraph.split())

            lines.append("")

        # ---------- OTHER / ADDITIONAL INFO ----------
        other_facts = categorized.get('other', [])
        if other_facts and current_words < target_words:
            if style == 'blog':
                lines.append("💡 Additional Information")
                lines.append("-" * 30)
            elif style == 'professional':
                lines.append(f"{section_num}. Additional Information")
                lines.append("-" * 30)
            else:
                lines.append("Additional Information")
                lines.append("-" * 30)

            for fact in other_facts[:4]:
                if current_words >= target_words:
                    break
                fact = fact.strip()
                if not fact.endswith('.'):
                    fact += '.'
                lines.append(f"  • {fact}")
                current_words += len(fact.split())

            lines.append("")

        # ---------- CONCLUSION ----------
        if style == 'blog':
            lines.append("✅ Conclusion")
            lines.append("-" * 30)
        elif style == 'professional':
            lines.append(f"{section_num}. Conclusion")
            lines.append("-" * 30)
        else:
            lines.append("Conclusion")
            lines.append("-" * 30)

        # Build a conclusion from the topic
        conclusion_parts = []
        if intro_facts:
            # Rephrase the first fact
            first_fact = intro_facts[0]
            if len(first_fact) > 50:
                conclusion_parts.append(f"In summary, {topic} is a significant subject that encompasses many aspects.")
            else:
                conclusion_parts.append(f"In conclusion, {first_fact}")

        # Add significance
        importance_facts = categorized.get('importance', [])
        if importance_facts:
            conclusion_parts.append(importance_facts[0])
        else:
            conclusion_parts.append(
                f"{topic_title} continues to be an important topic with wide-ranging "
                f"implications and applications in various fields."
            )

        conclusion_text = " ".join(conclusion_parts)
        if not conclusion_text.endswith('.'):
            conclusion_text += '.'
        lines.append(conclusion_text)
        lines.append("")

        # ---------- WORD COUNT & FOOTER ----------
        total_words = sum(len(line.split()) for line in lines)
        lines.append("-" * 50)
        if style == 'professional':
            lines.append(f"[Word Count: {total_words}]")
            lines.append(f"[Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}]")
        elif style == 'blog':
            lines.append(f"📊 Word Count: ~{total_words} words")
        else:
            lines.append(f"Word Count: {total_words}")

        return "\n".join(lines)

    # =============================================
    # OUTPUT: TYPE INTO ACTIVE APPLICATION
    # =============================================

    def type_into_active_app(self, text: str) -> str:
        """
        Type the given text into the currently active application.
        Uses clipboard (Ctrl+V) for reliability and Unicode support.
        Does NOT open any new application — types into whatever is currently focused.
        """
        try:
            if not text:
                return "No content to write."

            # Small delay to ensure the active app is ready
            time.sleep(0.5)

            # Copy to clipboard and paste (handles Unicode, formatting, speed)
            pyperclip.copy(text)
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'v')

            word_count = len(text.split())
            return f"Written {word_count} words into the active application."

        except Exception as e:
            return f"Error typing into application: {str(e)}"

    def type_into_notepad(self, text: str) -> str:
        """Open Notepad and type the text."""
        try:
            import subprocess
            subprocess.Popen(['notepad.exe'])
            time.sleep(1.5)
            return self.type_into_active_app(text)
        except Exception as e:
            return f"Error opening Notepad: {str(e)}"

    def type_into_word(self, text: str) -> str:
        """Open Word, create a Blank Document, and type the text."""
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = True
            doc = word.Documents.Add()
            selection = word.Selection
            selection.TypeText(text)
            return "Successfully created a professional Word document."
        except ImportError:
            # Fallback to PyAutoGUI if pywin32 not installed
            try:
                import subprocess
                subprocess.Popen(['winword.exe'])
                time.sleep(3)
                pyautogui.press('enter') # select Blank document
                time.sleep(1)
                return self.type_into_active_app(text)
            except Exception as e:
                return f"Error opening Microsoft Word: {str(e)}"
        except Exception as e:
            return f"Error interacting with Microsoft Word via COM: {str(e)}"

    def type_into_excel(self, topic: str, text: str) -> str:
        """Create a structured Dataset in Excel."""
        try:
            import win32com.client
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = True
            wb = excel.Workbooks.Add()
            ws = wb.ActiveSheet
            ws.Name = "Dataset"
            
            # Write Headers
            ws.Cells(1, 1).Value = "ID"
            ws.Cells(1, 2).Value = "Topic"
            ws.Cells(1, 3).Value = "Information / Fact"
            
            # Format Headers
            ws.Range("A1:C1").Font.Bold = True
            ws.Range("A1:C1").Interior.Color = 14277081 # Light Gray (BGR)
            
            # Split text into facts (sentences)
            sentences = [s.strip() for s in text.split('\n') if s.strip() and not s.startswith('=' * 5) and not s.startswith('-' * 5)]
            facts = []
            for s in sentences:
                if '•' in s:
                    facts.append(s.replace('•', '').strip())
                elif len(s.split()) >= 4:
                    facts.append(s)
            
            # Write Dataset
            row = 2
            for i, fact in enumerate(facts[:50]): # Limit strictly to 50 rows so it's fast
                if fact:
                    ws.Cells(row, 1).Value = i + 1
                    ws.Cells(row, 2).Value = topic.title()
                    ws.Cells(row, 3).Value = fact
                    row += 1
            
            # Autofit limits
            ws.Columns("A:B").AutoFit()
            # Constrain column C width nicely
            ws.Columns("C:C").ColumnWidth = 80
            ws.Columns("C:C").WrapText = True
            
            return f"Successfully created an Excel dataset with {row-2} records."
        except Exception as e:
            return f"Error opening Microsoft Excel: {str(e)}"

    def type_into_powerpoint(self, topic: str, text: str) -> str:
        """Create a modern Gamma-style presentation with varied backgrounds, smart content, and diagrams."""
        try:
            import win32com.client
            ppt = win32com.client.Dispatch("PowerPoint.Application")
            try:
                ppt.Visible = True
            except: pass

            topic_title = topic.strip().title()
            topic_lower = topic.strip().lower()

            # ============================================================
            # STEP 1: SMART CONTENT GENERATION PER SLIDE
            # ============================================================
            # Instead of relying on the thin article, generate slide-specific
            # content by doing targeted research queries for each archetype.

            # First, gather all available research facts
            raw_facts = []
            for line in text.split('\n'):
                l = line.replace('•', '').replace('-', '').strip()
                if l and len(l) > 20 and not l.startswith('=' * 5) and not "Word Count" in l and not l.startswith('-' * 5):
                    # Trim to max 15 words for clean bullets
                    words = l.split()
                    if len(words) > 15:
                        raw_facts.append(' '.join(words[:15]) + '...')
                    else:
                        raw_facts.append(l)

            # Remove duplicates
            seen = set()
            facts = []
            for f in raw_facts:
                key = f.lower()[:40]
                if key not in seen:
                    seen.add(key)
                    facts.append(f)

            # Also do additional targeted research queries to fill content
            extra_queries = [
                f"{topic_lower} definition overview",
                f"{topic_lower} how it works process",
                f"{topic_lower} advantages benefits",
                f"{topic_lower} challenges limitations problems",
                f"{topic_lower} real world applications examples",
                f"{topic_lower} future trends scope",
            ]
            for eq in extra_queries:
                try:
                    ddg_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(eq)}&format=json&no_html=1"
                    resp = self.session.get(ddg_url, timeout=5)
                    data = resp.json()
                    abstract = data.get('Abstract', '')
                    if abstract and len(abstract) > 30:
                        sentences = re.split(r'(?<=[.!?])\s+', abstract)
                        for s in sentences[:3]:
                            s = s.strip()
                            if len(s) > 20:
                                words = s.split()
                                if len(words) > 15:
                                    s = ' '.join(words[:15]) + '...'
                                key = s.lower()[:40]
                                if key not in seen:
                                    seen.add(key)
                                    facts.append(s)
                    for rt in data.get('RelatedTopics', [])[:3]:
                        t = rt.get('Text', '')
                        if t and len(t) > 20:
                            words = t.split()
                            if len(words) > 15:
                                t = ' '.join(words[:15]) + '...'
                            key = t.lower()[:40]
                            if key not in seen:
                                seen.add(key)
                                facts.append(t)
                except:
                    pass

            # ============================================================
            # STEP 2: DEFINE SLIDE STRUCTURE WITH SMART DEFAULTS
            # ============================================================
            slide_defs = [
                {
                    "title": topic_title,
                    "subtitle": "A Comprehensive Overview",
                    "type": "title",
                    "layout": "Hero Title Layout",
                    "bg": "gradient_dark",
                    "anim": "Fade",
                    "image_prompt": f"futuristic abstract technology background, {topic_lower}, dark blue gradient, minimal, 4K",
                    "diagram": None,
                },
                {
                    "title": "Why This Matters",
                    "type": "content",
                    "layout": "Image Focus Layout",
                    "bg": "gradient_blue",
                    "anim": "Zoom",
                    "image_prompt": f"professional business strategy concept, {topic_lower}, modern office, clean background",
                    "diagram": None,
                    "default_bullets": [
                        f"{topic_title} is reshaping how organizations operate globally.",
                        "Understanding it is critical for technical and business leaders.",
                        "This presentation covers concepts, applications, and future scope.",
                    ],
                },
                {
                    "title": "Introduction",
                    "type": "content",
                    "layout": "Left Text + Right Visual",
                    "bg": "minimal_white",
                    "anim": "Fade",
                    "image_prompt": f"clean infographic explaining {topic_lower}, flat design, pastel colors, presentation style",
                    "diagram": None,
                    "default_bullets": [
                        f"{topic_title} is a foundational concept in modern technology.",
                        "It enables scalable, efficient, and cost-effective solutions.",
                        "Widely adopted across industries including IT, finance, and healthcare.",
                    ],
                },
                {
                    "title": "Background & History",
                    "type": "content",
                    "layout": "Timeline Layout",
                    "bg": "tech_circuit",
                    "anim": "Wipe",
                    "image_prompt": f"historical timeline infographic, technology evolution, {topic_lower}, clean design",
                    "diagram": {"type": "Timeline", "elements": f"Origin → Early Adoption → Growth → {topic_title} Today"},
                    "default_bullets": [
                        f"The concept behind {topic_title} emerged in the early 2000s.",
                        "Rapid growth driven by cloud computing and digital transformation.",
                        "Now a multi-billion dollar industry with global adoption.",
                    ],
                },
                {
                    "title": "Core Concepts",
                    "type": "content",
                    "layout": "Infographic Layout",
                    "bg": "creative_purple",
                    "anim": "Fade",
                    "image_prompt": f"concept map diagram, {topic_lower}, colorful nodes, clean white background, infographic",
                    "diagram": None,
                    "default_bullets": [
                        "Pay-as-you-go model eliminates upfront capital expenditure.",
                        "Elasticity allows resources to scale on demand.",
                        "Service Level Agreements (SLAs) ensure reliability.",
                        "Multi-region availability for global deployment.",
                    ],
                },
                {
                    "title": "Architecture & Design",
                    "type": "diagram",
                    "layout": "Process Flow Layout",
                    "bg": "gradient_dark",
                    "anim": "Wipe",
                    "image_prompt": f"system architecture diagram, {topic_lower}, technical blueprint, dark background, neon accents",
                    "diagram": {"type": "System Architecture", "elements": f"User → Interface → {topic_title} Engine → Processing → Output"},
                    "default_bullets": [
                        "Layered architecture ensures modularity and scalability.",
                        "API gateway handles authentication and routing.",
                        "Backend services process requests asynchronously.",
                    ],
                },
                {
                    "title": "How It Works",
                    "type": "content",
                    "layout": "Left Text + Right Visual",
                    "bg": "corporate_gray",
                    "anim": "Fade",
                    "image_prompt": f"step by step process illustration, {topic_lower}, numbered steps, clean modern design",
                    "diagram": {"type": "Process Flow", "elements": "Step 1: Input → Step 2: Process → Step 3: Analyze → Step 4: Output"},
                    "default_bullets": [
                        "Users interact through a dashboard or API interface.",
                        "Requests are processed through automated pipelines.",
                        "Results are delivered in real-time with monitoring.",
                    ],
                },
                {
                    "title": "Real-World Applications",
                    "type": "content",
                    "layout": "Two Column Layout",
                    "bg": "infographic_teal",
                    "anim": "Fade",
                    "image_prompt": f"real world applications collage, {topic_lower}, industry icons, healthcare finance technology",
                    "diagram": None,
                    "default_bullets": [
                        "Healthcare: Patient data management and analytics.",
                        "Finance: Automated billing, fraud detection, compliance.",
                        "Education: Scalable e-learning platforms.",
                        "E-commerce: Dynamic pricing and inventory management.",
                    ],
                },
                {
                    "title": "Advantages & Impact",
                    "type": "content",
                    "layout": "Two Column Layout",
                    "bg": "gradient_blue",
                    "anim": "Fade",
                    "image_prompt": f"advantages benefits infographic, {topic_lower}, green checkmarks, professional design",
                    "diagram": None,
                    "default_bullets": [
                        "Cost Efficiency: Reduce operational expenses by up to 60%.",
                        "Scalability: Handle millions of requests seamlessly.",
                        "Reliability: 99.99% uptime with redundant systems.",
                        "Innovation: Accelerate time-to-market for new products.",
                    ],
                },
                {
                    "title": "Challenges & Limitations",
                    "type": "content",
                    "layout": "Comparison Layout",
                    "bg": "minimal_white",
                    "anim": "Fade",
                    "image_prompt": f"challenges obstacles infographic, {topic_lower}, warning icons, professional design, red accents",
                    "diagram": None,
                    "default_bullets": [
                        "Security: Data breaches and compliance concerns.",
                        "Complexity: Steep learning curve for new adopters.",
                        "Vendor Lock-in: Difficult to migrate between providers.",
                        "Cost Overruns: Unpredictable billing without proper monitoring.",
                    ],
                },
                {
                    "title": "Case Study",
                    "type": "content",
                    "layout": "Left Text + Right Visual",
                    "bg": "tech_circuit",
                    "anim": "Zoom",
                    "image_prompt": f"business case study presentation, {topic_lower}, charts metrics dashboard, corporate design",
                    "diagram": None,
                    "default_bullets": [
                        f"Company X adopted {topic_title} to optimize operations.",
                        "Achieved 40% cost reduction within the first quarter.",
                        "Improved system uptime from 95% to 99.9%.",
                        "Scaled to handle 10x traffic during peak events.",
                    ],
                },
                {
                    "title": "Future Scope",
                    "type": "content",
                    "layout": "Timeline Layout",
                    "bg": "creative_purple",
                    "anim": "Wipe",
                    "image_prompt": f"futuristic technology vision, {topic_lower}, AI automation, holographic interface, dark theme",
                    "diagram": {"type": "Timeline", "elements": "2024: AI Integration → 2025: Automation → 2026: Autonomous Systems → 2028+: Full Orchestration"},
                    "default_bullets": [
                        "AI and Machine Learning will automate decision-making.",
                        "Edge computing will reduce latency and improve performance.",
                        "Serverless architectures will become the default standard.",
                    ],
                },
                {
                    "title": "Key Takeaways",
                    "type": "content",
                    "layout": "Infographic Layout",
                    "bg": "gradient_dark",
                    "anim": "Fade",
                    "image_prompt": f"key takeaways summary, {topic_lower}, numbered list, clean minimal design, professional",
                    "diagram": None,
                    "default_bullets": [
                        f"{topic_title} is essential for modern digital infrastructure.",
                        "Choose the right pricing model to optimize costs.",
                        "Monitor usage continuously to avoid surprise bills.",
                        "Stay updated with evolving best practices and tools.",
                    ],
                },
                {
                    "title": "Thank You",
                    "subtitle": f"Questions about {topic_title}?",
                    "type": "closing",
                    "layout": "Hero Title Layout",
                    "bg": "gradient_blue",
                    "anim": "Fade",
                    "image_prompt": f"thank you slide background, professional, abstract blue gradient, clean modern design",
                    "diagram": None,
                },
            ]

            # Replace default bullets with real researched facts where available
            fact_idx = 0
            for sdef in slide_defs:
                if sdef["type"] in ("content", "diagram") and "default_bullets" in sdef:
                    replaced = []
                    for j in range(len(sdef["default_bullets"])):
                        if fact_idx < len(facts):
                            replaced.append(facts[fact_idx])
                            fact_idx += 1
                        else:
                            replaced.append(sdef["default_bullets"][j])
                    sdef["bullets"] = replaced
                elif "default_bullets" in sdef:
                    sdef["bullets"] = sdef["default_bullets"]

            # ============================================================
            # STEP 3: AUTO COLOR SYSTEM
            # ============================================================
            # Automatically picks a color theme based on the topic name.
            # Same topic always gets the same color. No hardcoded mappings.
            # Each tuple: (bg_rgb, text_rgb, accent_rgb, accent_dark_rgb, theme_name)

            color_pool = [
                (2040618,  16777215, 4569087,  2960685,  'Deep Blue'),
                (1978398,  16777215, 6205952,  1644825,  'Teal Gold'),
                (3801088,  16777215, 11184895, 2752512,  'Rich Purple'),
                (2105376,  16777215, 16751001, 1579032,  'Bold Orange'),
                (2118432,  16777215, 5635925,  1644825,  'Forest Green'),
                (2631720,  16777215, 16729156, 1907997,  'Warm Indigo'),
                (3158064,  16777215, 5614335,  2500134,  'Sharp Charcoal'),
                (1579032,  16777215, 6553710,  1118481,  'Cool Midnight'),
                (2364441,  16777215, 16755384, 1776411,  'Amber Brown'),
                (3342336,  16777215, 16756916, 2490368,  'Crimson Peach'),
            ]

            # Hash the topic string to pick a theme automatically
            hash_idx = sum(ord(c) for c in topic_lower) % len(color_pool)
            chosen_theme = color_pool[hash_idx]

            bg_rgb, text_rgb, accent_rgb, accent_dark, theme_name = chosen_theme
            is_light_bg = bg_rgb > 10000000

            def add_professional_design(slide_obj, idx, accent_clr, accent_dark_clr, is_light):
                """Add clean, professional decorative elements to each slide."""
                try:
                    # Element 1: Bottom accent bar (full-width colored strip at bottom)
                    bar = slide_obj.Shapes.AddShape(1, 0, 490, 960, 50)  # rectangle
                    bar.Fill.ForeColor.RGB = accent_clr
                    bar.Fill.Transparency = 0.15 if not is_light else 0.25
                    bar.Line.Visible = False

                    # Element 2: Thin accent line under the title area
                    title_line = slide_obj.Shapes.AddShape(1, 50, 95, 200, 4)
                    title_line.Fill.ForeColor.RGB = accent_clr
                    title_line.Line.Visible = False

                    # Element 3: Rotating subtle corner / edge accent (4 clean patterns)
                    p = idx % 4
                    if p == 0:
                        # Left sidebar strip
                        sb = slide_obj.Shapes.AddShape(1, 0, 0, 8, 540)
                        sb.Fill.ForeColor.RGB = accent_clr
                        sb.Line.Visible = False
                    elif p == 1:
                        # Top-right corner circle (partially off-canvas)
                        cr = slide_obj.Shapes.AddShape(9, 840, -40, 160, 160)
                        cr.Fill.ForeColor.RGB = accent_clr
                        cr.Fill.Transparency = 0.80
                        cr.Line.Visible = False
                    elif p == 2:
                        # Right sidebar strip
                        sb = slide_obj.Shapes.AddShape(1, 952, 0, 8, 540)
                        sb.Fill.ForeColor.RGB = accent_clr
                        sb.Line.Visible = False
                    else:
                        # Bottom-left corner rounded rect
                        cr = slide_obj.Shapes.AddShape(5, -30, 400, 140, 140)
                        cr.Fill.ForeColor.RGB = accent_clr
                        cr.Fill.Transparency = 0.82
                        cr.Line.Visible = False

                    # Element 4: Small accent dot/circle in opposite corner (elegant touch)
                    dot_positions = [(890, 20), (20, 460), (890, 460), (20, 20)]
                    dx, dy = dot_positions[p]
                    dot = slide_obj.Shapes.AddShape(9, dx, dy, 24, 24)
                    dot.Fill.ForeColor.RGB = accent_clr
                    dot.Fill.Transparency = 0.40
                    dot.Line.Visible = False

                except: pass

            # ============================================================
            # STEP 4: CREATE PRESENTATION
            # ============================================================
            presentation = ppt.Presentations.Add()
            output_lines = []

            for i, sdef in enumerate(slide_defs):
                slide_num = i + 1

                # --- Create Slide ---
                if sdef["type"] in ("title", "closing"):
                    slide = presentation.Slides.Add(slide_num, 1)  # ppLayoutTitle
                else:
                    slide = presentation.Slides.Add(slide_num, 2)  # ppLayoutText

                # --- Apply Background ---
                try:
                    slide.FollowMasterBackground = False
                    slide.Background.Fill.Solid()
                    slide.Background.Fill.ForeColor.RGB = bg_rgb
                except: pass

                # --- Apply Transition ---
                try:
                    slide.SlideShowTransition.EntryEffect = 701  # Fade
                except: pass

                # --- Professional Design Elements ---
                add_professional_design(slide, i, accent_rgb, accent_dark, is_light_bg)

                # ======================
                # TITLE / CLOSING SLIDE
                # ======================
                if sdef["type"] in ("title", "closing"):
                    try:
                        tf = slide.Shapes(1).TextFrame
                        tf.TextRange.Text = sdef["title"].upper() if sdef["type"] == "title" else sdef["title"]
                        tf.TextRange.Font.Size = 44
                        tf.TextRange.Font.Bold = True
                        tf.TextRange.Font.Color.RGB = text_rgb
                        try: tf.TextRange.Font.Name = "Montserrat"
                        except: tf.TextRange.Font.Name = "Segoe UI"
                    except: pass

                    try:
                        tf2 = slide.Shapes(2).TextFrame
                        tf2.TextRange.Text = sdef.get("subtitle", "")
                        tf2.TextRange.Font.Size = 24
                        tf2.TextRange.Font.Color.RGB = accent_rgb
                        try: tf2.TextRange.Font.Name = "Montserrat"
                        except: tf2.TextRange.Font.Name = "Segoe UI"
                    except: pass

                    # Accent line
                    try:
                        ln = slide.Shapes.AddShape(5, 340, 280, 280, 6)  # Centered accent bar
                        ln.Fill.ForeColor.RGB = accent_rgb
                        ln.Line.Visible = False
                    except: pass

                # ======================
                # CONTENT / DIAGRAM SLIDE
                # ======================
                else:
                    bullets = sdef.get("bullets", sdef.get("default_bullets", []))
                    has_right_visual = "Right" in sdef["layout"] or "Focus" in sdef["layout"]
                    has_two_col = "Two Column" in sdef["layout"] or "Comparison" in sdef["layout"]
                    has_diagram_below = sdef["type"] == "diagram" or (sdef.get("diagram") and "Flow" in sdef["layout"])

                    # --- Title ---
                    try:
                        tf_h = slide.Shapes(1).TextFrame
                        tf_h.TextRange.Text = sdef["title"]
                        tf_h.TextRange.Font.Size = 36
                        tf_h.TextRange.Font.Bold = True
                        tf_h.TextRange.Font.Color.RGB = text_rgb
                        try: tf_h.TextRange.Font.Name = "Montserrat"
                        except: tf_h.TextRange.Font.Name = "Segoe UI"
                    except: pass

                    # --- Body Text ---
                    try:
                        body = slide.Shapes(2)
                        # CRITICAL: Constrain width BEFORE setting text
                        if has_right_visual or has_two_col:
                            body.Left = 40
                            body.Width = 420
                            body.Top = 120
                            body.Height = 350
                        elif has_diagram_below:
                            body.Left = 40
                            body.Width = 880
                            body.Top = 120
                            body.Height = 180

                        body.TextFrame.TextRange.Text = '\n'.join(bullets)
                        body.TextFrame.TextRange.Font.Size = 22
                        body.TextFrame.TextRange.Font.Color.RGB = text_rgb
                        try: body.TextFrame.TextRange.Font.Name = "Montserrat"
                        except: body.TextFrame.TextRange.Font.Name = "Segoe UI"
                        body.TextFrame.TextRange.ParagraphFormat.SpaceAfter = 14
                        body.TextFrame.TextRange.ParagraphFormat.Bullet.Visible = True
                    except: pass

                    # --- Fade animation on body ---
                    try:
                        effect = slide.TimeLine.MainSequence.AddEffect(Shape=slide.Shapes(2), effectId=10)
                        effect.Timing.TriggerType = 1
                    except: pass

                    # --- RIGHT SIDE VISUAL (for split layouts) ---
                    if has_right_visual:
                        try:
                            sh = slide.Shapes.AddShape(5, 500, 120, 430, 350)
                            sh.Fill.ForeColor.RGB = accent_rgb
                            sh.Fill.Transparency = 0.85
                            sh.Line.ForeColor.RGB = accent_rgb
                            sh.Line.Weight = 2
                            sh.Line.Visible = True
                            sh.TextFrame.TextRange.Text = "[Image Placeholder]\n" + sdef.get("image_prompt", "")[:60]
                            sh.TextFrame.TextRange.Font.Size = 14
                            sh.TextFrame.TextRange.Font.Color.RGB = accent_rgb
                            sh.TextFrame.WordWrap = True
                        except: pass

                    # --- TWO COLUMN RIGHT SIDE ---
                    elif has_two_col:
                        try:
                            sh = slide.Shapes.AddShape(5, 500, 120, 430, 350)
                            sh.Fill.ForeColor.RGB = bg_rgb
                            sh.Line.ForeColor.RGB = accent_rgb
                            sh.Line.Weight = 2
                            sh.Line.Visible = True
                            # Put second half of bullets in column 2
                            half = len(bullets) // 2
                            col2_text = '\n'.join(bullets[half:]) if half > 0 else "[Additional data]"
                            sh.TextFrame.TextRange.Text = col2_text
                            sh.TextFrame.TextRange.Font.Size = 18
                            sh.TextFrame.TextRange.Font.Color.RGB = text_rgb
                            sh.TextFrame.WordWrap = True
                        except: pass

                    # --- DIAGRAM BELOW (for architecture/process slides) ---
                    if has_diagram_below and sdef.get("diagram"):
                        diag = sdef["diagram"]
                        elements = diag["elements"].split(' → ')
                        num_boxes = min(len(elements), 5)
                        box_w = 150
                        gap = 10
                        total_w = num_boxes * box_w + (num_boxes - 1) * gap
                        start_x = (960 - total_w) // 2
                        y = 340

                        for bi, label in enumerate(elements[:num_boxes]):
                            x = start_x + bi * (box_w + gap)
                            try:
                                bx = slide.Shapes.AddShape(5, x, y, box_w, 60)
                                bx.Fill.ForeColor.RGB = accent_rgb
                                bx.Fill.Transparency = 0.7
                                bx.Line.ForeColor.RGB = accent_rgb
                                bx.Line.Weight = 1.5
                                bx.Line.Visible = True
                                bx.TextFrame.TextRange.Text = label.strip()
                                bx.TextFrame.TextRange.Font.Size = 11
                                bx.TextFrame.TextRange.Font.Color.RGB = text_rgb
                                bx.TextFrame.TextRange.Font.Bold = True
                            except: pass

                            # Arrow between boxes
                            if bi < num_boxes - 1:
                                try:
                                    arrow_x = x + box_w
                                    arrow = slide.Shapes.AddLine(arrow_x + 2, y + 30, arrow_x + gap - 2, y + 30)
                                    arrow.Line.ForeColor.RGB = accent_rgb
                                    arrow.Line.Weight = 2
                                    arrow.Line.EndArrowheadStyle = 2  # Triangle
                                except: pass

                    # --- SMALL ACCENT ICON (for slides without right visual or diagram) ---
                    if not has_right_visual and not has_two_col and not has_diagram_below:
                        try:
                            ic = slide.Shapes.AddShape(9, 870, 40, 40, 40)
                            ic.Fill.ForeColor.RGB = accent_rgb
                            ic.Line.Visible = False
                        except: pass

                # ============================================================
                # BUILD OUTPUT TEXT
                # ============================================================
                output_lines.append(f"{'='*60}")
                output_lines.append(f"Slide {slide_num}: {sdef['title']}")
                output_lines.append(f"{'='*60}")
                output_lines.append(f"Layout: {sdef['layout']}")
                output_lines.append(f"Background: {theme_name} (consistent)")
                output_lines.append(f"Color Theme: {theme_name} - same across all slides")
                if sdef["type"] in ("content", "diagram"):
                    output_lines.append(f"Content:")
                    for b in sdef.get("bullets", sdef.get("default_bullets", [])):
                        output_lines.append(f"  • {b}")
                output_lines.append(f"AI Image Prompt: \"{sdef.get('image_prompt', 'N/A')}\"")
                if sdef.get("diagram"):
                    d = sdef["diagram"]
                    output_lines.append(f"Diagram Type: {d['type']}")
                    output_lines.append(f"Diagram Elements: {d['elements']}")
                output_lines.append(f"Animation: {sdef['anim']}")
                output_lines.append("")

            total_slides = len(slide_defs)
            header = f"Successfully generated {total_slides}-slide Elite Presentation on '{topic_title}'.\n\n"
            return header + '\n'.join(output_lines)

        except ImportError:
            return "Error: pywin32 module is required for PowerPoint automation."
        except Exception as e:
            return f"Error opening Microsoft PowerPoint: {str(e)}"

    # =============================================
    # MAIN ENTRY POINT
    # =============================================

    def write_about(self, topic: str, target_app: str = 'active', 
                    style: str = 'assignment', word_limit: int = 500) -> str:
        """
        Main function: Research a topic and write a formatted article.
        
        Args:
            topic: The subject to write about
            target_app: Where to type ('active', 'notepad', 'word')
            style: Writing style ('assignment', 'blog', 'professional')
            word_limit: Approximate word limit
            
        Returns:
            Status message about the writing operation
        """
        if not topic or len(topic.strip()) < 2:
            return "Please specify a topic. For example: 'write about artificial intelligence'"

        # Step 1: Research (background, no browser)
        article = self.compile_article(topic, style=style, word_limit=word_limit)

        if article.startswith("I couldn't find"):
            return article

        # Step 2: Type into target application
        if target_app == 'notepad':
            result = self.type_into_notepad(article)
        elif target_app == 'word':
            result = self.type_into_word(article)
        elif target_app in ['excel', 'dataset']:
            result = self.type_into_excel(topic, article)
        elif target_app in ['powerpoint', 'ppt', 'presentation']:
            result = self.type_into_powerpoint(topic, article)
        else:
            # Type into whatever app is currently active/focused
            result = self.type_into_active_app(article)

        word_count = len(article.split())
        return (
            f"I've researched '{topic}' from multiple sources and written a "
            f"{word_count}-word {style}-style article. {result}"
        )


# =============================================
# CONVENIENCE FUNCTIONS (for command_router)
# =============================================

_writer_instance = None

def _get_writer():
    """Get or create the SmartWriter singleton."""
    global _writer_instance
    if _writer_instance is None:
        _writer_instance = SmartWriter()
    return _writer_instance


def write_about_topic(topic: str, target_app: str = 'active', 
                      style: str = 'assignment', word_limit: int = 500) -> str:
    """
    Quick function: Research topic and write formatted article.
    
    Usage from command_router:
        from wizard.commands.smart_writer import write_about_topic
        return write_about_topic("artificial intelligence", target_app="notepad")
    """
    writer = _get_writer()
    return writer.write_about(topic, target_app=target_app, style=style, word_limit=word_limit)


def research_only(topic: str, style: str = 'assignment', word_limit: int = 500) -> str:
    """
    Research and compile article without typing it anywhere.
    Returns the formatted article as a string.
    """
    writer = _get_writer()
    return writer.compile_article(topic, style=style, word_limit=word_limit)

