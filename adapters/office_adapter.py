"""
Microsoft Office COM Adapter:
Automates Word, Excel, and Outlook locally via pywin32 COM interfaces.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from core.logger import logger, log_latency
from core.safety_gate import RiskLevel
from tools.base import BaseTool
from pydantic import BaseModel, Field

class CreateWordDocArgs(BaseModel):
    file_path: str = Field(..., description="Path for the output .docx file.")
    title: str = Field(..., description="Document main title.")
    body_text: str = Field(..., description="Content paragraphs of the document.")

class CreateWordDocumentTool(BaseTool):
    name = "create_word_document"
    description = "Create and save a new Microsoft Word document (.docx) with formatted text."
    risk_level = RiskLevel.WRITE
    args_schema = CreateWordDocArgs

    def run(self, file_path: str, title: str, body_text: str) -> str:
        with log_latency("OfficeAdapter.create_word_document", Path(file_path).name):
            try:
                import win32com.client as win32
                word = win32.gencache.EnsureDispatch('Word.Application')
                word.Visible = False
                doc = word.Documents.Add()
                
                # Add Heading
                p1 = doc.Paragraphs.Add()
                p1.Range.Text = title
                p1.Range.Font.Bold = True
                p1.Range.Font.Size = 18
                p1.Range.InsertParagraphAfter()

                # Add Body
                p2 = doc.Paragraphs.Add()
                p2.Range.Text = body_text
                p2.Range.Font.Size = 12
                p2.Range.InsertParagraphAfter()

                dest = str(Path(file_path).resolve())
                doc.SaveAs(dest)
                doc.Close()
                word.Quit()
                return f"Word document created successfully at {dest}."
            except Exception as e:
                logger.warning(f"[OFFICE ADAPTER] COM error (fallback to text file): {e}")
                # Fallback to plain text saving
                Path(file_path).write_text(f"{title}\n\n{body_text}", encoding="utf-8")
                return f"Created text document fallback at {file_path} (Office COM unavailable)."
