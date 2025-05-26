# playwright_react_agent.py
import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# MCP / LangGraph imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

# Set up logging to both console and file
log_filename = f"mcp_agent_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()  # loads GOOGLE_API_KEY if set

ENHANCED_SYSTEM_PROMPT = """You are an advanced web automation agent with access to Playwright browser tools. Follow these guidelines:

## CORE PRINCIPLES:
1. **Always be explicit about your actions** - Explain what you're doing step by step
2. **Keep the browser open** - When opening websites, take a screenshot to verify success before proceeding
3. **Handle popups and consent dialogs** - Look for consent buttons, cookie banners, and close any blocking dialogs
4. **Use proper waiting** - Wait for pages to load completely before interacting
5. **Document your actions** - Take screenshots to show your progress

## STANDARD WORKFLOW FOR OPENING WEBSITES:
1. Use `browser_navigate` to go to the URL
2. Use `browser_wait_for` to wait for page load (3-5 seconds)
3. Use `browser_snapshot` or `browser_take_screenshot` to capture the current state
4. Look for consent dialogs, cookie banners, or popups and handle them with `browser_click`
5. If asked to stay on a page, use `browser_wait_for` with appropriate duration
6. Only use `browser_close` when explicitly asked to close

## REQUIRED TOOLS FOR BASIC OPERATIONS:
- `browser_navigate`: For opening websites (ALWAYS use this first)
- `browser_wait_for`: For waiting and keeping browser open
- `browser_take_screenshot`: For visual confirmation
- `browser_snapshot`: For better page analysis
- `browser_click`: For interacting with buttons/consent dialogs
- `browser_close`: Only when explicitly requested

## CONSENT DIALOG HANDLING:
- Look for text like "Accept", "Accept All", "I Agree", "Continue", "OK"
- Common selectors: buttons with "accept", "agree", "continue", "ok" text
- If you see cookie banners, always accept them first

## ERROR HANDLING:
- If a tool fails, explain what happened and try an alternative approach
- If browser closes unexpectedly, navigate again and continue
- Always verify success with screenshots

## COMMUNICATION:
- Explain each step you're taking
- Report what you see on the page
- Confirm successful completion of tasks
- Ask for clarification if instructions are unclear

Remember: Your goal is to successfully complete web automation tasks while keeping the user informed of your progress."""

async def main():
    logger.info("=== Starting Enhanced MCP Agent Session ===")
    
    # 1) Instantiate Google Gemini chat model
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-001"),
        temperature=0.1
    )
    logger.info(f"Initialized LLM: {llm.model}")

    # 2) Point to the Playwright MCP server with correct transport configuration
    mcp_servers = {
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest"],
            "transport": "stdio",
            "environment": {
                "PLAYWRIGHT_HEADLESS": "false"
            }
        }
    }
    logger.info(f"MCP Server Configuration: {mcp_servers}")

    logger.info("Initializing MCP client...")
    
    #3) Initialize MCP client
    client = MultiServerMCPClient(mcp_servers)
    tools = await client.get_tools()
    
    logger.info(f"Available tools: {[tool.name for tool in tools]}")
    
    #logs 
    tools_info = "\n=== Available MCP Tools ==="
    for tool in tools:
        tools_info += f"\n- {tool.name}: {tool.description}"
    tools_info += "\n==========================="
    
    print(tools_info)
    logger.info(tools_info)

    #Agent
    agent = create_react_agent(llm, tools)
    logger.info("Enhanced ReAct agent created successfully")

    
    print(f"\nLogging all interactions to: {log_filename}")
    print("Enhanced MCP Agent ready!")
    print("The agent will follow structured web automation workflows.")
    print("Type 'exit' or 'quit' to stop.")
    
    session_count = 0
    while True:
        user = input("\nYou: ")
        if user.strip().lower() in {"exit", "quit"}:
            print("Goodbye!")
            logger.info("=== Session ended by user ===")
            break

        session_count += 1
        logger.info(f"=== Session {session_count} ===")
        
        try:
            # Use proper message format for LangChain with system prompt
            from langchain_core.messages import HumanMessage
            
            logger.info(f"USER INPUT: {user}")
            
            # Create messages with system prompt for this session
            messages = [
                SystemMessage(content=ENHANCED_SYSTEM_PROMPT),
                HumanMessage(content=user)
            ]
            
            # Log before invoking agent
            logger.info("Invoking enhanced agent with system prompt...")
            resp = await agent.ainvoke({"messages": messages})
            logger.info("Agent response received")
            
            # Log all messages in the response
            logger.info(f"Total messages in response: {len(resp['messages'])}")
            for i, msg in enumerate(resp["messages"]):
                msg_type = type(msg).__name__
                content = getattr(msg, 'content', str(msg))
                logger.info(f"Message {i+1} ({msg_type}): {content}")
            
            # Get the final response
            final_message = resp["messages"][-1]
            reply = final_message.content if hasattr(final_message, 'content') else str(final_message)
            
            print(f"\nAgent: {reply}")
            logger.info(f"AGENT REPLY: {reply}")
            
            # Show and log intermediate steps if available
            if len(resp["messages"]) > 3:  # More than system + user + final response
                reasoning_steps = "\n--- Agent's reasoning and tool calls ---"
                for i, msg in enumerate(resp["messages"][2:-1], 1):  # Skip system and user messages
                    if hasattr(msg, 'content') and msg.content:
                        step_content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                        reasoning_steps += f"\nStep {i}: {step_content}"
                        logger.info(f"REASONING STEP {i}: {msg.content}")
                reasoning_steps += "\n--- End of reasoning ---\n"
                print(reasoning_steps)
                        
        except Exception as e:
            error_msg = f"Error processing request: {e}"
            logger.error(error_msg)
            print(f"Error: {e}")
        
        logger.info(f"=== End of Session {session_count} ===\n")

if __name__ == "__main__":
    asyncio.run(main())
