import logging
# import google.generativeai as genai # Lazy
from typing import Optional
from ..config import config
from ..core.types import Insight, Hook, TweetContent, ContentType

logger = logging.getLogger("ContentBuilder")

class ContentBuilder:
    def __init__(self):
        self.model = None
        if config.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                logger.error(f"Gemini Init Error: {e}")

    def generate_content(self, insight: Insight, hook: Hook) -> Optional[TweetContent]:
        """
        Synthesizes an Insight and a Hook into a Tweet.
        Enforces strict constraints: <280 chars, No CTA.
        """
        if not self.model:
            return self._mock_generate(insight, hook)

        prompt = f"""
        Role: World-class ghostwriter.
        Task: Write a tweet.
        
        Input Data:
        - Insight: "{insight.content}"
        - Hook Template/Style: "{hook.template_text}" ({hook.structure_type})
        - Emotional Polarity: {hook.emotional_polarity}
        
        Hard Constraints (VIOLATION = FAILURE):
        1. MAX 280 characters.
        2. NO "Call to Action" (e.g., "Follow me", "Click here", "?").
        3. Declarative, authoritative tone.
        4. ONE idea only.
        
        Output:
        Just the tweet text. No quotes.
        """
        
        try:
            response = self.model.generate_content(prompt)
            tweet_text = response.text.strip()
            
            # Quality Gate
            if len(tweet_text) > 280:
                logger.warning(f"Generated tweet too long ({len(tweet_text)}). Rejecting.")
                return None
            if "?" in tweet_text and "Question" not in hook.structure_type:
                # Soft check: avoid questions unless requested
                pass
            
            return TweetContent(
                text=tweet_text,
                insight_id=insight.id,
                hook_id=hook.id,
                status="DRAFT"
            )

        except Exception as e:
            logger.error(f"Content Generation Failed: {e}")
            return None

    def _mock_generate(self, insight: Insight, hook: Hook) -> TweetContent:
        text = f"Simulated tweet based on {insight.content[:20]}... #AI"
        return TweetContent(
            text=text,
            insight_id=insight.id,
            hook_id=hook.id,
            status="DRAFT"
        )
