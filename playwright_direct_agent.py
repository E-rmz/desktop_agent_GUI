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
import json
import shutil

# Playwright imports
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

# PyAutoGUI and OmniParser imports
import pyautogui
from gradio_client import Client, handle_file

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

ENHANCED_SYSTEM_PROMPT = """You are an advanced web automation agent with access to Playwright browser tools, screen analysis, and system interaction capabilities. Follow these guidelines:

## CORE PRINCIPLES:
1. **Always launch browser first** - Use browser_launch before any navigation
2. **Keep the browser open** - Do NOT use browser_close unless explicitly requested
3. **Use proper sequencing** - Launch → Navigate → Wait → Screenshot → (Optional: Wait more)
4. **Wait 10 seconds between steps** - Always use browser_wait(10) between major actions
5. **Use OmniParser for screen analysis** - Use omniparser_analyze to understand screen elements
6. **STOP when task is complete** - Do not continue executing tools after completing the requested task
7. **Be explicit about completion** - When finished, clearly state the task is complete

## STANDARD WORKFLOW:
1. Use `browser_launch` to start the browser (only once per session)
2. Use `browser_navigate` to go to the URL
3. Use `browser_wait(10)` to wait for page load
4. Use `browser_screenshot` to capture the page
5. Use `omniparser_analyze` to analyze screen elements and get coordinates
6. Use `pyautogui_click` or `pyautogui_type` for system-level interactions
7. Always wait 10 seconds between major steps using `browser_wait(10)`
8. **STOP and provide final response when the requested task is complete**
9. Only use `browser_close` when explicitly requested to close

## STOPPING CONDITIONS:
- After completing all requested actions, provide a summary and STOP
- Do not continue executing tools unless there are more specific instructions
- If a screenshot is the final requested action, take it and STOP
- If typing/clicking is the final action, do it and STOP

## TOOLS AVAILABLE:
- `browser_launch`: Start browser instance (call this first!)
- `browser_navigate`: Navigate to a URL
- `browser_wait`: Wait for specified seconds (use 10 for step delays)
- `browser_screenshot`: Take a screenshot and save it
- `omniparser_analyze`: Analyze screen and get clickable elements
- `pyautogui_click`: Click at specific (x,y) coordinates
- `pyautogui_type`: Type text at current cursor position
- `browser_close`: Close browser (only when requested)

Remember: Always wait 10 seconds between major steps for stability, and STOP when the task is complete."""

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
    """Wait for a specified number of seconds. Useful for keeping the browser open or waiting for page loads. Use 10 seconds for standard step delays.
    
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

@tool
async def omniparser_analyze(custom_filename: Optional[str] = None) -> str:
    """Take a screenshot of the entire screen and analyze it with OmniParser to identify clickable elements and their coordinates.
    
    Args:
        custom_filename: Optional custom filename for the analysis screenshot
    """
    try:
        logger.info("Starting OmniParser screen analysis...")
        
        # Take screenshot of entire screen
        screenshot = pyautogui.screenshot()
        
        # Save to a local file
        if custom_filename:
            screenshot_path = custom_filename
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"omniparser_screenshot_{timestamp}.png"
        
        screenshot.save(screenshot_path)
        logger.info(f"Screenshot saved to: {screenshot_path}")
        
        # Connect to OmniParser
        logger.info("Connecting to OmniParser-v2 space...")
        client = Client("microsoft/OmniParser-v2")
        
        # Process the screenshot
        logger.info("Processing screenshot with OmniParser...")
        result = client.predict(
            image_input=handle_file(screenshot_path),
            box_threshold=0.05,
            iou_threshold=0.1,
            use_paddleocr=True,
            imgsz=640,
            api_name="/process"
        )
        
        logger.info("OmniParser processing completed successfully!")
        
        response_text = "OmniParser Analysis Results:\n" + "="*50 + "\n"
        
        # Handle different result formats
        if isinstance(result, (list, tuple)):
            # Extract the processed image (first element)
            if len(result) >= 1 and result[0]:
                processed_image_path = result[0]
                
                if os.path.exists(processed_image_path):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_filename = f"omniparser_result_{timestamp}.webp"
                    shutil.copy2(processed_image_path, output_filename)
                    response_text += f"Processed image saved to: {output_filename}\n"
                    
                    file_size = os.path.getsize(output_filename)
                    response_text += f"File size: {file_size} bytes\n"
                else:
                    response_text += f"Warning: Processed image file not found at: {processed_image_path}\n"
                    
            # Extract metadata/text results (second element)
            if len(result) >= 2 and result[1]:
                response_text += f"\nDetected Elements and Coordinates:\n{result[1]}\n"
                
                # Save text results to a file
                if isinstance(result[1], str):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    text_filename = f"omniparser_text_result_{timestamp}.txt"
                    with open(text_filename, "w", encoding="utf-8") as f:
                        f.write(result[1])
                    response_text += f"Text results saved to: {text_filename}\n"
                    
        elif isinstance(result, dict):
            response_text += json.dumps(result, indent=2)
        else:
            response_text += str(result)
        
        response_text += "\nUse the coordinates from this analysis with pyautogui_click to interact with elements."
        logger.info("OmniParser analysis completed successfully")
        return response_text
        
    except Exception as e:
        error_msg = f"OmniParser analysis failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool
async def pyautogui_click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """Click at specific screen coordinates using PyAutoGUI.
    
    Args:
        x: X coordinate to click
        y: Y coordinate to click  
        button: Mouse button to use (left, right, middle)
        clicks: Number of clicks (default: 1)
    """
    try:
        logger.info(f"Clicking at coordinates ({x}, {y}) with {button} button, {clicks} clicks")
        
        # Ensure coordinates are within screen bounds
        screen_width, screen_height = pyautogui.size()
        if x < 0 or x > screen_width or y < 0 or y > screen_height:
            return f"Error: Coordinates ({x}, {y}) are outside screen bounds ({screen_width}x{screen_height})"
        
        # Perform the click
        pyautogui.click(x, y, button=button, clicks=clicks)
        
        response = f"Successfully clicked at ({x}, {y}) using {button} button ({clicks} clicks). Screen size: {screen_width}x{screen_height}"
        logger.info(response)
        return response
        
    except Exception as e:
        error_msg = f"Failed to click at ({x}, {y}): {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool 
async def pyautogui_type(text: str, interval: float = 0.1) -> str:
    """Type text at the current cursor position using PyAutoGUI.
    
    Args:
        text: Text to type
        interval: Delay between keystrokes in seconds (default: 0.1)
    """
    try:
        logger.info(f"Typing text: '{text}' with interval {interval}s")
        
        # Type the text
        pyautogui.typewrite(text, interval=interval)
        
        response = f"Successfully typed: '{text}' (length: {len(text)} characters)"
        logger.info(response)
        return response
        
    except Exception as e:
        error_msg = f"Failed to type text '{text}': {str(e)}"
        logger.error(error_msg)
        return error_msg

async def main():
    logger.info("=== Starting Enhanced Playwright Agent with OmniParser ===")
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-001"),
        temperature=0.1
    )
    logger.info(f"Initialized LLM: {llm.model}")
    
    # Create enhanced tools including OmniParser and PyAutoGUI
    tools = [
        browser_launch,
        browser_navigate,
        browser_wait,
        browser_screenshot,
        omniparser_analyze,
        pyautogui_click,
        pyautogui_type,
        browser_close
    ]
    
    logger.info(f"Created {len(tools)} enhanced tools (Browser + OmniParser + PyAutoGUI)")
    
    # Print available tools
    print("\n=== Available Enhanced Tools ===")
    print("BROWSER TOOLS:")
    print("- browser_launch: Start browser instance")
    print("- browser_navigate: Navigate to a URL") 
    print("- browser_wait: Wait for specified seconds (use 10 for step delays)")
    print("- browser_screenshot: Take a screenshot")
    print("- browser_close: Close browser")
    print("\nANALYSIS TOOLS:")
    print("- omniparser_analyze: Analyze screen and get clickable elements")
    print("\nINTERACTION TOOLS:")
    print("- pyautogui_click: Click at (x,y) coordinates")
    print("- pyautogui_type: Type text at cursor position")
    print("=====================================\n")
    
    # Create ReAct agent with enhanced tools and increased recursion limit
    agent = create_react_agent(
        llm, 
        tools, 
        config={
            "recursion_limit": 50,  # Increased from default 25 to 50
            "configurable": {
                "thread_id": "enhanced_agent"
            }
        }
    )
    logger.info("Enhanced Playwright + OmniParser ReAct agent created successfully")
    
    print(f"Logging to: {log_filename}")
    print("Enhanced Playwright Agent with OmniParser ready!")
    print("Features: Browser automation + Screen analysis + System interaction")
    print("Type 'exit' or 'quit' to stop.")
    print("Note: Agent will wait 10 seconds between major steps for stability.\n")
    
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
                
                # Create messages with enhanced system prompt
                messages = [
                    SystemMessage(content=ENHANCED_SYSTEM_PROMPT),
                    HumanMessage(content=user)
                ]
                
                logger.info("Invoking enhanced Playwright agent...")
                resp = await agent.ainvoke(
                    {"messages": messages},
                    config={
                        "recursion_limit": 50,  # Set recursion limit per invocation
                        "configurable": {
                            "thread_id": f"session_{session_count}"
                        }
                    }
                )
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
                
                # If recursion limit hit, suggest shorter commands
                if "recursion_limit" in str(e).lower():
                    print("\n💡 Tip: Try breaking your request into smaller, more specific tasks.")
                    print("Example: Instead of 'do everything', try 'open google.com and take a screenshot'")
            
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