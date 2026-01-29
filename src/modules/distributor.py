import logging
# import tweepy # Lazy import
from datetime import datetime
from typing import Optional
from ..config import config
from ..core.types import TweetContent
from ..core.rate_limiter import rate_limiter

logger = logging.getLogger("Distributor")

class Distributor:
    def __init__(self, account_config: 'AccountConfig', rate_limiter: 'RateLimiter'):
        self.account_config = account_config
        self.rate_limiter = rate_limiter
        self.api = None
        self._init_api()

    def _init_api(self):
        creds = self.account_config.credentials
        if creds.api_key:
            try:
                import tweepy
                auth = tweepy.OAuthHandler(creds.api_key, creds.api_secret)
                auth.set_access_token(creds.access_token, creds.access_secret)
                
                # Proxy Support
                proxy = self.account_config.proxy_url
                self.api = tweepy.API(
                    auth, 
                    proxy=proxy if proxy else None
                )
            except Exception as e:
                logger.error(f"[{self.account_config.id}] Distributor Auth Failed: {e}")
        else:
            logger.info(f"[{self.account_config.id}] Distributor running in Mock Mode.")

    def post_tweet(self, content: TweetContent) -> bool:
        """
        Executes the posting logic.
        """
        # Final safety check from Rate Limiter
        if not self.rate_limiter.can_tweet():
            logger.warning(f"[{self.account_config.id}] Distributor blocked tweet: Rate Limit.")
            return False

        if config.LAUNCH_MODE == "SHADOW":
            logger.info(f"[{self.account_config.id}] [SHADOW] Would post tweet: {content.text}")
            self.rate_limiter.record_tweet()
            return True
            
        if config.LAUNCH_MODE == "APPROVAL":
            # Save to disk/notify
            logger.info(f"[{self.account_config.id}] [APPROVAL] Tweet queued: {content.text}")
            return True

        # Mode = AUTONOMOUS
        try:
            if self.api:
                self.api.update_status(content.text)
                logger.info(f"[{self.account_config.id}] Posted to X: {content.text[:30]}...")
            else:
                logger.info(f"[{self.account_config.id}] [MOCK-AUTO] Posted: {content.text}")
            
            self.rate_limiter.record_tweet()
            return True
        except Exception as e:
            logger.error(f"[{self.account_config.id}] Failed to post to X: {e}")
            return False

    def post_reply(self, signal_id: str, text: str) -> bool:
        if not self.rate_limiter.can_reply():
            return False

        if config.LAUNCH_MODE == "AUTONOMOUS" and self.api:
            try:
                self.api.update_status(status=text, in_reply_to_status_id=signal_id, auto_populate_reply_metadata=True)
                self.rate_limiter.record_reply()
                return True
            except Exception as e:
                logger.error(f"[{self.account_config.id}] Reply failed: {e}")
                return False
        
        logger.info(f"[{self.account_config.id}] [{config.LAUNCH_MODE}] Would reply to {signal_id}: {text}")
        self.rate_limiter.record_reply()
        return True
