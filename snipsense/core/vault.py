"""Embedded SQLite and FTS5 Visual Memory Search Index for SnipSense."""

from __future__ import annotations
import os
import re
import time
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass(frozen=True)
class VaultRecord:
    """Represents an indexed capture stored in the persistent database."""
    id: int
    file_path: str
    title: str
    ocr_text: str
    tags: str
    window_title: str
    perceptual_hash: str
    created_at: float


@dataclass(frozen=True)
class SearchResult:
    """Represents a ranked match from an FTS5 search query."""
    id: int
    file_path: str
    title: str
    ocr_text: str
    tags: str
    created_at: float
    snippet: str
    rank: float = 0.0


class VaultDatabase:
    """Manages SQLite storage and FTS5 full-text search for historical visual memory."""

    _instance: Optional["VaultDatabase"] = None

    def __init__(self, db_path: Optional[Path] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default to ~/.snipsense/vault.db
            home_dir = Path.home() / ".snipsense"
            home_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = home_dir / "vault.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @classmethod
    def get_instance(cls, db_path: Optional[Path] = None) -> "VaultDatabase":
        """Singleton accessor for the global vault instance."""
        if cls._instance is None or (db_path and cls._instance.db_path != Path(db_path)):
            cls._instance = cls(db_path)
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with row_factory enabled."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        """Initializes tables, FTS5 virtual table, and sync triggers."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Main captures metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    ocr_text TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '',
                    window_title TEXT NOT NULL DEFAULT '',
                    perceptual_hash TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL
                );
            """)

            # FTS5 virtual table for full-text search
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_captures USING fts5(
                    title,
                    ocr_text,
                    tags,
                    file_path,
                    content='captures',
                    content_rowid='id'
                );
            """)

            # Triggers to keep FTS table in sync with main table
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS captures_ai AFTER INSERT ON captures BEGIN
                    INSERT INTO fts_captures(rowid, title, ocr_text, tags, file_path)
                    VALUES (new.id, new.title, new.ocr_text, new.tags, new.file_path);
                END;
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS captures_ad AFTER DELETE ON captures BEGIN
                    INSERT INTO fts_captures(fts_captures, rowid, title, ocr_text, tags, file_path)
                    VALUES ('delete', old.id, old.title, old.ocr_text, old.tags, old.file_path);
                END;
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS captures_au AFTER UPDATE ON captures BEGIN
                    INSERT INTO fts_captures(fts_captures, rowid, title, ocr_text, tags, file_path)
                    VALUES ('delete', old.id, old.title, old.ocr_text, old.tags, old.file_path);
                    INSERT INTO fts_captures(rowid, title, ocr_text, tags, file_path)
                    VALUES (new.id, new.title, new.ocr_text, new.tags, new.file_path);
                END;
            """)

            conn.commit()

    def index_capture(
        self,
        file_path: str | Path,
        title: str,
        ocr_text: str = "",
        tags: str = "",
        window_title: str = "",
        perceptual_hash: str = "",
        created_at: Optional[float] = None,
    ) -> int:
        """Inserts or updates a capture record in the database."""
        path_str = str(Path(file_path).resolve())
        timestamp = created_at if created_at is not None else time.time()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO captures (file_path, title, ocr_text, tags, window_title, perceptual_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    title=excluded.title,
                    ocr_text=excluded.ocr_text,
                    tags=excluded.tags,
                    window_title=excluded.window_title,
                    perceptual_hash=excluded.perceptual_hash,
                    created_at=excluded.created_at
                RETURNING id;
            """, (path_str, title, ocr_text, tags, window_title, perceptual_hash, timestamp))

            row = cursor.fetchone()
            conn.commit()
            return row["id"] if row else 0

    def get_capture(self, capture_id: int) -> Optional[VaultRecord]:
        """Retrieves a single capture record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM captures WHERE id = ?", (capture_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return VaultRecord(
                id=row["id"],
                file_path=row["file_path"],
                title=row["title"],
                ocr_text=row["ocr_text"],
                tags=row["tags"],
                window_title=row["window_title"],
                perceptual_hash=row["perceptual_hash"],
                created_at=row["created_at"],
            )

    @staticmethod
    def _sanitize_fts_query(query: str) -> str:
        """Sanitizes user input into valid FTS5 prefix syntax safely."""
        # Extract alphanumeric words
        tokens = re.findall(r"[a-zA-Z0-9_]+", query)
        if not tokens:
            return ""
        # Format tokens with prefix wildcard, e.g. token1* token2*
        formatted = " ".join(f'"{t}"*' for t in tokens)
        return formatted

    def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Searches indexed captures by title, OCR text, or tags.
        
        Args:
            query: User search string. If empty, returns recent captures.
            limit: Maximum results to return.
            
        Returns:
            List of SearchResult records.
        """
        trimmed = query.strip()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if not trimmed:
                # Return most recent captures
                cursor.execute("""
                    SELECT id, file_path, title, ocr_text, tags, created_at,
                           substr(ocr_text, 1, 120) as snippet
                    FROM captures
                    ORDER BY created_at DESC
                    LIMIT ?;
                """, (limit,))
                rows = cursor.fetchall()
                return [
                    SearchResult(
                        id=r["id"],
                        file_path=r["file_path"],
                        title=r["title"],
                        ocr_text=r["ocr_text"],
                        tags=r["tags"],
                        created_at=r["created_at"],
                        snippet=r["snippet"] or "(No text detected)",
                        rank=0.0,
                    )
                    for r in rows
                ]

            fts_query = self._sanitize_fts_query(trimmed)
            if not fts_query:
                return []

            try:
                # Query FTS5 with BM25 ranking and snippet generation
                cursor.execute("""
                    SELECT c.id, c.file_path, c.title, c.ocr_text, c.tags, c.created_at,
                           snippet(fts_captures, 1, '<mark>', '</mark>', '...', 12) as snippet,
                           bm25(fts_captures) as rank
                    FROM fts_captures f
                    JOIN captures c ON f.rowid = c.id
                    WHERE fts_captures MATCH ?
                    ORDER BY rank ASC, c.created_at DESC
                    LIMIT ?;
                """, (fts_query, limit))
                rows = cursor.fetchall()

                return [
                    SearchResult(
                        id=r["id"],
                        file_path=r["file_path"],
                        title=r["title"],
                        ocr_text=r["ocr_text"],
                        tags=r["tags"],
                        created_at=r["created_at"],
                        snippet=r["snippet"] if r["snippet"] else (r["ocr_text"][:100] or "(No text detected)"),
                        rank=r["rank"],
                    )
                    for r in rows
                ]
            except sqlite3.OperationalError:
                # Fallback to simple LIKE query if FTS query syntax is malformed
                like_pattern = f"%{trimmed}%"
                cursor.execute("""
                    SELECT id, file_path, title, ocr_text, tags, created_at,
                           substr(ocr_text, 1, 120) as snippet
                    FROM captures
                    WHERE title LIKE ? OR ocr_text LIKE ? OR tags LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?;
                """, (like_pattern, like_pattern, like_pattern, limit))
                rows = cursor.fetchall()
                return [
                    SearchResult(
                        id=r["id"],
                        file_path=r["file_path"],
                        title=r["title"],
                        ocr_text=r["ocr_text"],
                        tags=r["tags"],
                        created_at=r["created_at"],
                        snippet=r["snippet"] or "(No text detected)",
                        rank=0.0,
                    )
                    for r in rows
                ]

    def count_total(self) -> int:
        """Returns the total number of indexed captures."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM captures;")
            return cursor.fetchone()[0]
