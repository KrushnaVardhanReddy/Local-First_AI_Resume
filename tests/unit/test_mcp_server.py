import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.mcp_server import handle_list_tools, handle_call_tool
import mcp.types as types
from src.exceptions import ValidationError
from src.tailor_resume import _fetch_mcp_resume, _read_base_resume
from src.config import AppConfig, SearchConfig

@pytest.mark.asyncio
async def test_handle_list_tools():
    ctx = MagicMock()
    result = await handle_list_tools(ctx, None)
    assert isinstance(result, types.ListToolsResult)
    tool_names = [t.name for t in result.tools]
    assert "search_jobs" in tool_names
    assert "tailor_resume" in tool_names

@pytest.mark.asyncio
async def test_handle_call_tool_missing_username():
    ctx = MagicMock()
    params = types.CallToolRequestParams(name="search_jobs", arguments={})
    result = await handle_call_tool(ctx, params)
    assert result.is_error is True
    assert "username is required" in result.content[0].text

@pytest.mark.asyncio
@patch("src.mcp_server.load_config")
@patch("src.mcp_server.run_search")
async def test_handle_call_tool_search_jobs(mock_run_search, mock_load_config):
    ctx = MagicMock()
    params = types.CallToolRequestParams(name="search_jobs", arguments={"username": "testuser"})

    mock_config = MagicMock()
    mock_load_config.return_value = mock_config

    result = await handle_call_tool(ctx, params)

    assert result.is_error is not True
    assert "Successfully completed job search" in result.content[0].text
    mock_run_search.assert_called_once()
    assert mock_run_search.call_args[0][0] == mock_config

@pytest.mark.asyncio
@patch("src.mcp_server.load_config")
@patch("src.mcp_server.run_tailor")
async def test_handle_call_tool_tailor_resume(mock_run_tailor, mock_load_config):
    ctx = MagicMock()
    params = types.CallToolRequestParams(
        name="tailor_resume",
        arguments={"username": "testuser", "job_slug": "my-job", "force": True, "dry_run": False}
    )

    mock_config = MagicMock()
    mock_load_config.return_value = mock_config

    result = await handle_call_tool(ctx, params)

    assert result.is_error is not True
    assert "Successfully completed tailor process" in result.content[0].text
    mock_run_tailor.assert_called_once()
    # run_tailor args: config, user_dir, force, dry_run, job_slug
    args = mock_run_tailor.call_args[0]
    assert args[0] == mock_config
    assert args[2] is True # force
    assert args[3] is False # dry_run
    assert args[4] == "my-job" # job_slug

@patch("src.tailor_resume.asyncio.run")
def test_read_base_resume_mcp(mock_asyncio_run):
    config = AppConfig(
        provider="test",
        model="test",
        base_resume="base_resume.md",
        output_dir="output",
        search=SearchConfig(keywords="test", location="test", remote=False, results_wanted=1),
        mcp_base_resume={"command": "echo", "args": ["hello"], "resource_uri": "test://uri"}
    )
    user_dir = Path("users/test")
    mock_asyncio_run.return_value = "mcp_content"

    result = _read_base_resume(config, user_dir)
    assert result == "mcp_content"
    mock_asyncio_run.assert_called_once()
