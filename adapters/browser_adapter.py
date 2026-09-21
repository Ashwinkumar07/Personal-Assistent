"""
Browser & Web Search Adapter:
Free, local web searching and webpage text extraction.
"""

import urllib.parse
import urllib.request
import json
from typing import List, Dict, Any, Optional
from core.logger import logger, log_latency
from core.safety_gate import RiskLevel
from tools.base import BaseTool
from pydantic import BaseModel, Field

class SearchWebArgs(BaseModel):
    query: str = Field(..., description="Search query string.")
    max_results: int = Field(default=5, description="Number of results to retrieve.")

class BrowserAdapter(BaseTool):
    name = "search_web"
    description = "Search the web for news, information, or answers without cloud account."
    risk_level = RiskLevel.READ
    args_schema = SearchWebArgs

    def run(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        with log_latency("BrowserAdapter.search_web", query):
            try:
                # Direct free search endpoint via DuckDuckGo API/HTML
                encoded_q = urllib.parse.quote(query)
                url = f"https://api.duckduckgo.com/?q={encoded_q}&format=json&no_html=1&skip_disambig=1"
                
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())

                results = []
                if data.get("AbstractText"):
                    results.append({"title": data.get("Heading", "Summary"), "snippet": data.get("AbstractText"), "url": data.get("AbstractURL", "")})
                
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({"title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "), "snippet": topic.get("Text"), "url": topic.get("FirstURL", "")})

                if not results:
                    results.append({"title": "Search Query", "snippet": f"Web query conducted for: '{query}'.", "url": url})
                return results

            except Exception as e:
                logger.warning(f"[BROWSER ADAPTER] Web search error: {e}")
                return [{"title": "Search Failed", "snippet": f"Could not reach search service: {e}", "url": ""}]
