import threading
import time
import logging
from typing import List
from ..config import config, load_accounts
from ..core.engine import AntigravityEngine

logger = logging.getLogger("FleetManager")

class FleetManager:
    """
    Orchestrates multiple Antigravity Engines, one per account.
    """
    def __init__(self):
        self.engines: List[AntigravityEngine] = []
        self.threads: List[threading.Thread] = []
        self.running = False

    def load_engines(self):
        """Loads accounts from config and initializes engines."""
        accounts = load_accounts(config.ACCOUNTS_FILE)
        logger.info(f"Learned {len(accounts)} accounts from config.")
        
        for acc in accounts:
            if acc.enabled:
                engine = AntigravityEngine(acc)
                self.engines.append(engine)
                logger.info(f"Loaded Engine for: {acc.id}")
            else:
                logger.info(f"Skipping disabled account: {acc.id}")

    def start(self):
        """Starts all engines in separate threads."""
        if not self.engines:
            self.load_engines()
            
        self.running = True
        logger.info("Starting Fleet...")
        
        for engine in self.engines:
            t = threading.Thread(target=engine.run, name=f"Thread-{engine.account_config.id}")
            t.daemon = True # Daemonize to kill when main process dies
            t.start()
            self.threads.append(t)
            
        # Main loop just monitors
        try:
            while self.running:
                time.sleep(5)
                # Could perform health checks here
                dead_threads = [t for t in self.threads if not t.is_alive()]
                if dead_threads:
                    logger.warning(f"Found {len(dead_threads)} dead threads!")
                    # TODO: Restart logic
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logger.info("Stopping Fleet...")
        self.running = False
        for engine in self.engines:
            engine.running = False
        
        for t in self.threads:
            t.join(timeout=5)
            
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fleet = FleetManager()
    fleet.start()
