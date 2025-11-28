"""
Kalag Vision Pipeline
Uses Google Gemini Flash for analyzing PDF page images

This is the CORE VISION COMPONENT that enables:
1. Extracting descriptions from charts, diagrams, and images in PDFs
2. Creating embeddings from visual content for semantic search
3. Providing visual citations in search results
"""

import google.generativeai as genai
from PIL import Image
import base64
import io
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.google_api_key)


# ===========================================
# Vision Analysis Prompt Templates
# ===========================================

PAGE_ANALYSIS_PROMPT = """Analyze this document page image and provide a detailed description.

Your response should include:
1. **Text Content**: Summarize any visible text content on the page.
2. **Visual Elements**: Describe any charts, graphs, tables, diagrams, or images present.
3. **Data Points**: Extract specific numbers, percentages, or data values visible in charts/tables.
4. **Layout**: Note the overall structure (headers, sections, columns).

Focus on extracting information that would help answer business questions about this document.
Be specific with numbers and data values when visible.

Format your response as:
TEXT SUMMARY: [summary of text content]
VISUAL ELEMENTS: [description of charts/images/tables]
KEY DATA: [specific numbers and data points]
ELEMENT TYPES: [list: chart, table, image, diagram, or none]"""


CHART_ANALYSIS_PROMPT = """Analyze this chart/graph image in detail.

Extract and describe:
1. Chart type (bar, line, pie, etc.)
2. Title and axis labels
3. All visible data points and values
4. Trends or patterns
5. Any legends or annotations

Be precise with numbers. If Q3 revenue shows $2.5M, state that explicitly."""


TABLE_EXTRACTION_PROMPT = """Extract the complete contents of this table.

Provide:
1. Column headers
2. All row data
3. Any totals or summaries
4. Notable patterns in the data

Format as structured text that preserves the table relationships."""


async def analyze_page_image(
    image_path: str,
    custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a PDF page image using Gemini Flash vision capabilities.
    
    This function is the HEART of the multi-modal RAG system.
    It takes a rendered PDF page and extracts:
    - Text descriptions
    - Chart/graph data
    - Table contents
    - Visual element classifications
    
    Args:
        image_path: Path to the page image file (PNG/JPEG)
        custom_prompt: Optional custom prompt (uses PAGE_ANALYSIS_PROMPT if None)
        
    Returns:
        Dict containing:
        - description: Full text description of the page
        - has_charts: Boolean indicating chart presence
        - has_tables: Boolean indicating table presence
        - has_images: Boolean indicating image presence
        - extracted_data: Specific data points extracted
        
    Example:
        >>> result = await analyze_page_image("/uploads/doc1/page_1.png")
        >>> print(result["description"])
        "TEXT SUMMARY: Q3 Financial Report showing revenue growth..."
        >>> print(result["has_charts"])
        True
    """
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Initialize Gemini Flash model with vision
        model = genai.GenerativeModel(settings.gemini_model)
        
        # Use custom prompt or default
        prompt = custom_prompt or PAGE_ANALYSIS_PROMPT
        
        # Generate content with vision
        response = await _call_gemini_vision(model, image, prompt)
        
        # Parse the response to extract structured data
        result = _parse_vision_response(response)
        
        logger.info(f"Successfully analyzed page image: {image_path}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing page image {image_path}: {str(e)}")
        return {
            "description": "",
            "has_charts": False,
            "has_tables": False,
            "has_images": False,
            "extracted_data": [],
            "error": str(e)
        }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _call_gemini_vision(
    model: genai.GenerativeModel,
    image: Image.Image,
    prompt: str
) -> str:
    """
    Call Gemini API with retry logic for reliability.
    
    Uses exponential backoff to handle rate limits on free tier.
    """
    response = model.generate_content([prompt, image])
    return response.text


def _parse_vision_response(response_text: str) -> Dict[str, Any]:
    """
    Parse Gemini vision response into structured data.
    """
    result = {
        "description": response_text,
        "has_charts": False,
        "has_tables": False,
        "has_images": False,
        "extracted_data": []
    }
    
    # Detect element types from response
    lower_response = response_text.lower()
    
    chart_indicators = ["chart", "graph", "bar", "line", "pie", "histogram", "plot"]
    table_indicators = ["table", "grid", "rows", "columns", "spreadsheet"]
    image_indicators = ["image", "photo", "picture", "diagram", "illustration", "figure"]
    
    result["has_charts"] = any(ind in lower_response for ind in chart_indicators)
    result["has_tables"] = any(ind in lower_response for ind in table_indicators)
    result["has_images"] = any(ind in lower_response for ind in image_indicators)
    
    # Extract key data points (numbers with context)
    import re
    data_patterns = [
        r'\$[\d,]+(?:\.\d{2})?[MBK]?',  # Currency
        r'\d+(?:\.\d+)?%',               # Percentages
        r'Q[1-4]\s*\d{4}',               # Quarters
        r'\d{4}',                         # Years
    ]
    
    for pattern in data_patterns:
        matches = re.findall(pattern, response_text)
        result["extracted_data"].extend(matches)
    
    # Remove duplicates while preserving order
    result["extracted_data"] = list(dict.fromkeys(result["extracted_data"]))
    
    return result


async def analyze_chart_region(
    image_path: str,
    crop_box: Optional[tuple] = None
) -> Dict[str, Any]:
    """
    Analyze a specific chart/graph region in detail.
    
    Args:
        image_path: Path to the image
        crop_box: Optional (left, top, right, bottom) to crop specific region
        
    Returns:
        Detailed chart analysis
    """
    image = Image.open(image_path)
    
    if crop_box:
        image = image.crop(crop_box)
    
    model = genai.GenerativeModel(settings.gemini_model)
    response = await _call_gemini_vision(model, image, CHART_ANALYSIS_PROMPT)
    
    return {
        "chart_description": response,
        "chart_type": _detect_chart_type(response)
    }


def _detect_chart_type(description: str) -> str:
    """Detect chart type from description."""
    lower_desc = description.lower()
    
    if "bar" in lower_desc:
        return "bar_chart"
    elif "line" in lower_desc:
        return "line_chart"
    elif "pie" in lower_desc:
        return "pie_chart"
    elif "scatter" in lower_desc:
        return "scatter_plot"
    elif "histogram" in lower_desc:
        return "histogram"
    else:
        return "unknown"


async def batch_analyze_pages(
    image_paths: List[str],
    concurrency: int = 3
) -> List[Dict[str, Any]]:
    """
    Analyze multiple pages with controlled concurrency.
    
    Important for free tier - limits concurrent API calls.
    
    Args:
        image_paths: List of page image paths
        concurrency: Max concurrent API calls (default 3 for free tier)
        
    Returns:
        List of analysis results in order
    """
    import asyncio
    
    semaphore = asyncio.Semaphore(concurrency)
    
    async def analyze_with_semaphore(path: str) -> Dict[str, Any]:
        async with semaphore:
            return await analyze_page_image(path)
    
    tasks = [analyze_with_semaphore(path) for path in image_paths]
    results = await asyncio.gather(*tasks)
    
    return list(results)


def image_to_base64(image_path: str) -> str:
    """
    Convert image to base64 string for API transmission.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Base64 encoded string
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def create_page_thumbnail(
    image_path: str,
    max_size: tuple = (300, 400)
) -> bytes:
    """
    Create a thumbnail of a page for quick preview.
    
    Args:
        image_path: Path to full-size page image
        max_size: Maximum (width, height) for thumbnail
        
    Returns:
        PNG bytes of thumbnail
    """
    image = Image.open(image_path)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
