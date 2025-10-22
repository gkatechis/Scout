"""
Tests for the MCP server skeleton
"""
import pytest
from mcpindexer.server import app, list_tools, call_tool


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the MCP server initializes correctly"""
    assert app is not None
    assert app.name == "mcpindexer"


@pytest.mark.asyncio
async def test_list_tools():
    """Test that all expected tools are registered"""
    tools = await list_tools()

    assert len(tools) == 13  # We defined 13 tools

    tool_names = [tool.name for tool in tools]
    expected_tools = [
        "semantic_search",
        "find_definition",
        "find_references",
        "find_related_code",
        "get_repo_stats",
        "reindex_repo",
        "add_repo_to_stack",
        "remove_repo",
        "list_repos",
        "get_cross_repo_dependencies",
        "suggest_missing_repos",
        "get_stack_status",
        "answer_question"
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Tool {expected_tool} not found"


@pytest.mark.asyncio
async def test_semantic_search_schema():
    """Test semantic_search tool has correct schema"""
    tools = await list_tools()
    semantic_search = next(t for t in tools if t.name == "semantic_search")

    assert semantic_search is not None
    assert "query" in semantic_search.inputSchema["properties"]
    assert "repos" in semantic_search.inputSchema["properties"]
    assert "language" in semantic_search.inputSchema["properties"]
    assert "limit" in semantic_search.inputSchema["properties"]
    assert "query" in semantic_search.inputSchema["required"]


@pytest.mark.asyncio
async def test_find_definition_schema():
    """Test find_definition tool has correct schema"""
    tools = await list_tools()
    find_definition = next(t for t in tools if t.name == "find_definition")

    assert find_definition is not None
    assert "symbol" in find_definition.inputSchema["properties"]
    assert "symbol" in find_definition.inputSchema["required"]


@pytest.mark.asyncio
async def test_call_semantic_search():
    """Test calling semantic_search tool (placeholder)"""
    result = await call_tool("semantic_search", {"query": "authentication logic"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "authentication logic" in result[0].text


@pytest.mark.asyncio
async def test_call_find_definition():
    """Test calling find_definition tool (placeholder)"""
    result = await call_tool("find_definition", {"symbol": "authenticate_user"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "authenticate_user" in result[0].text


@pytest.mark.asyncio
async def test_call_find_references():
    """Test calling find_references tool (placeholder)"""
    result = await call_tool("find_references", {"symbol": "User"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "User" in result[0].text


@pytest.mark.asyncio
async def test_call_reindex_repo():
    """Test calling reindex_repo tool (placeholder)"""
    result = await call_tool("reindex_repo", {"repo_name": "test-repo"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "test-repo" in result[0].text


@pytest.mark.asyncio
async def test_call_unknown_tool():
    """Test calling an unknown tool"""
    result = await call_tool("nonexistent_tool", {})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Unknown tool" in result[0].text


@pytest.mark.asyncio
async def test_all_tools_callable():
    """Test that all registered tools can be called"""
    tools = await list_tools()

    for tool in tools:
        # Create minimal valid arguments
        args = {}
        for required_param in tool.inputSchema.get("required", []):
            args[required_param] = "test_value"

        result = await call_tool(tool.name, args)
        assert len(result) > 0
        assert result[0].type == "text"


@pytest.mark.asyncio
async def test_call_get_cross_repo_dependencies():
    """Test calling get_cross_repo_dependencies tool"""
    result = await call_tool("get_cross_repo_dependencies", {})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "dependencies" in result[0].text or "No cross-repository" in result[0].text


@pytest.mark.asyncio
async def test_call_suggest_missing_repos():
    """Test calling suggest_missing_repos tool"""
    result = await call_tool("suggest_missing_repos", {})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Suggested" in result[0].text or "No missing" in result[0].text


@pytest.mark.asyncio
async def test_call_get_stack_status():
    """Test calling get_stack_status tool"""
    result = await call_tool("get_stack_status", {})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Stack Status" in result[0].text or "Total Repositories" in result[0].text


@pytest.mark.asyncio
async def test_answer_question_schema():
    """Test answer_question tool has correct schema"""
    tools = await list_tools()
    answer_question = next(t for t in tools if t.name == "answer_question")

    assert answer_question is not None
    assert "question" in answer_question.inputSchema["properties"]
    assert "repos" in answer_question.inputSchema["properties"]
    assert "context_limit" in answer_question.inputSchema["properties"]
    assert "question" in answer_question.inputSchema["required"]


@pytest.mark.asyncio
async def test_call_answer_question():
    """Test calling answer_question returns relevant context"""
    result = await call_tool("answer_question", {"question": "What is authentication?"})

    assert len(result) == 1
    assert result[0].type == "text"
    # Should return either results or "No relevant code found"
    assert "authentication" in result[0].text.lower() or "no relevant code" in result[0].text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
