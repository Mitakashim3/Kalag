"""
Kalag Input Sanitization
Protects against XSS, SQL Injection, and Prompt Injection attacks
"""

import re
import html
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PromptInjectionError(Exception):
    """Raised when prompt injection is detected"""
    pass


# ===========================================
# Prompt Injection Detection Patterns
# ===========================================

# Common prompt injection patterns
INJECTION_PATTERNS = [
    # Direct instruction override attempts
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    r"override\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    
    # Role manipulation attempts
    r"you\s+are\s+now\s+(a|an)\s+",
    r"pretend\s+(you\s+are|to\s+be)\s+",
    r"act\s+as\s+(a|an|if)\s+",
    r"roleplay\s+as\s+",
    r"switch\s+(to|into)\s+.*(mode|persona|character)",
    
    # System prompt extraction attempts
    r"(reveal|show|display|print|output)\s+(your|the)\s+(system\s+)?(prompt|instructions?)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?)",
    r"repeat\s+(your|the)\s+(initial|system|original)\s+(prompt|instructions?)",
    
    # Jailbreak attempts
    r"(dan|dude|evil|jailbreak)\s*mode",
    r"developer\s*mode\s*(enabled|on|activated)",
    r"bypass\s+(content\s+)?(filter|restriction|safety)",
    
    # Code injection via prompts
    r"\{\{.*\}\}",  # Template injection
    r"\$\{.*\}",    # Variable injection
    r"<script.*?>",  # Script injection
    
    # Delimiter-based attacks
    r"---+\s*(new|system|admin|ignore)",
    r"###\s*(new|system|admin|ignore)",
    r"\[system\]",
    r"\[admin\]",
    r"\[instruction\]",
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> tuple[bool, Optional[str]]:
    """
    Detect potential prompt injection attacks in user input.
    
    Args:
        text: User-provided text to analyze
        
    Returns:
        Tuple of (is_injection_detected, matched_pattern)
    """
    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.warning(f"Prompt injection detected: {match.group()}")
            return True, match.group()
    
    return False, None


def sanitize_for_prompt(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user input before including in LLM prompts.
    
    This function:
    1. Checks for prompt injection patterns
    2. Escapes special characters
    3. Limits length to prevent context overflow
    4. Normalizes whitespace
    
    Args:
        text: Raw user input
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text safe for prompt inclusion
        
    Raises:
        PromptInjectionError: If injection attempt detected
    """
    # Check for injection attempts
    is_injection, matched = detect_prompt_injection(text)
    if is_injection:
        raise PromptInjectionError(
            f"Potential prompt injection detected. Please rephrase your query."
        )
    
    # Normalize whitespace
    sanitized = " ".join(text.split())
    
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized


def sanitize_html(text: str) -> str:
    """
    Escape HTML special characters to prevent XSS.
    
    Args:
        text: Raw text
        
    Returns:
        HTML-escaped text
    """
    return html.escape(text)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove path separators
    safe_name = re.sub(r'[/\\]', '', filename)
    
    # Remove null bytes
    safe_name = safe_name.replace('\x00', '')
    
    # Remove leading dots (hidden files)
    safe_name = safe_name.lstrip('.')
    
    # Only allow safe characters
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', safe_name)
    
    # Limit length
    if len(safe_name) > 255:
        name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
        safe_name = name[:250] + ('.' + ext if ext else '')
    
    return safe_name or "unnamed"


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query for database and vector store operations.
    
    Args:
        query: User search query
        
    Returns:
        Sanitized query
    """
    # First check for prompt injection
    sanitized = sanitize_for_prompt(query, max_length=1000)
    
    # Remove SQL-like patterns (extra paranoid)
    sql_patterns = [
        r";\s*drop\s+",
        r";\s*delete\s+",
        r";\s*update\s+",
        r";\s*insert\s+",
        r"'\s*or\s+'",
        r"'\s*and\s+'",
        r"--",
        r"/\*",
        r"\*/",
    ]
    
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, " ", sanitized, flags=re.IGNORECASE)
    
    return sanitized
