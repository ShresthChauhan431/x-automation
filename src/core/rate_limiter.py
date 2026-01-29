import json
import os
from datetime import datetime
from typing import Dict, Optional
from ..config import config

class RateLimitExceeded(Exception):
    pass

class RateLimiter:
    """
    Tracks usage against system-defined limits using a local JSON file for persistence.
    Now supports Multi-Tenancy via `account_id`.
    """
    def __init__(self, account_id: str):
        self.account_id = account_id
        # Use account-specific state file
        self.state_file = os.path.join(config.DATA_DIR, f"rate_limit_{account_id}.json")
        self.state = {
            "daily_tweets_count": 0,
            "daily_replies_count": 0,
            "monthly_posts_count": 0, # Tweets + Replies
            "monthly_reads_count": 0,
            "last_reset_day": datetime.now().strftime("%Y-%m-%d"),
            "last_reset_month": datetime.now().strftime("%Y-%m"),
            "last_tweet_time": None,
            "last_reply_time": None
        }
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Merge with default structure to handle schema evolution
                    self.state.update(data)
                    self._convert_times()
            except Exception as e:
                print(f"[{self.account_id}] Warning: Failed to load rate limit state: {e}")

    def _convert_times(self):
        """Convert stored string timestamps back to datetime objects if needed."""
        # JSON validation or simple key checking could go here
        pass

    def _save_state(self):
        try:
            # Create data dir if not exists
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"[{self.account_id}] Error saving rate limit state: {e}")

    def _check_resets(self):
        now = datetime.now()
        current_day = now.strftime("%Y-%m-%d")
        current_month = now.strftime("%Y-%m")

        state_changed = False
        
        # Daily Reset
        if current_day != self.state["last_reset_day"]:
            self.state["daily_tweets_count"] = 0
            self.state["daily_replies_count"] = 0
            self.state["last_reset_day"] = current_day
            state_changed = True

        # Monthly Reset
        if current_month != self.state["last_reset_month"]:
            self.state["monthly_posts_count"] = 0
            self.state["monthly_reads_count"] = 0
            self.state["last_reset_month"] = current_month
            state_changed = True
            
        if state_changed:
            self._save_state()

    def can_tweet(self) -> bool:
        self._check_resets()
        
        # 1. Total Monthly Limit
        if self.state["monthly_posts_count"] >= config.MAX_MONTHLY_POSTS:
            return False

        # 2. Daily Limit
        if self.state["daily_tweets_count"] >= config.MAX_DAILY_TWEETS:
            return False
            
        # 3. Cooldown
        if self.state["last_tweet_time"]:
            last_time = datetime.fromtimestamp(self.state["last_tweet_time"])
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < config.MIN_TWEET_INTERVAL_SECONDS:
                return False
                
        return True

    def record_tweet(self):
        self.state["daily_tweets_count"] += 1
        self.state["monthly_posts_count"] += 1
        self.state["last_tweet_time"] = datetime.now().timestamp()
        self._save_state()

    def can_reply(self) -> bool:
        self._check_resets()
        
        # 1. Total Monthly Limit (Shared with tweets)
        if self.state["monthly_posts_count"] >= config.MAX_MONTHLY_POSTS:
            return False
            
        # 2. Daily Limit
        if self.state["daily_replies_count"] >= config.MAX_DAILY_REPLIES:
            return False
            
        return True

    def record_reply(self):
        self.state["daily_replies_count"] += 1
        self.state["monthly_posts_count"] += 1
        self.state["last_reply_time"] = datetime.now().timestamp()
        self._save_state()

    def can_read(self) -> bool:
        self._check_resets()
        if self.state["monthly_reads_count"] >= config.MAX_MONTHLY_READS:
            return False
        return True

    def record_read(self, count=1):
        self.state["monthly_reads_count"] += count
        self._save_state()
