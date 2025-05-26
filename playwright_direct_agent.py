#!/usr/bin/env python3
"""
Direct Playwright Agent without MCP
Uses custom LangChain tools with Playwright for better browser control
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Any, Dict, Type
from dotenv import load_dotenv

# Playwright imports
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

# Set up logging
log_filename = f"playwright_direct_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Global browser instances - this ensures browser stays open across tool calls
browser_state = {
    "playwright": None,
    "browser": None,
    "context": None,
    "page": None
}

ENHANCED_SYSTEM_PROMPT = """You are an advanced web automation agent with access to Playwright browser tools. Follow these guidelines:

## CORE PRINCIPLES:
1. **Always launch browser first** - Use browser_launch before any navigation
2. **Keep the browser open** - Do NOT use browser_close unless explicitly requested
3. **Use proper sequencing** - Launch → Navigate → Wait → Screenshot → (Optional: Wait more)
4. **Be explicit about actions** - Explain each step you're taking

## STANDARD WORKFLOW:
1. Use `browser_launch` to start the browser (only once per session)
2. Use `browser_navigate` to go to the URL
3. Use `browser_wait` to wait for page load (3-5 seconds)
4. Use `browser_screenshot` to capture and verify the page
5. If asked to stay on page, use `browser_wait` with appropriate duration
6. Only use `browser_close` when explicitly requested to close

## TOOLS AVAILABLE:
- `browser_launch`: Start browser instance (call this first!)
- `browser_navigate`: Navigate to a URL
- `browser_wait`: Wait for specified seconds
- `browser_screenshot`: Take a screenshot and save it
- `browser_close`: Close browser (only when requested)

Remember: The browser will stay open between tool calls, so you only need to launch once per session."""

# Tool functions using @tool decorator for simpler definition
@tool
async def browser_launch(headless: bool = False) -> str:
    """Launch a browser instance. Call this before any other browser operations.
    
    Args:
        headless: Whether to run browser in headless mode (default: False)
    """
    try:
        if browser_state["browser"] is not None:
            return "Browser is already running."
        
        logger.info(f"Launching browser (headless={headless})")
        browser_state["playwright"] = await async_playwright().start()
        browser_state["browser"] = await browser_state["playwright"].chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--allow-running-insecure-content'
            ]
        )
        browser_state["context"] = await browser_state["browser"].new_context(
            viewport={'width': 1280, 'height': 720}
        )
        browser_state["page"] = await browser_state["context"].new_page()
        
        logger.info("Browser launched successfully")
        return "Browser launched successfully. Ready for navigation."
        
    except Exception as e:
        error_msg = f"Failed to launch browser: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
async def browser_navigate(url: str) -> str:
    """Navigate to a specified URL. Browser must be launched first.
    
    Args:
        url: The URL to navigate to
    """
    try:
        if browser_state["page"] is None:
            return "Browser not launched. Please use browser_launch first."
        
        logger.info(f"Navigating to: {url}")
        await browser_state["page"].goto(url, wait_until='networkidle')
        
        # Get page title for confirmation
        title = await browser_state["page"].title()
        
        logger.info(f"Successfully navigated to {url}, page title: {title}")
        return f"Successfully navigated to {url}. Page title: '{title}'. Browser is open and ready."
        
    except Exception as e:
        error_msg = f"Failed to navigate to {url}: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
async def browser_wait(seconds: int) -> str:
    """Wait for a specified number of seconds. Useful for keeping the browser open or waiting for page loads.
    
    Args:
        seconds: Number of seconds to wait
    """
    try:
        logger.info(f"Waiting for {seconds} seconds...")
        await asyncio.sleep(seconds)
        
        # Check if page is still available
        if browser_state["page"]:
            title = await browser_state["page"].title()
            logger.info(f"Wait completed. Browser still open with page: {title}")
            return f"Waited for {seconds} seconds. Browser is still open and active with page: '{title}'"
        else:
            return f"Waited for {seconds} seconds. Browser state unknown."
            
    except Exception as e:
        error_msg = f"Error during wait: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
async def browser_screenshot(filename: Optional[str] = None) -> str:
    """Take a screenshot of the current page and save it to file.
    
    Args:
        filename: Optional filename for screenshot (default: auto-generated)
    """
    try:
        if browser_state["page"] is None:
            return "Browser not launched or no page available."
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{timestamp}.png"
        
        logger.info(f"Taking screenshot: {filename}")
        await browser_state["page"].screenshot(path=filename, full_page=True)
        
        # Get current URL and title
        url = browser_state["page"].url
        title = await browser_state["page"].title()
        
        logger.info(f"Screenshot saved: {filename}")
        return f"Screenshot saved as '{filename}'. Current page: '{title}' at {url}. Browser remains open."
        
    except Exception as e:
        error_msg = f"Failed to take screenshot: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
async def browser_close() -> str:
    """Close the browser. Only use when explicitly requested to close."""
    try:
        if browser_state["browser"] is None:
            return "Browser is not running."
        
        logger.info("Closing browser...")
        
        if browser_state["context"]:
            await browser_state["context"].close()
        if browser_state["browser"]:
            await browser_state["browser"].close()
        if browser_state["playwright"]:
            await browser_state["playwright"].stop()
        
        # Reset state
        browser_state.update({
            "playwright": None,
            "browser": None,
            "context": None,
            "page": None
        })
        
        logger.info("Browser closed successfully")
        return "Browser closed successfully."
        
    except Exception as e:
        error_msg = f"Error closing browser: {str(e)}"
        logger.error(error_msg)
        return error_msg

async def main():
    logger.info("=== Starting Direct Playwright Agent ===")
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-001"),
        temperature=0.1
    )
    logger.info(f"Initialized LLM: {llm.model}")
    
    # Create custom tools using the @tool decorator approach
    tools = [
        browser_launch,
        browser_navigate,
        browser_wait,
        browser_screenshot,
        browser_close
    ]
    
    logger.info(f"Created {len(tools)} custom Playwright tools")
    
    # Print available tools
    print("\n=== Available Playwright Tools ===")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    print("===================================\n")
    
    # Create ReAct agent with custom tools
    agent = create_react_agent(llm, tools)
    logger.info("Direct Playwright ReAct agent created successfully")
    
    print(f"Logging to: {log_filename}")
    print("Direct Playwright Agent ready!")
    print("Type 'exit' or 'quit' to stop.")
    print("Note: Browser will stay open between commands until you explicitly close it.\n")
    
    session_count = 0
    
    try:
        while True:
            user = input("\nYou: ")
            if user.strip().lower() in {"exit", "quit"}:
                print("Goodbye!")
                logger.info("=== Session ended by user ===")
                break

            session_count += 1
            logger.info(f"=== Session {session_count} ===")
            
            try:
                logger.info(f"USER INPUT: {user}")
                
                # Create messages with system prompt
                messages = [
                    SystemMessage(content=ENHANCED_SYSTEM_PROMPT),
                    HumanMessage(content=user)
                ]
                
                logger.info("Invoking direct Playwright agent...")
                resp = await agent.ainvoke({"messages": messages})
                logger.info("Agent response received")
                
                # Get the final response
                final_message = resp["messages"][-1]
                reply = final_message.content if hasattr(final_message, 'content') else str(final_message)
                
                print(f"\nAgent: {reply}")
                logger.info(f"AGENT REPLY: {reply}")
                
                # Show intermediate steps
                if len(resp["messages"]) > 3:
                    print("\n--- Agent's Tool Calls ---")
                    for i, msg in enumerate(resp["messages"][2:-1], 1):
                        if hasattr(msg, 'content') and msg.content:
                            step_content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
                            print(f"Step {i}: {step_content}")
                            logger.info(f"TOOL STEP {i}: {msg.content}")
                    print("--- End of Tool Calls ---\n")
                            
            except Exception as e:
                error_msg = f"Error processing request: {e}"
                logger.error(error_msg)
                print(f"Error: {e}")
            
            logger.info(f"=== End of Session {session_count} ===\n")
            
    finally:
        # Cleanup on exit
        if browser_state["browser"]:
            logger.info("Cleaning up browser on exit...")
            try:
                if browser_state["context"]:
                    await browser_state["context"].close()
                if browser_state["browser"]:
                    await browser_state["browser"].close()
                if browser_state["playwright"]:
                    await browser_state["playwright"].stop()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 