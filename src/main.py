from src.core.engine import AntigravityEngine
import sys

# Ensure src is in path if needed, though standard python run usually handles it
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    engine = AntigravityEngine()
    try:
        engine.run()
    except KeyboardInterrupt:
        print("Shutdown requested.")
