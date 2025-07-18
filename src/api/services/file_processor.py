import os
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

# Document processing imports
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None

logger = logging.getLogger(__name__)

class FileProcessor:
    """Service for processing uploaded files and extracting content"""
    
    def __init__(self):
        self.supported_extensions = {
            '.pdf': self._process_pdf,
            '.txt': self._process_text,
            '.md': self._process_markdown,
            '.docx': self._process_docx,
            '.doc': self._process_docx  # Limited support
        }
    
    async def process_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Process a file and extract its content"""
        try:
            # Import here to avoid circular imports
            from ..routes.files import uploaded_files_store
            
            if file_id not in uploaded_files_store:
                logger.error(f"File {file_id} not found in store")
                return None
            
            file_info = uploaded_files_store[file_id]
            filename = file_info["filename"]
            content = file_info["content"]
            
            # Get file extension
            extension = Path(filename).suffix.lower()
            
            if extension not in self.supported_extensions:
                logger.warning(f"Unsupported file extension: {extension}")
                return None
            
            # Process file content
            processor = self.supported_extensions[extension]
            extracted_text = await processor(content, filename)
            
            if extracted_text:
                # Update file info to mark as processed
                file_info["processed"] = True
                file_info["text_content"] = extracted_text
                
                return {
                    "file_id": file_id,
                    "filename": filename,
                    "content": extracted_text,
                    "metadata": {
                        "original_size": len(content),
                        "extracted_size": len(extracted_text),
                        "file_type": extension
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing file {file_id}: {e}")
            return None
    
    async def _process_pdf(self, content: bytes, filename: str) -> Optional[str]:
        """Process PDF file and extract text"""
        try:
            # Try pdfplumber first (better text extraction)
            if pdfplumber:
                return await self._process_pdf_with_pdfplumber(content)
            
            # Fall back to PyPDF2
            if PyPDF2:
                return await self._process_pdf_with_pypdf2(content)
            
            logger.error("No PDF processing library available")
            return None
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            return None
    
    async def _process_pdf_with_pdfplumber(self, content: bytes) -> Optional[str]:
        """Process PDF using pdfplumber"""
        import io
        
        def extract_text():
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n\n".join(text_parts)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_text)
    
    async def _process_pdf_with_pypdf2(self, content: bytes) -> Optional[str]:
        """Process PDF using PyPDF2"""
        import io
        
        def extract_text():
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_parts = []
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n\n".join(text_parts)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, extract_text)
    
    async def _process_text(self, content: bytes, filename: str) -> Optional[str]:
        """Process plain text file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            logger.warning(f"Could not decode text file {filename} with any encoding")
            return None
            
        except Exception as e:
            logger.error(f"Error processing text file {filename}: {e}")
            return None
    
    async def _process_markdown(self, content: bytes, filename: str) -> Optional[str]:
        """Process Markdown file"""
        # Markdown is just text, so use text processor
        return await self._process_text(content, filename)
    
    async def _process_docx(self, content: bytes, filename: str) -> Optional[str]:
        """Process Word document"""
        try:
            if not Document:
                logger.error("python-docx not available for processing .docx files")
                return None
            
            def extract_text():
                import io
                doc = Document(io.BytesIO(content))
                text_parts = []
                
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text)
                
                return "\n\n".join(text_parts)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_text)
            
        except Exception as e:
            logger.error(f"Error processing Word document {filename}: {e}")
            return None
    
    def get_file_preview(self, content: str, max_length: int = 500) -> str:
        """Get a preview of the file content"""
        if not content:
            return "No content available"
        
        if len(content) <= max_length:
            return content
        
        # Get first max_length characters and add ellipsis
        preview = content[:max_length]
        
        # Try to break at word boundary
        last_space = preview.rfind(' ')
        if last_space > max_length * 0.8:  # If we can break at a word near the end
            preview = preview[:last_space]
        
        return preview + "..."
    
    def get_content_summary(self, content: str) -> Dict[str, Any]:
        """Get summary statistics of the content"""
        if not content:
            return {
                "character_count": 0,
                "word_count": 0,
                "line_count": 0,
                "paragraph_count": 0
            }
        
        lines = content.split('\n')
        words = content.split()
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        return {
            "character_count": len(content),
            "word_count": len(words),
            "line_count": len(lines),
            "paragraph_count": len(paragraphs)
        }
    
    def chunk_content(self, content: str, chunk_size: int = 4000, overlap: int = 200) -> List[str]:
        """Split content into chunks for processing"""
        if not content or len(content) <= chunk_size:
            return [content] if content else []
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at sentence or paragraph
            if end < len(content):
                # Look for paragraph break
                paragraph_break = content.rfind('\n\n', start, end)
                if paragraph_break > start:
                    end = paragraph_break
                else:
                    # Look for sentence break
                    sentence_break = content.rfind('.', start, end)
                    if sentence_break > start:
                        end = sentence_break + 1
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap if end < len(content) else len(content)
        
        return chunks