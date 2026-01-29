import sqlite3
import json
import logging
# import chromadb # Moved inside method
from typing import List, Optional
from datetime import datetime
from ..config import config
from ..core.types import Signal, Insight, Hook

logger = logging.getLogger("MemoryStore")

class MemoryStore:
    def __init__(self):
        self.db_path = f"{config.DATA_DIR}/aae_brain.db"
        self._init_sqlite()
        self._init_vector_db()

    def _init_sqlite(self):
        os.makedirs(config.DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Signals Table
        c.execute('''CREATE TABLE IF NOT EXISTS signals
                     (id TEXT PRIMARY KEY, content TEXT, author_id TEXT, 
                      created_at TEXT, urgency_score REAL, metadata TEXT)''')
                      
        # Insights Table
        c.execute('''CREATE TABLE IF NOT EXISTS insights
                     (id TEXT PRIMARY KEY, content TEXT, created_at TEXT, 
                      fitness_score REAL)''')
                      
        # Hooks Table
        c.execute('''CREATE TABLE IF NOT EXISTS hooks
                     (id TEXT PRIMARY KEY, template_text TEXT, structure_type TEXT,
                      emotional_polarity TEXT, historical_performance REAL, 
                      saturation_score REAL)''')
        
        conn.commit()
        conn.close()

    def _init_vector_db(self):
        try:
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=f"{config.DATA_DIR}/chroma")
            self.insight_collection = self.chroma_client.get_or_create_collection("insights")
        except Exception as e:
            logger.warning(f"ChromaDB Init Failed (Mocking for now): {e}")
            self.chroma_client = None

    # --- Signal Operations ---
    def add_signal(self, signal: Signal):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO signals VALUES (?, ?, ?, ?, ?, ?)",
                  (signal.id, signal.content, signal.author_id, 
                   signal.created_at.isoformat(), signal.urgency_score, 
                   json.dumps(signal.metadata)))
        conn.commit()
        conn.close()

    def get_high_urgency_signals(self, limit=10) -> List[Signal]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM signals ORDER BY urgency_score DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        
        results = []
        for r in rows:
            results.append(Signal(
                id=r[0], content=r[1], author_id=r[2], 
                created_at=datetime.fromisoformat(r[3]), 
                urgency_score=r[4], metadata=json.loads(r[5])
            ))
        return results

    # --- Insight Operations ---
    def add_insight(self, insight: Insight):
        # 1. SQLite
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO insights VALUES (?, ?, ?, ?)",
                  (insight.id, insight.content, insight.created_at.isoformat(), 
                   insight.fitness_score))
        conn.commit()
        conn.close()
        
        # 2. Vector DB
        if self.chroma_client and insight.embedding:
            self.insight_collection.add(
                ids=[insight.id],
                embeddings=[insight.embedding],
                metadatas=[{"fitness": insight.fitness_score}],
                documents=[insight.content]
            )

    # --- Hook Operations ---
    def add_hook(self, hook: Hook):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO hooks VALUES (?, ?, ?, ?, ?, ?)",
                  (hook.id, hook.template_text, hook.structure_type, 
                   hook.emotional_polarity, hook.historical_performance, 
                   hook.saturation_score))
        conn.commit()
        conn.close()

# Global Instance
import os
store = MemoryStore()
