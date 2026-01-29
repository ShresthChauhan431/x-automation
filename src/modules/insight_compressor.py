import logging
# import google.generativeai as genai # Lazy
from typing import Optional
from datetime import datetime
from ..config import config
from ..core.types import Signal, Insight
from ..memory.store import store

logger = logging.getLogger("InsightCompressor")

class InsightCompressor:
    def __init__(self):
        self.client = None
        self._init_llm()

    def _init_llm(self):
        if config.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-pro')
                self.client = True
            except Exception as e:
                logger.error(f"Failed to init Gemini: {e}")
        else:
            logger.warning("No Gemini API Key. Insight Compressor running in mock mode.")

    def process_signal(self, signal: Signal) -> Optional[Insight]:
        """
        Compresses a signal into an Insight. Returns None if rejected.
        """
        if not self.client:
            return self._mock_compress(signal)

        prompt = f"""
        Analyze this social media signal:
        "{signal.content}"
        
        Your Goal: Compress this into a single, decisive insight.
        
        Rules:
        1. REJECT if it is Common Knowledge (e.g., "Sky is blue", "AI is popular").
        2. REJECT if it is purely explanatory without behavioral implication.
        3. ACCEPT only if it offers a non-obvious perspective or specific action.
        4. Max length: 40 tokens.
        
        Output Format:
        If Rejected: "REJECT: [Reason]"
        If Accepted: "INSIGHT: [The Insight Text]"
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            if text.startswith("REJECT"):
                logger.info(f"Signal {signal.id} rejected: {text}")
                return None
            
            if text.startswith("INSIGHT:"):
                insight_text = text.replace("INSIGHT:", "").strip()
                insight = Insight(
                    content=insight_text,
                    original_research_id=signal.id,
                    created_at=datetime.now()
                )
                store.add_insight(insight)
                return insight
                
            return None
            
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return None

    def _mock_compress(self, signal: Signal) -> Optional[Insight]:
        """Mock logic for testing without API."""
        if "AI" in signal.content:
            insight = Insight(
                content=f"AI agents are evolving rapidly: {signal.content[:20]}...",
                original_research_id=signal.id
            )
            store.add_insight(insight)
            return insight
        return None
