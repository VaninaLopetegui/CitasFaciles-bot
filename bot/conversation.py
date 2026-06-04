import json
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Optional

DB_PATH = "conversations.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            user_id      TEXT PRIMARY KEY,
            step         TEXT,
            date         TEXT,
            time         TEXT,
            professional TEXT,
            client_name  TEXT,
            history      TEXT NOT NULL DEFAULT '[]',
            updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@dataclass
class ConversationState:
    scheduling_step: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    professional: Optional[dict] = None
    client_name: Optional[str] = None
    history: list = field(default_factory=list)


class ConversationStore:
    def __init__(self):
        self._cache: dict[str, ConversationState] = {}
        self._lock = threading.Lock()

    def get(self, user_id: str) -> ConversationState:
        with self._lock:
            if user_id not in self._cache:
                self._cache[user_id] = self._load(user_id)
            return self._cache[user_id]

    def save(self, user_id: str, state: ConversationState):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT OR REPLACE INTO conversations
                (user_id, step, date, time, professional, client_name, history, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            user_id,
            state.scheduling_step,
            state.appointment_date,
            state.appointment_time,
            json.dumps(state.professional) if state.professional else None,
            state.client_name,
            json.dumps(state.history),
        ))
        conn.commit()
        conn.close()

    def _load(self, user_id: str) -> ConversationState:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT step, date, time, professional, client_name, history "
            "FROM conversations WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()
        if not row:
            return ConversationState()
        return ConversationState(
            scheduling_step=row[0],
            appointment_date=row[1],
            appointment_time=row[2],
            professional=json.loads(row[3]) if row[3] else None,
            client_name=row[4],
            history=json.loads(row[5]) if row[5] else [],
        )

    def reset_scheduling(self, user_id: str):
        state = self.get(user_id)
        state.scheduling_step = None
        state.appointment_date = None
        state.appointment_time = None
        state.professional = None
        state.client_name = None

    def add_to_history(self, user_id: str, role: str, text: str):
        state = self.get(user_id)
        state.history.append({"role": role, "parts": [text]})
        if len(state.history) > 20:
            state.history = state.history[-20:]


conversation_store = ConversationStore()
