import sqlite3
from typing import List, Dict
import tiktoken
import asyncio

class ConversationMemory:
    def __init__(self,
                 db_path: str,
                 max_context_tokens: int,
                 session_id: str = 'default'):
        
        self.db_path = db_path
        self.session_id = session_id
        self.max_context_tokens = max_context_tokens
        self.tokenizer = tiktoken.get_encoding('cl100k_base') 

        self._init_session()

    def _init_session(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT 1 FROM sessions WHERE session_id = ?',
                       (self.session_id,))
        
        if not cursor.fetchone():
            cursor.execute('INSERT INTO sessions (session_id) VALUES (?)',
                           (self.session_id,))
            
            conn.commit()
        conn.close()
    
    def _add_message_sync(self, role: str, content: str) -> None:
        conn = sqlite3.connect(self.db_path)
        tokens = len(self.tokenizer.encode(content))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO messages (session_id, role, content, tokens)
            VALUES (?, ?, ?, ?)
            ''', (self.session_id, role, content, tokens))

        conn.commit()
        conn.close()
    
    async def add_menssage(self, role: str, content: str) -> None:
        await asyncio.to_thread(self._add_message_sync, role, content)

    def get_context(self) -> List[Dict[str, str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT role, content FROM messages WHERE session_id = ?
        ORDER BY message_timestamp DESC
        ''', (self.session_id,))

        messages = [{'role': row[0], 'content': row[1]} for row in cursor.fetchall()]

        total_tokens = 0
        filtred_messages = []

        for msg in reversed(messages):
            msg_tokens = len(self.tokenizer.encode(msg['content']))
            if total_tokens + msg_tokens <= self.max_context_tokens:
                filtred_messages.insert(0, msg) #mantiene el orden cronologico
                total_tokens += msg_tokens
            else:
                break
        conn.close()
        return filtred_messages
    
    def clear(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''
            DELETE FROM messages WHERE session_id = ?
            ''', (self.session_id,))
        conn.commit()
        conn.close()
    
    def close(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.close()