import asyncio

# Sets the asyncio event loop policy
# This is a workaround for a known issue on Windows, especially when using libraries like supabase-py within a GUI application
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())