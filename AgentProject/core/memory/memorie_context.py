import sqlite3
from typing import List, Dict
import tiktoken

class ConversationMemory:
    def __init__(self,
                 db_path: str,
                 max_context_tokens: int,
                 session_id: str = 'default'):
        
        self.conn = sqlite3.connect(db_path)
        self.session_id = session_id
        self.max_context_tokens = max_context_tokens
        self.tokenizer = tiktoken.get_encoding('cl100k_base') # Tokenizar

        #Configuracion si la sesion no existe
        self._init_session()

    def _init_session(self) -> None:
        cursor = self.conn.cursor()

        cursor.execute('SELECT 1 FROM sessions WHERE session_id = ?',
                       (self.session_id,))
        
        if not cursor.fetchone():
            cursor.execute('INSERT INTO sessions (session_id) VALUES (?)',
                           (self.session_id,))
            
            self.conn.commit()
    
    def add_message(self, role: str, content: str) -> None:
        tokens = len(self.tokenizer.encode(content))
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO messages (session_id, role, content, tokens)
            VALUES (?, ?, ?, ?)
            ''', (self.session_id, role, content, tokens))

        self.conn.commit()

    def get_context(self) -> List[Dict[str, str]]:
        cursor = self.conn.cursor()

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
        return filtred_messages
    
    def clear(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            DELETE FROM messages WHERE session_id = ?
            ''', (self.session_id,))
        self.conn.commit()
    
    def close(self) -> None:
        self.conn.close()