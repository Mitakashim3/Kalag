"""
Kalag Security Headers Middleware
Implements security headers equivalent to Helmet.js

These headers protect against:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME sniffing
- Information disclosure
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    Equivalent to Express.js Helmet middleware.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # ===========================================
        # Core Security Headers
        # ===========================================
        # Note: Only set headers if they don't already exist
        # This prevents overwriting CORS and other important headers
        
        # Prevent MIME type sniffing
        if "X-Content-Type-Options" not in response.headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking by disabling framing
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable browser XSS filter (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Prevent browsers from DNS prefetching
        response.headers["X-DNS-Prefetch-Control"] = "off"
        
        # Disable client-side caching for sensitive data
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # ===========================================
        # Content Security Policy (CSP)
        # ===========================================
        # Strict CSP to prevent XSS and data injection
        csp_directives = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",  # Tailwind needs inline styles
            "img-src 'self' data: blob:",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # ===========================================
        # HTTPS Enforcement (Production Only)
        # ===========================================
        # Uncomment in production with HTTPS
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # ===========================================
        # Permissions Policy (formerly Feature-Policy)
        # ===========================================
        # Disable unnecessary browser features
        permissions = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        return response
