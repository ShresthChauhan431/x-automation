import logging
from ..modules.hook_engine import HookEngine
from ..config import config

logger = logging.getLogger("Strategist")

class Strategist:
    def __init__(self, hook_engine: HookEngine):
        self.hook_engine = hook_engine

    def run_daily_stratagem(self):
        """
        Executed once every 24h.
        """
        logger.info("Executing Daily Strategy Mutation...")
        
        # 1. Evolve Hooks
        self.hook_engine.evolve()
        
        # 2. Mutate Thresholds (with safeguards)
        # Example: If we are hitting rate limits often, increase intervals
        # This is a placeholder for the logic described in FR-8
        
        # Safeguard check
        if config.MAX_DAILY_TWEETS > 50:
             logger.warning("MAX_DAILY_TWEETS too high. Resetting to 20.")
             config.MAX_DAILY_TWEETS = 20
             
        logger.info("Strategy Mutation Complete.")
