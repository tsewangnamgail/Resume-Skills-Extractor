"""
pdf_extractor.py - PDF text extraction utilities
"""

import logging
from io import BytesIO
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Utility class for extracting text from PDF files."""
    
    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        """
        Extract text from a PDF file given as bytes.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text from all pages (combined with double newlines)
            
        Raises:
            ValueError: If PDF is invalid, cannot be read, or no text extracted
        """
        try:
            # Create BytesIO object from bytes
            pdf_stream = BytesIO(pdf_bytes)
            
            # Create PDF reader
            reader = PdfReader(pdf_stream)
            
            # Validate PDF has pages
            if len(reader.pages) == 0:
                raise ValueError("PDF file has no pages")
            
            # Extract text from all pages
            text_parts = []
            total_pages = len(reader.pages)
            
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(page_text.strip())
                        logger.debug(f"Extracted {len(page_text)} characters from page {page_num}/{total_pages}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    # Continue with other pages even if one fails
                    continue
            
            # Combine all pages with double newlines
            full_text = "\n\n".join(text_parts)
            
            if not full_text.strip():
                raise ValueError(
                    "No text could be extracted from the PDF. "
                    "The PDF might be image-based (scanned) or corrupted. "
                    "Consider using OCR for image-based PDFs."
                )
            
            logger.info(f"Successfully extracted {len(full_text)} characters from {total_pages} page(s)")
            
            return full_text
            
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            error_msg = f"Failed to extract text from PDF: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @staticmethod
    def validate_pdf(pdf_bytes: bytes) -> bool:
        """
        Validate that the bytes represent a valid PDF file.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            # Check minimum size
            if len(pdf_bytes) < 4:
                return False
            
            # Check PDF magic number (%PDF)
            if not pdf_bytes[:4].startswith(b'%PDF'):
                return False
            
            # Try to read the PDF structure
            pdf_stream = BytesIO(pdf_bytes)
            reader = PdfReader(pdf_stream)
            
            # Check if it has at least one page
            if len(reader.pages) == 0:
                return False
            
            return True
            
        except Exception:
            return False