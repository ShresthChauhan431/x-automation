import time
import logging
import random
from datetime import datetime, timedelta
from ..config import config, AccountConfig
from ..core.rate_limiter import RateLimiter
from ..core.types import TweetContent
from ..memory.store import store

# Modules
from ..modules.signal_observer import SignalObserver
from ..modules.researcher import Researcher
from ..modules.insight_compressor import InsightCompressor
from ..modules.hook_engine import HookEngine
from ..modules.content_builder import ContentBuilder
from ..modules.distributor import Distributor
from ..modules.outcome_measurer import OutcomeMeasurer
from ..modules.strategist import Strategist

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AntigravityEngine")

class AntigravityEngine:
    def __init__(self, account_config: AccountConfig):
        self.account_config = account_config
        self.running = False
        self.logger = logging.getLogger(f"Engine-{self.account_config.id}")
        self.logger.info(f"Initializing Engine for {self.account_config.id} in {config.LAUNCH_MODE} mode.")
        
        # Local Rate Limiter
        self.rate_limiter = RateLimiter(self.account_config.id)
        
        # Initialize Components
        self.observer = SignalObserver(self.account_config, self.rate_limiter)
        self.researcher = Researcher() # Stateless enough for now
        self.compressor = InsightCompressor() # Stateless
        self.hook_engine = HookEngine() # Shared hooks for now, but could be per-niche
        self.content_builder = ContentBuilder() # Stateless
        self.distributor = Distributor(self.account_config, self.rate_limiter)
        self.measurer = OutcomeMeasurer(self.distributor)
        self.strategist = Strategist(self.hook_engine)
        
        # State
        self.last_strategy_run = datetime.now() - timedelta(days=1)
        
        # Seeding
        self.hook_engine.initialize_genome_if_empty()

    def run(self):
        """Main execution loop."""
        self.running = True
        self.logger.info("Engine started.")
        
        while self.running:
            try:
                self.tick()
                # Fast loop for simulation/debug, slow for prod
                time.sleep(10) 
            except KeyboardInterrupt:
                self.logger.info("Stopping engine...")
                self.running = False
            except Exception as e:
                self.logger.error(f"Engine Loop Error: {e}", exc_info=True)
                time.sleep(60)

    def tick(self):
        """Single heartbeat of the system."""
        
        # 1. Strategy Mutation (Once Daily)
        if (datetime.now() - self.last_strategy_run).total_seconds() > 86400:
            self.strategist.run_daily_stratagem()
            self.last_strategy_run = datetime.now()

        # 2. Measurement
        self.measurer.run_measurement_cycle()

        # 3. Observation (15 min interval usually, but doing per tick for simplicity of 'agentness')
        # We should use a timer here in real life
        if random.random() < 0.3: # 30% chance per tick to observe
            self.observer.run_observation_cycle()

        # 4. Insight Generation
        # Get pending signals? 
        signals = store.get_high_urgency_signals()
        for signal in signals:
            # Check if we already have an insight for this signal? To prevent loops.
            # TODO: Add 'processed' flag to signals.
            # Assuming we pick one and process.
            
            research = self.researcher.research_signal(signal)
            if research:
                insight = self.compressor.process_signal(signal)
                if insight:
                    self.logger.info(f"New Insight: {insight.content[:50]}...")

        # 5. Content Construction & Distribution
        # Only build if we can tweet
        if self.rate_limiter.can_tweet():
            # Get an unused insight
            # Mock: just pick one from vector store or using store method
            # For now, let's assume we grabbed one
            # hook = self.hook_engine.select_hooks(1)[0]
            # tweet = self.content_builder.generate_content(insight, hook)
            
            # Since we don't have robust 'Pending Insights' query yet, I'll simulate
            # a "Decision Logic" for the MVP Verification
            self.logger.debug("Checking for content opportunities...")
            pass # Real logic would query pending insights -> generate -> post

if __name__ == "__main__":
    # Test harness
    from ..config import load_accounts
    accounts = load_accounts(config.ACCOUNTS_FILE)
    if accounts:
        engine = AntigravityEngine(accounts[0])
        engine.run()
    else:
        print("No accounts configured.")
