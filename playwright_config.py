#!/usr/bin/env python3
"""
Custom Playwright MCP server launcher with better browser configuration for macOS
"""
import asyncio
import sys
import json
import os
from playwright.async_api import async_playwright

async def main():
    """Main MCP server function with custom Playwright configuration"""
    
    # Read MCP requests from stdin
    async def handle_mcp_request():
        async with async_playwright() as p:
            # Launch browser with non-headless mode for macOS
            browser = await p.chromium.launch(
                headless=False,  # Keep browser visible
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--allow-running-insecure-content',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Keep a context and page open
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # Process stdin for MCP requests
                while True:
                    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break
                        
                    try:
                        request = json.loads(line.strip())
                        
                        if request.get('method') == 'tools/call' and request.get('params', {}).get('name') == 'navigate':
                            url = request['params']['arguments'].get('url', 'https://yahoo.com')
                            await page.goto(url, wait_until='networkidle')
                            
                            # Keep the page open for a few seconds
                            await asyncio.sleep(3)
                            
                            response = {
                                'jsonrpc': '2.0',
                                'id': request.get('id'),
                                'result': {
                                    'content': [
                                        {
                                            'type': 'text',
                                            'text': f'Successfully navigated to {url} and page is now open'
                                        }
                                    ]
                                }
                            }
                            print(json.dumps(response))
                            sys.stdout.flush()
                            
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        error_response = {
                            'jsonrpc': '2.0',
                            'id': request.get('id') if 'request' in locals() else None,
                            'error': {
                                'code': -1,
                                'message': str(e)
                            }
                        }
                        print(json.dumps(error_response))
                        sys.stdout.flush()
                        
            finally:
                await browser.close()
    
    await handle_mcp_request()

if __name__ == '__main__':
    asyncio.run(main()) 