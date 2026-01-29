import sys
import os
import shutil
# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.rate_limiter import rate_limiter
from src.config import config

def test_rate_limiter():
    print("Testing Rate Limiter...")
    
    # 1. Reset state for testing
    rate_limiter.state["monthly_posts_count"] = 0
    rate_limiter.state["monthly_reads_count"] = 0
    rate_limiter._save_state()
    
    # 2. Test Posts Limit
    print(f"Max Monthly Posts: {config.MAX_MONTHLY_POSTS}")
    
    # Set limit to something small for testing in memory temporarily
    original_limit = config.MAX_MONTHLY_POSTS
    config.MAX_MONTHLY_POSTS = 5
    config.MIN_TWEET_INTERVAL_SECONDS = 0 # Disable cooldown for test
    
    for i in range(5):
        if rate_limiter.can_tweet():
            rate_limiter.record_tweet()
            print(f"Tweet {i+1} recorded.")
        else:
            print(f"Tweet {i+1} blocked unexpectedly.")

    if not rate_limiter.can_tweet():
        print("Tweet 6 correctly blocked.")
    else:
        print("Tweet 6 INCORRECTLY allowed.")
        
    # 3. Test Reads Limit
    print(f"Max Monthly Reads: {config.MAX_MONTHLY_READS}")
    config.MAX_MONTHLY_READS = 2
    
    rate_limiter.record_read()
    print("Read 1 recorded.")
    rate_limiter.record_read()
    print("Read 2 recorded.")
    
    if not rate_limiter.can_read():
        print("Read 3 correctly blocked.")
    else:
        print("Read 3 INCORRECTLY allowed.")

    # 4. Verify Persistence
    stats = rate_limiter.state
    print(f"State in memory: {stats}")
    
    # Reload from disk
    new_limiter = rate_limiter.__class__() # Create new instance to load from disk
    print(f"State from disk: {new_limiter.state}")
    
    assert new_limiter.state["monthly_posts_count"] == 5
    assert new_limiter.state["monthly_reads_count"] == 2
    
    print("Persistence verification passed.")
    
    # Cleanup
    config.MAX_MONTHLY_POSTS = original_limit

if __name__ == "__main__":
    test_rate_limiter()
