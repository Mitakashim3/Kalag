"""
Kalag PDF Parser
Uses LlamaParse for intelligent document parsing with pypdf fallback
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import os
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import LlamaParse, but don't fail if not available
_llama_parse_available = False
try:
    from llama_parse import LlamaParse
    _llama_parse_available = True
except ImportError:
    logger.warning("LlamaParse not available, using pypdf fallback")
except Exception as e:
    logger.warning(f"LlamaParse import error: {e}, using pypdf fallback")


class DocumentParser:
    """
    PDF parsing using LlamaParse with fallback to pypdf.
    
    LlamaParse Features (when available):
    - Table extraction with structure preservation
    - Image/chart detection
    - Multi-column layout handling
    
    pypdf Fallback:
    - Basic text extraction per page
    """
    
    def __init__(self):
        self.use_llama_parse = (
            _llama_parse_available 
            and settings.llama_cloud_api_key is not None
        )
        
        if self.use_llama_parse:
            self.parser = LlamaParse(
                api_key=settings.llama_cloud_api_key,
                result_type="markdown",
                num_workers=2,
                verbose=False,
                language="en",
            )
            logger.info("Using LlamaParse for PDF parsing")
        else:
            self.parser = None
            logger.info("Using pypdf fallback for PDF parsing")
    
    async def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a PDF document and extract structured content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict containing:
            - pages: List of page contents
            - total_pages: Number of pages
            - raw_text: Combined text
        """
        if self.use_llama_parse and self.parser:
            return await self._parse_with_llama(file_path)
        else:
            return await self._parse_with_pypdf(file_path)
    
    async def _parse_with_llama(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF using LlamaParse."""
        try:
            documents = await self.parser.aload_data(file_path)
            
            # Check if we actually got data (LlamaParse might return empty on auth failure)
            if not documents or len(documents) == 0:
                logger.warning("LlamaParse returned no documents, falling back to pypdf")
                return await self._parse_with_pypdf(file_path)
            
            result = {
                "pages": [],
                "total_pages": len(documents),
                "raw_text": "",
                "tables": [],
                "has_images": False
            }
            
            for i, doc in enumerate(documents):
                page_content = {
                    "page_number": i + 1,
                    "text": doc.text,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                }
                result["pages"].append(page_content)
                result["raw_text"] += doc.text + "\n\n"
            
            logger.info(f"Successfully parsed PDF with LlamaParse: {file_path} ({len(documents)} pages)")
            return result
            
        except Exception as e:
            logger.warning(f"LlamaParse failed: {e}, falling back to pypdf")
            return await self._parse_with_pypdf(file_path)
    
    async def _parse_with_pypdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF using pypdf (fallback)."""
        from pypdf import PdfReader
        
        try:
            reader = PdfReader(file_path)
            
            result = {
                "pages": [],
                "total_pages": len(reader.pages),
                "raw_text": "",
                "tables": [],
                "has_images": False
            }
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                page_content = {
                    "page_number": i + 1,
                    "text": text,
                    "metadata": {}
                }
                result["pages"].append(page_content)
                result["raw_text"] += text + "\n\n"
            
            logger.info(f"Successfully parsed PDF with pypdf: {file_path}, {result['total_pages']} pages")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise


# Try to import pdf2image for rendering pages
_pdf2image_available = False
try:
    from pdf2image import convert_from_path
    _pdf2image_available = True
except ImportError:
    logger.warning("pdf2image not available, page rendering will be disabled")


async def render_pdf_pages(
    pdf_path: str,
    output_dir: str,
    dpi: int = 150
) -> List[Dict[str, Any]]:
    """
    Render PDF pages to images for vision analysis.
    
    This is CRITICAL for multi-modal search - we need page images to:
    1. Run vision analysis with Gemini
    2. Provide visual citations in search results
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save page images
        dpi: Resolution (150 is good balance of quality vs size)
        
    Returns:
        List of dicts with page info and image paths
    """
    if not _pdf2image_available:
        logger.warning("pdf2image not available, returning empty page list")
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert PDF pages to images
    try:
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            fmt="png",
            thread_count=2
        )
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        # Try with poppler path for Windows
        try:
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt="png",
                poppler_path=os.environ.get("POPPLER_PATH")
            )
        except Exception as e2:
            logger.error(f"Poppler fallback also failed: {str(e2)}")
            raise
    
    page_info = []
    
    for i, image in enumerate(images):
        page_num = i + 1
        image_filename = f"page_{page_num:04d}.png"
        image_path = os.path.join(output_dir, image_filename)
        
        # Save the page image
        image.save(image_path, "PNG", optimize=True)
        
        page_info.append({
            "page_number": page_num,
            "image_path": image_path,
            "width": image.width,
            "height": image.height
        })
        
        logger.debug(f"Rendered page {page_num} to {image_path}")
    
    logger.info(f"Rendered {len(images)} pages from {pdf_path}")
    return page_info


def get_page_count(pdf_path: str) -> int:
    """Quick page count without full parsing."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        logger.error(f"Error getting page count: {e}")
        raise Exception(f"Unable to get page count. Is poppler installed and in PATH?")
