"""
Research Assistant Module for Wizard Voice Assistant
Handles background information gathering without opening browser tabs.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, List, Dict
from ..utils.logger import WizardLogger
from ..utils.config_manager import ConfigManager

class ResearchAssistant:
    def __init__(self, config_manager: ConfigManager, logger: WizardLogger):
        self.config = config_manager
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def search_and_summarize(self, query: str) -> str:
        """Search Google and summarize the top result snippet or page."""
        try:
            self.logger.info(f"Researching: {query}")
            
            # Step 1: Search Wikipedia first (best for direct entities/topics)
            wiki_answer = self._search_wikipedia(query)
            if wiki_answer:
                return self._clean_text(f"According to Wikipedia: {wiki_answer}")
            
            # Step 2: Search Google for snippets
            google_answer = self._search_google_snippets(query)
            if google_answer:
                return self._clean_text(google_answer)

            # Step 3: Search DuckDuckGo (Great backup for direct answers)
            ddg_answer = self._search_duckduckgo(query)
            if ddg_answer:
                return self._clean_text(ddg_answer)

            # Step 4: Query relaxation - try searching for a simpler version if specific one fails
            # e.g. "ajit pawar death" -> "ajit pawar"
            words = query.split()
            if len(words) > 2:
                relaxed_query = " ".join(words[:2])
                self.logger.info(f"Specific search failed. Relaxing query to: {relaxed_query}")
                relaxed_answer = self._search_google_snippets(relaxed_query) or self._search_wikipedia(relaxed_query)
                if relaxed_answer:
                    return self._clean_text(f"I couldn't find specific details for your full request, but about {relaxed_query}: {relaxed_answer}")

            return f"I found some information about {query}, but I couldn't summarize it easily. Would you like me to open the full results in your browser?"

        except Exception as e:
            self.logger.error(f"Error during research: {e}")
            return "I encountered an error while researching that topic."

    def _search_wikipedia(self, query: str) -> Optional[str]:
        """Fetch summary from Wikipedia."""
        try:
            # Search for the page
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=1&namespace=0&format=json"
            response = self.session.get(search_url, timeout=5)
            data = response.json()
            
            if not data[1]:
                return None
            
            title = data[1][0]
            
            # Get the summary
            summary_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={title}&format=json"
            response = self.session.get(summary_url, timeout=5)
            pages = response.json()['query']['pages']
            
            for page_id in pages:
                extract = pages[page_id].get('extract', '')
                if extract:
                    # Return the first two sentences
                    sentences = extract.split('. ')
                    if len(sentences) > 1:
                        summary = sentences[0] + '. ' + sentences[1].split('.')[0] + '.'
                    else:
                        summary = sentences[0]
                    
                    if len(summary) > 400:
                        summary = summary[:397] + "..."
                    return summary
            
            return None
        except:
            return None

    def _search_google_snippets(self, query: str) -> Optional[str]:
        """Scrape Google search results for snippets/featured snippets."""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&hl=en"
            response = self.session.get(search_url, timeout=5)
            
            # Check for cookie consent redirect
            if "consent.google.com" in response.url:
                # Try one more time with a stay-on-google parameter
                response = self.session.get(search_url + "&fg=1", timeout=5)
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Try to find a single high-quality snippet (using various selectors)
            selectors = [
                'div.hgKElc', 'span.hgKElc', 'div.VwiC3b', 'div.L89Z0d', 'div.ayS6S',
                'div.gsrt.GBS_v', 'div.kno-rdesc span', 'div.MUwY0b', 'div.yNb9V',
                'div.BNeawe', 'span.XL7A9b', 'div.kbS69', 'div.wM6W7d'
            ]
            
            # Use snippets found to build a response
            found_texts = []
            for selector in selectors:
                elements = soup.select(selector)
                for el in elements:
                    text = el.get_text().strip()
                    if len(text) > 40 and text not in found_texts:
                        found_texts.append(text)
            
            if found_texts:
                # Prioritize the longest/most complete looking answer
                best_answer = max(found_texts, key=len)
                if len(best_answer) > 50:
                    return self._clean_text(best_answer[:500] + ("..." if len(best_answer) > 500 else ""))

            # 2. Fallback: Parse paragraphs from result descriptions
            descriptions = soup.select('div.VwiC3b, div.BNeawe, div.wM6W7d, div.yNb9V')
            if descriptions:
                combined = " ".join([d.get_text().strip() for d in descriptions[:3] if len(d.get_text().strip()) > 30])
                if len(combined) > 60:
                    return self._clean_text(combined[:600] + ("..." if len(combined) > 600 else ""))

            # 3. Last resort: Scrape text from result blocks 'div.g' directly
            blocks = soup.select('div.g')
            if blocks:
                block_text = " ".join([b.get_text(separator=' ').strip() for b in blocks[:2]])
                if len(block_text) > 100:
                    # Clean up multiple spaces and returns
                    clean_block = re.sub(r'\s+', ' ', block_text)
                    return self._clean_text(clean_block[:550] + "...")

            return None
        except:
            return None

    def _search_duckduckgo(self, query: str) -> Optional[str]:
        """Fetch result from DuckDuckGo Instant Answer API."""
        try:
            url = f"https://api.duckduckgo.com/?q={query.replace(' ', '+')}&format=json"
            response = self.session.get(url, timeout=5)
            data = response.json()
            
            # Abstract is the direct answer
            if data.get('AbstractText'):
                return data['AbstractText']
            
            # If no abstract, try RelatedTopics
            if data.get('RelatedTopics') and len(data['RelatedTopics']) > 0:
                first_topic = data['RelatedTopics'][0]
                if 'Text' in first_topic:
                    return first_topic['Text']
            
            return None
        except:
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for output."""
        if not text:
            return ""
        # Remove multiple newlines and extra spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def answer_question(self, question: str) -> str:
        """Specifically handle question patterns."""
        result = self.search_and_summarize(question)
        return self._clean_text(result)
