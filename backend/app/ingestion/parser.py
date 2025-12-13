"""
Kalag PDF Parser
Uses LlamaParse for intelligent document parsing with pypdf fallback
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import os
import logging
from PIL import Image

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
    dpi: int = 150,
    max_pages: int = 100
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
        max_pages: Maximum number of pages to render (prevent memory issues)
        
    Returns:
        List of dicts with page info and image paths
    """
    if not _pdf2image_available:
        logger.warning("pdf2image not available, returning empty page list")
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert PDF pages to images
    # Use lower DPI for large PDFs to reduce memory usage
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    
    # Limit pages if PDF is too large
    if page_count > max_pages:
        logger.warning(f"PDF has {page_count} pages, limiting to first {max_pages} to prevent memory issues")
        page_count = max_pages
    
    # If PDF is large, reduce DPI to prevent memory issues on free tier
    if page_count > 50:
        dpi = 100
        logger.info(f"Large PDF ({page_count} pages), reducing DPI to {dpi}")
    
    poppler_path = os.environ.get("POPPLER_PATH")
    page_info = []

    # Render pages one-by-one to keep memory low.
    for page_num in range(1, page_count + 1):
        try:
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt="png",
                thread_count=1,  # Reduce parallelism to save memory
                first_page=page_num,
                last_page=page_num,
                poppler_path=poppler_path,
            )
        except Exception as e:
            logger.error(f"Error converting PDF page {page_num} to image: {str(e)}")
            raise

        if not images:
            continue

        image = images[0]

        image_filename = f"page_{page_num:04d}.png"
        image_path = os.path.join(output_dir, image_filename)

        # Resize large images to save memory and disk space
        max_dimension = 2048
        if image.width > max_dimension or image.height > max_dimension:
            ratio = min(max_dimension / image.width, max_dimension / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Save the page image with compression
        image.save(image_path, "PNG", optimize=True, compress_level=6)

        page_info.append({
            "page_number": page_num,
            "image_path": image_path,
            "width": image.width,
            "height": image.height
        })

        logger.debug(f"Rendered page {page_num} to {image_path}")

        # Free memory after each page
        del image
        del images
    
    logger.info(f"Rendered {len(page_info)} pages from {pdf_path}")
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
