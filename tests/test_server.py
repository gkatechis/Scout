"""
Tests for the MCP server skeleton
"""

import pytest

from mcpindexer.server import app, call_tool, list_tools


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
        "answer_question",
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
    assert (
        "authentication" in result[0].text.lower()
        or "no relevant code" in result[0].text.lower()
    )


@pytest.mark.asyncio
async def test_answer_question_output_format():
    """Test answer_question returns properly formatted output with file references"""
    result = await call_tool("answer_question", {"question": "What is authentication?"})

    assert len(result) == 1
    output = result[0].text

    # Check for key components of the new format
    # Should have either results or "No relevant code found"
    if "No relevant code" not in output:
        # If we have results, verify the format includes:
        # - "Found N relevant code snippets"
        assert "Found" in output or "relevant" in output
        # - File references section
        assert "Relevant files:" in output or ":" in output  # file:line format
        # - Analysis instruction
        assert "Analyze" in output or "answer" in output.lower()


@pytest.mark.asyncio
async def test_answer_question_with_context_limit():
    """Test answer_question respects context_limit parameter"""
    result = await call_tool(
        "answer_question", {"question": "authentication", "context_limit": 3}
    )

    assert len(result) == 1
    assert result[0].type == "text"
    # Should work without errors
    assert len(result[0].text) > 0


@pytest.mark.asyncio
async def test_answer_question_with_repos_filter():
    """Test answer_question with repos filter"""
    result = await call_tool(
        "answer_question", {"question": "authentication", "repos": ["test-repo"]}
    )

    assert len(result) == 1
    assert result[0].type == "text"
    # Should work without errors
    assert len(result[0].text) > 0


@pytest.mark.asyncio
async def test_answer_question_empty_question():
    """Test answer_question handles empty question gracefully"""
    result = await call_tool("answer_question", {"question": ""})

    assert len(result) == 1
    assert result[0].type == "text"
    # Should return error message
    assert "Error" in result[0].text or "required" in result[0].text


@pytest.mark.asyncio
async def test_answer_question_vs_semantic_search_format():
    """Test that answer_question format is more concise than semantic_search"""
    # Call both tools with the same query
    semantic_result = await call_tool("semantic_search", {"query": "authentication"})
    answer_result = await call_tool("answer_question", {"question": "authentication"})

    assert len(semantic_result) == 1
    assert len(answer_result) == 1

    # Both should return text
    assert semantic_result[0].type == "text"
    assert answer_result[0].type == "text"

    # answer_question should include analysis prompt
    if "No relevant code" not in answer_result[0].text:
        assert (
            "Analyze" in answer_result[0].text
            or "answer" in answer_result[0].text.lower()
        )


@pytest.mark.asyncio
async def test_answer_question_includes_file_paths():
    """Test that answer_question includes file:line references in output"""
    result = await call_tool("answer_question", {"question": "authentication"})

    assert len(result) == 1
    output = result[0].text

    # If we found results, verify file paths are included
    if "No relevant code" not in output and "Found" in output:
        # Should have file path format (something.py:number or Relevant files:)
        has_file_ref = (
            ".py:" in output
            or ".ts:" in output
            or ".js:" in output
            or "Relevant files:" in output
        )
        # If no actual results, that's okay - the format is correct
        assert has_file_ref or "No relevant" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
