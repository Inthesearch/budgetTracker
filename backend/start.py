#!/usr/bin/env python3
"""
Budget Tracker Backend - Startup Script
Sets event loop policy for Windows before starting uvicorn
"""

import sys
import asyncio
import os

# Fix for Windows: psycopg3 requires SelectorEventLoop, not ProactorEventLoop
# This MUST be set before any async operations or imports
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Now import and run uvicorn
if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level="info"
    )

