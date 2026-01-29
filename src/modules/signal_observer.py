import logging
# import tweepy # Lazy import
import time
import random 
from datetime import datetime, timezone
from typing import List
from ..config import config
from ..core.types import Signal, SignalType
from ..memory.store import store
from ..core.rate_limiter import rate_limiter

logger = logging.getLogger("SignalObserver")

class SignalObserver:
    def __init__(self, account_config: 'AccountConfig', rate_limiter: 'RateLimiter'):
        self.account_config = account_config
        self.rate_limiter = rate_limiter
        self.auth = None
        self.api = None
        self._init_api()

    def _init_api(self):
        creds = self.account_config.credentials
        if creds.api_key:
            try:
                import tweepy
                self.auth = tweepy.OAuthHandler(creds.api_key, creds.api_secret)
                self.auth.set_access_token(creds.access_token, creds.access_secret)
                
                proxy = self.account_config.proxy_url
                self.api = tweepy.API(
                    self.auth, 
                    proxy=proxy if proxy else None
                )
            except Exception as e:
                logger.error(f"[{self.account_config.id}] Failed to auth with X: {e}")
        else:
            logger.warning(f"[{self.account_config.id}] No X API Key found. Running in simulation mode for Observer.")

    def run_observation_cycle(self):
        """Main entry point for the observation loop."""
        logger.info(f"[{self.account_config.id}] Starting observation cycle...")
        raw_tweets = self._fetch_timeline()
        processed_signals = self._process_tweets(raw_tweets)
        
        count = 0
        for signal in processed_signals:
            if signal.urgency_score > 0.7 or signal.novelty_score > 0.7:
                store.add_signal(signal)
                count += 1
        
        logger.info(f"[{self.account_config.id}] Observation cycle complete. Stored {count} high-value signals.")

    def _fetch_timeline(self) -> List[Dict]:
        """Fetches tweets from home timeline or lists."""
        if not self.api:
            return self._mock_tweets()
            
        # Check Rate Limit for Reads
        if not self.rate_limiter.can_read():
            logger.warning(f"[{self.account_config.id}] SignalObserver blocked: Monthly Read Limit Exceeded.")
            return []

        try:
            # Real API call
            tweets = self.api.home_timeline(count=20, tweet_mode="extended")
            # Record 1 read (1 call)
            self.rate_limiter.record_read()
            return [t._json for t in tweets]
        except Exception as e:
            logger.error(f"Error fetching timeline: {e}")
            return []

    def _mock_tweets(self) -> List[Dict]:
        """Generates fake tweets for simulation."""
        return [
            {
                "id_str": str(random.randint(100000, 999999)),
                "full_text": f"This is a simulated tweet about AI agent number {random.randint(1, 100)}.",
                "user": {
                    "id_str": "12345",
                    "screen_name": "simulated_user",
                    "followers_count": random.randint(100, 50000),
                    "verified": random.choice([True, False])
                },
                "created_at": datetime.now(timezone.utc).strftime("%a %b %d %H:%M:%S +0000 %Y")
            }
            for _ in range(5)
        ]

    def _process_tweets(self, raw_tweets: List[Dict]) -> List[Signal]:
        signals = []
        for t in raw_tweets:
            # 1. Compute Authority Score
            user = t.get("user", {})
            followers = user.get("followers_count", 0)
            verified = user.get("verified", False)
            
            # Log-scale-ish normalization
            auth_score = min(followers / 10000.0, 1.0)
            if verified:
                auth_score = min(auth_score + 0.2, 1.0)

            # 2. Compute Urgency Score (Time decay function)
            created_at = datetime.strptime(t["created_at"], "%a %b %d %H:%M:%S +0000 %Y")
            # urgency = 1.0 / (minutes_old + 1)
            # For now, simplistic random + freshness
            urgency_score = random.uniform(0.1, 0.9) 

            # 3. Compute Novelty Score
            # TODO: Use embedding distance vs store.insight_collection
            novelty_score = random.uniform(0.1, 1.0) 

            sig = Signal(
                id=t["id_str"],
                content=t.get("full_text", "") or t.get("text", ""),
                author_id=user.get("id_str", "unknown"),
                created_at=created_at,
                urgency_score=urgency_score,
                novelty_score=novelty_score,
                authority_score=auth_score,
                metadata={"username": user.get("screen_name")}
            )
            signals.append(sig)
        return signals
