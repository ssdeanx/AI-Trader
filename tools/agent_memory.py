"""
Agent Memory System with Hybrid SQL + Vector Search
Features:
- SQLite for structured data storage
- Sentence transformers for vector embeddings
- Hybrid retrieval (semantic + keyword + recency)
- LRU cache for performance
- Cross-platform compatibility
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Lazy import for sentence transformers (only loaded when needed)
_sentence_transformer_model = None


def get_embedding_model():
    """Lazy load sentence transformer model"""
    global _sentence_transformer_model
    if _sentence_transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use lightweight but effective model for financial domain
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            _sentence_transformer_model = SentenceTransformer(model_name)
            print(f"✅ Loaded embedding model: {model_name}")
        except ImportError:
            print("⚠️ sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
    return _sentence_transformer_model


class AgentMemory:
    """
    Hybrid memory system for AI trading agents
    
    Memory types:
    1. Short-term: Recent trading decisions and reasoning
    2. Long-term: Historical patterns and learned strategies
    3. Episodic: Specific market events and outcomes
    
    Features:
    - Vector similarity search for semantic retrieval
    - SQL queries for structured data filtering
    - Temporal decay for relevance scoring
    - Caching layer for performance
    """

    def __init__(
        self,
        agent_signature: str,
        db_path: Optional[str] = None,
        embedding_dim: int = 384,  # all-MiniLM-L6-v2 default
        cache_size: int = 128
    ):
        """
        Initialize agent memory system
        
        Args:
            agent_signature: Unique identifier for the agent
            db_path: Path to SQLite database (defaults to data/memory/{signature}.db)
            embedding_dim: Dimension of embedding vectors
            cache_size: Size of LRU cache for embeddings
        """
        self.agent_signature = agent_signature
        self.embedding_dim = embedding_dim
        # Setup database path
        if db_path is None:
            base_dir = Path(__file__).resolve().parents[1]
            memory_dir = base_dir / "data" / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(memory_dir / f"{agent_signature}.db")
        else:
            self.db_path = db_path

        # Initialize database
        self.conn = self._init_database()

        # Cache for embeddings
        self._embedding_cache: Dict[str, np.ndarray] = {}

        print(f"✅ Initialized AgentMemory for {agent_signature}")
        print(f"📁 Database: {self.db_path}")

    def _init_database(self) -> sqlite3.Connection:
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # Main memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                date TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT,
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL,
                created_at REAL NOT NULL,
                INDEX idx_date (date),
                INDEX idx_type (memory_type),
                INDEX idx_importance (importance),
                INDEX idx_timestamp (timestamp)
            )
        """)

        # Trading decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER,
                date TEXT NOT NULL,
                action TEXT NOT NULL,
                symbol TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                price REAL,
                quantity REAL,
                outcome TEXT,
                profit_loss REAL,
                created_at REAL NOT NULL,
                FOREIGN KEY (memory_id) REFERENCES memories(id),
                INDEX idx_symbol (symbol),
                INDEX idx_date (date),
                INDEX idx_action (action)
            )
        """)

        # Market patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence REAL NOT NULL,
                occurrences INTEGER DEFAULT 1,
                success_rate REAL,
                embedding BLOB,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                INDEX idx_pattern (pattern_name),
                INDEX idx_confidence (confidence)
            )
        """)
        conn.commit()
        return conn

    def _text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text to embedding vector with caching"""
        # Check cache first
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        # Generate embedding
        model = get_embedding_model()
        embedding = np.array(model.encode(text, normalize_embeddings=True))

        # Cache it (with size limit)
        if len(self._embedding_cache) < 1000:
            self._embedding_cache[text] = embedding

        return embedding

    def _embedding_to_blob(self, embedding: np.ndarray) -> bytes:
        """Convert numpy array to blob for storage"""
        return embedding.astype(np.float32).tobytes()

    def _blob_to_embedding(self, blob: bytes) -> np.ndarray:
        """Convert blob back to numpy array"""
        return np.frombuffer(blob, dtype=np.float32)

    def add_memory(
        self,
        content: str,
        memory_type: str,
        date: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> int:
        """
        Add new memory to the system
        Args:
            content: Memory content (text)
            memory_type: Type of memory (e.g., "decision", "observation", "reflection")
            date: Trading date associated with this memory
            metadata: Additional structured data
            importance: Importance score (0.0-1.0)
        Returns:
            Memory ID
        """
        timestamp = time.time()
        embedding = self._text_to_embedding(content)
        embedding_blob = self._embedding_to_blob(embedding)
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO memories
            (timestamp, date, memory_type, content, embedding, metadata, importance, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, date, memory_type, content, embedding_blob, metadata_json, importance, timestamp, timestamp))

        self.conn.commit()
        memory_id = cursor.lastrowid
        assert memory_id is not None

        return memory_id

    def add_trading_decision(
        self,
        date: str,
        action: str,
        symbol: str,
        reasoning: str,
        price: Optional[float] = None,
        quantity: Optional[float] = None,
        outcome: Optional[str] = None,
        profit_loss: Optional[float] = None
    ) -> int:
        """Add trading decision to memory"""
        # First add to memories
        content = f"Trading Decision: {action} {symbol}\nReasoning: {reasoning}"
        metadata = {
            "action": action,
            "symbol": symbol,
            "price": price,
            "quantity": quantity
        }
        memory_id = self.add_memory(content, "trading_decision", date, metadata, importance=0.8)
        
        # Then add to trading_decisions table
        timestamp = time.time()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trading_decisions
            (memory_id, date, action, symbol, reasoning, price, quantity, outcome, profit_loss, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, date, action, symbol, reasoning, price, quantity, outcome, profit_loss, timestamp))
        
        self.conn.commit()
        return memory_id

    def semantic_search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector similarity
        
        Args:
            query: Search query text
            memory_type: Filter by memory type (optional)
            top_k: Number of results to return
            min_similarity: Minimum cosine similarity threshold
        
        Returns:
            List of matching memories with similarity scores
        """
        query_embedding = self._text_to_embedding(query)
        
        cursor = self.conn.cursor()
        
        # Build query
        sql = "SELECT * FROM memories"
        params = []
        
        if memory_type:
            sql += " WHERE memory_type = ?"
            params.append(memory_type)
        
        cursor.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            if row["embedding"] is None:
                continue
            
            memory_embedding = self._blob_to_embedding(row["embedding"])
            similarity = float(np.dot(query_embedding, memory_embedding))
            
            if similarity >= min_similarity:
                results.append({
                    "id": row["id"],
                    "content": row["content"],
                    "date": row["date"],
                    "memory_type": row["memory_type"],
                    "importance": row["importance"],
                    "similarity": similarity,
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                })
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def hybrid_search(
        self,
        query: str,
        date_range: Optional[Tuple[str, str]] = None,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0,
        top_k: int = 10,
        recency_weight: float = 0.2,
        importance_weight: float = 0.3,
        similarity_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic similarity, recency, and importance
        
        Args:
            query: Search query
            date_range: Tuple of (start_date, end_date) for filtering
            memory_types: List of memory types to include
            min_importance: Minimum importance threshold
            top_k: Number of results
            recency_weight: Weight for recency score (0-1)
            importance_weight: Weight for importance score (0-1)
            similarity_weight: Weight for semantic similarity (0-1)
        
        Returns:
            List of memories ranked by hybrid score
        """
        # Semantic search first
        results = self.semantic_search(query, top_k=top_k * 3)
        
        # Apply additional filters
        filtered_results = []
        current_time = time.time()
        
        for result in results:
            # Filter by date range
            if date_range:
                if not (date_range[0] <= result["date"] <= date_range[1]):
                    continue
            
            # Filter by memory type
            if memory_types and result["memory_type"] not in memory_types:
                continue
            
            # Filter by importance
            if result["importance"] < min_importance:
                continue
            
            # Calculate recency score (exponential decay)
            cursor = self.conn.cursor()
            cursor.execute("SELECT timestamp FROM memories WHERE id = ?", (result["id"],))
            row = cursor.fetchone()
            if row:
                age_days = (current_time - row["timestamp"]) / 86400
                recency_score = np.exp(-age_days / 30)  # 30-day half-life
            else:
                recency_score = 0.0
            
            # Calculate hybrid score
            hybrid_score = (
                similarity_weight * result["similarity"] +
                importance_weight * result["importance"] +
                recency_weight * recency_score
            )
            
            result["recency_score"] = recency_score
            result["hybrid_score"] = hybrid_score
            filtered_results.append(result)
        
        # Sort by hybrid score
        filtered_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        # Update access count
        for result in filtered_results[:top_k]:
            self._update_access(result["id"])
        
        return filtered_results[:top_k]

    def _update_access(self, memory_id: int):
        """Update access count and last accessed time"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE memories 
            SET access_count = access_count + 1, last_accessed = ?
            WHERE id = ?
        """, (time.time(), memory_id))
        self.conn.commit()

    def get_recent_decisions(self, days: int = 7, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent trading decisions"""
        cursor = self.conn.cursor()
        
        cutoff_date = (datetime.now() - __import__("datetime").timedelta(days=days)).strftime("%Y-%m-%d")
        
        if symbol:
            cursor.execute("""
                SELECT * FROM trading_decisions 
                WHERE date >= ? AND symbol = ?
                ORDER BY created_at DESC
            """, (cutoff_date, symbol))
        else:
            cursor.execute("""
                SELECT * FROM trading_decisions 
                WHERE date >= ?
                ORDER BY created_at DESC
            """, (cutoff_date,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "date": row["date"],
                "action": row["action"],
                "symbol": row["symbol"],
                "reasoning": row["reasoning"],
                "price": row["price"],
                "quantity": row["quantity"],
                "outcome": row["outcome"],
                "profit_loss": row["profit_loss"]
            })
        
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM memories")
        total_memories = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM trading_decisions")
        total_decisions = cursor.fetchone()["total"]
        
        cursor.execute("SELECT memory_type, COUNT(*) as count FROM memories GROUP BY memory_type")
        memory_types = {row["memory_type"]: row["count"] for row in cursor.fetchall()}
        
        cursor.execute("SELECT AVG(importance) as avg_importance FROM memories")
        avg_importance = cursor.fetchone()["avg_importance"]
        
        return {
            "total_memories": total_memories,
            "total_decisions": total_decisions,
            "memory_types": memory_types,
            "avg_importance": avg_importance,
            "db_path": self.db_path,
            "cache_size": len(self._embedding_cache)
        }

    def clear_old_memories(self, days: int = 90, keep_important: bool = True):
        """
        Clear old memories to manage database size
        
        Args:
            days: Delete memories older than this many days
            keep_important: Keep memories with importance > 0.7 even if old
        """
        cutoff_timestamp = time.time() - (days * 86400)
        
        cursor = self.conn.cursor()
        
        if keep_important:
            cursor.execute("""
                DELETE FROM memories 
                WHERE timestamp < ? AND importance < 0.7
            """, (cutoff_timestamp,))
        else:
            cursor.execute("""
                DELETE FROM memories 
                WHERE timestamp < ?
            """, (cutoff_timestamp,))
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        
        # Vacuum to reclaim space
        cursor.execute("VACUUM")
        
        print(f"🗑️  Deleted {deleted_count} old memories")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print(f"✅ Closed memory database for {self.agent_signature}")

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Example usage
if __name__ == "__main__":
    # Create memory system
    memory = AgentMemory("test-agent")
    
    # Add some memories
    memory.add_memory(
        content="Market showed strong bullish momentum with tech stocks leading gains",
        memory_type="observation",
        date="2026-01-05",
        importance=0.7
    )
    
    memory.add_trading_decision(
        date="2026-01-05",
        action="buy",
        symbol="NVDA",
        reasoning="Strong earnings report and positive sector sentiment",
        price=145.50,
        quantity=10
    )
    
    # Search memories
    results = memory.semantic_search("bullish tech stocks", top_k=5)
    print("\n🔍 Semantic search results:")
    for r in results:
        print(f"  [{r['similarity']:.3f}] {r['content'][:100]}...")
    
    # Hybrid search
    results = memory.hybrid_search("recent NVDA decisions", top_k=5)
    print("\n🎯 Hybrid search results:")
    for r in results:
        print(f"  [Score: {r['hybrid_score']:.3f}] {r['content'][:100]}...")
    
    # Statistics
    stats = memory.get_statistics()
    print(f"\n📊 Memory Statistics:")
    print(f"  Total memories: {stats['total_memories']}")
    print(f"  Total decisions: {stats['total_decisions']}")
    print(f"  Memory types: {stats['memory_types']}")
    
    memory.close()
