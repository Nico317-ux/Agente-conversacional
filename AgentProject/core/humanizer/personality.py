from dataclasses import dataclass
from typing import Dict

@dataclass
class Personality:
    name: str
    description: str
    traits: Dict[str, str]

class PersonalityManager:
    PERSONALITIES = {
        'formal': Personality(
            name= 'formal',
            description= 'Professional assistant with precise language and very polite.',
            traits={
                'tone': 'formal',
                'responses': 'structured',
                'emojis_usage': 'low'
            }
        ),
        "friendly": Personality(
            name="friendly",
            description="Close, friendly assistant that provides a feeling of closeness and familiarity",
            traits={
                "tone": "colloquial and casual",
                "responses": "empathetic, daring, and funny",
                "emoji_usage": "high"
            }
        )
    }

    def __init__(self, default_personality: str = 'formal'):
        self.current = self.PERSONALITIES.get(default_personality)
    def set_personality(self, name: str) -> bool:
        if name in self.PERSONALITIES:
            self.current = self.PERSONALITIES[name]
            return True
        return False