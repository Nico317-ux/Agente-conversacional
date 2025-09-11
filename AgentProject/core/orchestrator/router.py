import unicodedata

class Router:
    def __init__(self):
        pass

    def requires_rag(self, text: str) -> bool:
        rag_keyphrases = [
            'que es', 'quién fue', 'como funciona',
            'explica', 'informacion sobre', 'detalles de',
            'informacion', 'detalles','defineme', 'define', 'definir', 'what is', 
            'who was', 'how it works', 'explain', 
            'information about', 'details of', 'information', 
            'give me', 'details'
        ]
        normalized_text = unicodedata.normalize('NFD', text)
        without_an_accent = "".join(
            char for char in normalized_text if unicodedata.category(char) != 'Mn'
        )
        return any(phrase in without_an_accent.lower() for phrase in rag_keyphrases)
    
    def router(self, user_input: str) -> str:
        if self.requires_rag(user_input):
            return True
        return False
