from docx import Document
from pathlib import Path
from typing import Any, Dict, Optional
import json
from datetime import datetime
from docx.shared import Cm

class DocxEditor:
    def __init__(self):
        self.current_docx = None
        self.doc_path = None

    def create_new_docx(self, margins: Optional[Dict[str, float]] = None) -> Document:
        self.current_docx = Document()
        self.doc_path = None
        if margins:
            self.set_margins(margins)
        return self.current_docx

    def set_margins(self, margins:Dict[str, float]):
        if not self.current_docx:
            raise ValueError("No document is currently open")

        section = self.current_docx.sections[0]
        if 'top' in margins:
            section.top_margin = Cm(margins['top'])
        if 'bottom' in margins:
            section.bottom_margin = Cm(margins['bottom'])
        if 'left' in margins:
            section.left_margin = Cm(margins['left'])
        if 'right' in margins:
            section.right_margin = Cm(margins['right'])

    def open_docx(self, file_path: str) -> Document:
        path = Path(file_path).absolute()
        self.current_docx = Document(str(path))
        self.doc_path = path
        return self.current_docx

def format_json(status: str, message: str, data: Dict[str, Any] = None, path: str = None) -> str:
    response = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
    if data:
        response.update({'data': data})
    if path:
        response.update({'path': path})
        
    return json.dumps(response)
