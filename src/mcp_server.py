import asyncio
import logging
from pathlib import Path

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from src.config import load_config
from src.exceptions import ConfigError
from src.pipeline import run_search, run_tailor

async def handle_list_tools(ctx, params: types.PaginatedRequestParams | None = None) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="search_jobs",
                description="Search for jobs based on configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "The user to search jobs for"}
                    },
                    "required": ["username"]
                }
            ),
            types.Tool(
                name="tailor_resume",
                description="Tailor a resume for a specific job",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "The user to tailor resume for"},
                        "job_slug": {"type": "string", "description": "The specific job slug to process. If omitted, all unprocessed jobs are processed"},
                        "force": {"type": "boolean", "description": "Force reprocessing even if already processed"},
                        "dry_run": {"type": "boolean", "description": "Dry run without executing actual API calls"}
                    },
                    "required": ["username"]
                }
            )
        ]
    )

async def handle_call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    name = params.name
    arguments = params.arguments if params.arguments else {}

    username = arguments.get("username")
    if not username:
        return types.CallToolResult(
            is_error=True,
            content=[types.TextContent(type="text", text="Error: username is required")]
        )

    user_dir = Path("users") / username
    config_path = user_dir / "config.yaml"

    try:
        config = load_config(config_path)
    except ConfigError as e:
        return types.CallToolResult(
            is_error=True,
            content=[types.TextContent(type="text", text=f"ConfigError: {e}")]
        )

    try:
        if name == "search_jobs":
            await asyncio.to_thread(run_search, config, user_dir)
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="Successfully completed job search")]
            )
        elif name == "tailor_resume":
            job_slug = arguments.get("job_slug")
            force = bool(arguments.get("force", False))
            dry_run = bool(arguments.get("dry_run", False))

            await asyncio.to_thread(run_tailor, config, user_dir, force, dry_run, job_slug)
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="Successfully completed tailor process")]
            )
        else:
            return types.CallToolResult(
                is_error=True,
                content=[types.TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        return types.CallToolResult(
            is_error=True,
            content=[types.TextContent(type="text", text=f"Error executing {name}: {e}")]
        )

server = Server("job-pipeline")

async def _handle_list_tools(params: types.PaginatedRequestParams | None = None) -> types.ListToolsResult:
    return await handle_list_tools()
server.add_request_handler("tools/list", types.PaginatedRequestParams, _handle_list_tools)

async def _handle_call_tool(params: types.CallToolRequestParams) -> types.CallToolResult:
    arguments = params.arguments if params.arguments else {}
    return await handle_call_tool(params.name, arguments)
server.add_request_handler("tools/call", types.CallToolRequestParams, _handle_call_tool)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(main())
