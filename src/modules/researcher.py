import logging
# import google.generativeai as genai # Lazy
from typing import Optional
from ..config import config
from ..core.types import Signal, ResearchOutput

logger = logging.getLogger("Researcher")

class Researcher:
    def __init__(self):
        self.model = None
        if config.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                logger.error(f"Gemini Init Error: {e}")

    def research_signal(self, signal: Signal) -> Optional[ResearchOutput]:
        """
        Deep dives into a signal.
        Conceptually equivalent to loading a source into NotebookLM and asking for a structural analysis.
        """
        if not self.model:
            return self._mock_research(signal)

        # In a real implementation with URL support, we'd fetch the webpage content here.
        # context = self.fetch_url(signal.url)
        context = signal.content 

        prompt = f"""
        Analyze this source content regarding: "{context}"
        
        Task: Perform a rigorous structural analysis.
        
        Extract:
        1. The Core Claim (What is being asserted?)
        2. Non-obvious Implications (2-3 items)
        3. Attack Vectors (How could this be wrong/attacked? 2-3 items)
        
        Output Format (STRICT JSON):
        {{
            "core_claim": "...",
            "implications": ["...", "..."],
            "attack_vectors": ["...", "..."],
            "summary": "..."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Simple JSON parsing (in prod, use strict schema mode or repairjson)
            import json
            text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(text)
            
            return ResearchOutput(
                source_signal_id=signal.id,
                core_claim=data.get("core_claim", ""),
                implications=data.get("implications", []),
                attack_vectors=data.get("attack_vectors", []),
                raw_source_summary=data.get("summary", "")
            )

        except Exception as e:
            logger.error(f"Research Failed: {e}")
            return None

    def _mock_research(self, signal: Signal) -> ResearchOutput:
        return ResearchOutput(
            source_signal_id=signal.id,
            core_claim="AI Agents are the future",
            implications=["Manual coding will decrease", "System architecture value increases"],
            attack_vectors=["Reliability is low", "Looping issues"],
            raw_source_summary=signal.content
        )
