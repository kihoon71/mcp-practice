from gettext import find
import time
from typing import Any, Dict, List, Optional, Callable
import json
import asyncio
import logging
import os
from openai import api_key, timeout
from langchain.chat_models import init_chat_model
from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate, ChatPromptTemplate
from .client import CustomClient
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv, find_dotenv


# Load environment variables from .env file
dot_env_path = find_dotenv()
if dot_env_path:
    load_dotenv(dotenv_path=dot_env_path)

# Set up logging
logging.basicConfig(
    filename='log/mcp-server.log',  # 원하는 경로와 파일명 지정
    filemode='a',  # 'a'는 append 모드, 'w'는 overwrite 모드
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG,  # 로깅 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    encoding='utf-8'  # 파일 인코딩 설정
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "ToolSelectServer",
    timeout=120
    )

OPEN_AI_API_KEY = os.getenv('OPENAI_API_KEY')

logger.info(f"OPENAI_API_KEY: {isinstance(OPEN_AI_API_KEY, str)}")

# CLAUD_CONFG = "C:\\Users\\SONKIHOON\\AppData\\Roaming\\Claude\\claude_desktop_config.json"
CLAUD_CONFG = os.getenv('CLAUDE_CONFIG_PATH')

logger.info(f"CLAUD_CONFG: {isinstance(CLAUD_CONFG, str)}")

llm = init_chat_model(
    model='gpt-4o',
    temperature=0.7,
    api_key=OPEN_AI_API_KEY,
    timeout=300
    )

async def get_tools_list() -> List[Dict[str, Any]]:
    """
    Get the list of tools from the configuration file.
    """
    # Load the configuration file
    with open(CLAUD_CONFG, "r") as f:
        claude_config = json.load(f)

    clients =  CustomClient(claude_config)

    await clients._get_tools()
    
    tools_list = clients.list_tools

    # log for debugging
    logger.info(f"Tools list: {len(tools_list)}")

    return tools_list

@mcp.tool(name="call_this_first", description="""
    This is the first tool to be called. It will chose the best tools for you and return the tool calling scinario to deal with the task.
    """)
async def call_this_first(task : str) -> List[Dict[str, Any]]:
    """
    This is the first tool to be called. It will chose the best tools for you and return the tool calling scinario to deal with the task.
    """
    
    tools_list = await get_tools_list()

    # log for debugging
    logger.info(f"Tools list: {len(tools_list)}")

    system_template = SystemMessagePromptTemplate.from_template(
        """You are a helpful assistant and a tool selector. You SHOULD check your a list of tools which is bound to you and their descriptions. 
        You will also be given a task. Your job is to select the best tool for the task and return the tool calling scinario for the task.
        write scinario simple and clear as possible. Just write the tool calling scinario, not a code!!.
        """)
    
    prompt = ChatPromptTemplate.from_messages([
        system_template,
        HumanMessagePromptTemplate.from_template("{task}")
    ])

    llm.bind_tools(
        tools=tools_list
    )

    prompt_llm = prompt | llm

    task_scinario = prompt_llm.invoke({
        "task": task
        })

    logger.info(f"Task: {task}")

    response = task_scinario.content
    
    logger.info(f"Task scinario: {response}")

    return response


def get_mcp() -> FastMCP:
    """
    Get the MCP server instance.
    """
    return mcp

if __name__ == "__main__":

    # Start the FastMCP server
    mcp.run(transport="stdio")
    