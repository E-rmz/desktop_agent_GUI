#!/usr/bin/env python3
"""
Test script for the enhanced Playwright agent with OmniParser and PyAutoGUI
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright_direct_agent import (
    browser_launch, 
    browser_navigate, 
    browser_wait, 
    browser_screenshot,
    omniparser_analyze,
    pyautogui_click,
    pyautogui_type,
    browser_close
)

async def test_tools():
    """Test all enhanced tools individually"""
    print("=== Testing Enhanced Agent Tools ===\n")
    
    # Test 1: Browser Launch
    print("1. Testing browser_launch...")
    result = await browser_launch(headless=False)
    print(f"Result: {result}\n")
    
    # Test 2: Browser Navigate  
    print("2. Testing browser_navigate...")
    result = await browser_navigate("https://www.google.com")
    print(f"Result: {result}\n")
    
    # Test 3: Browser Wait
    print("3. Testing browser_wait (5 seconds)...")
    result = await browser_wait(5)
    print(f"Result: {result}\n")
    
    # Test 4: Browser Screenshot
    print("4. Testing browser_screenshot...")
    result = await browser_screenshot("test_browser_screenshot.png")
    print(f"Result: {result}\n")
    
    # Test 5: OmniParser Analysis
    print("5. Testing omniparser_analyze...")
    try:
        result = await omniparser_analyze("test_omniparser_screenshot.png")
        print(f"Result: {result[:500]}..." if len(result) > 500 else result)
        print()
    except Exception as e:
        print(f"OmniParser test failed: {e}\n")
    
    # Test 6: PyAutoGUI Click (safe coordinates - middle of typical screen)
    print("6. Testing pyautogui_click (safe coordinates)...")
    try:
        result = await pyautogui_click(640, 360)  # Middle of 1280x720 screen
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"PyAutoGUI click test failed: {e}\n")
    
    # Test 7: PyAutoGUI Type
    print("7. Testing pyautogui_type...")
    try:
        result = await pyautogui_type("test text", interval=0.05)
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"PyAutoGUI type test failed: {e}\n")
    
    # Test 8: Browser Close
    print("8. Testing browser_close...")
    result = await browser_close()
    print(f"Result: {result}\n")
    
    print("=== All tests completed ===")

if __name__ == "__main__":
    asyncio.run(test_tools()) 