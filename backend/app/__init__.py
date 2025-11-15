# Budget Tracker Backend

# Fix for Windows: psycopg3 requires SelectorEventLoop, not ProactorEventLoop
# Set this at the very beginning of the app package to ensure it's set before any async operations
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 