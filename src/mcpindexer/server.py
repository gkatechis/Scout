"""
MCP Server for semantic code search and indexing

This server implements the Model Context Protocol, making code search
available to any MCP-compatible LLM client.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.types import TextContent, Tool

from mcpindexer.embeddings import EmbeddingStore
from mcpindexer.indexer import MultiRepoIndexer

# Global state for the server
_multi_indexer: Optional[MultiRepoIndexer] = None
_embedding_store: Optional[EmbeddingStore] = None


def get_indexer() -> MultiRepoIndexer:
    """Get or create the multi-repo indexer"""
    global _multi_indexer, _embedding_store

    if _multi_indexer is None:
        # Initialize embedding store
        db_path = os.getenv(
            "MCP_INDEXER_DB_PATH", os.path.expanduser("~/.mcpindexer/db")
        )
        _embedding_store = EmbeddingStore(
            db_path=db_path, collection_name="mcp_code_index"
        )
        _multi_indexer = MultiRepoIndexer(embedding_store=_embedding_store)

    return _multi_indexer


# Initialize MCP server
app = Server("mcpindexer")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools"""
    return [
        Tool(
            name="semantic_search",
            description="Search for code using natural language queries across indexed repositories",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "repos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: List of repo names to search. If empty, searches all.",
                    },
                    "language": {
                        "type": "string",
                        "description": "Optional: Filter by language (python, javascript, typescript, ruby, go)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="find_definition",
            description="Find the definition of a function, class, or variable",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The symbol name to find",
                    },
                    "repos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: List of repo names to search",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="find_references",
            description="Find all references/usages of a symbol (searches by semantic similarity)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The symbol name to find references for",
                    },
                    "repos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: List of repo names to search",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="find_related_code",
            description="Find architecturally related code for a given file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10,
                    },
                },
                "required": ["file_path", "repo"],
            },
        ),
        Tool(
            name="get_repo_stats",
            description="Get statistics for a repository (files, chunks, dependencies)",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Repository name"}
                },
                "required": ["repo_name"],
            },
        ),
        Tool(
            name="reindex_repo",
            description="Trigger reindexing of a specific repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Name of the repository to reindex",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force full reindex (default: false)",
                        "default": False,
                    },
                },
                "required": ["repo_name"],
            },
        ),
        Tool(
            name="add_repo_to_stack",
            description="Add a new repository to the user's stack and index it",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Local path to the repository",
                    },
                    "repo_name": {
                        "type": "string",
                        "description": "Name to identify the repository",
                    },
                },
                "required": ["repo_path", "repo_name"],
            },
        ),
        Tool(
            name="remove_repo",
            description="Remove a repository from the stack",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Name of the repository to remove",
                    }
                },
                "required": ["repo_name"],
            },
        ),
        Tool(
            name="list_repos",
            description="List all repositories in the current stack",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_cross_repo_dependencies",
            description="Find dependencies between indexed repositories",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="suggest_missing_repos",
            description="Suggest repositories to add based on dependency analysis",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_stack_status",
            description="Get overall stack status and statistics",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="answer_question",
            description="Retrieve relevant code context to answer questions about the codebase. Returns code snippets with metadata that the agent can use to formulate answers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to answer about the codebase",
                    },
                    "repos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Limit search to specific repositories. If empty, searches all repos.",
                    },
                    "context_limit": {
                        "type": "integer",
                        "description": "Maximum number of code snippets to retrieve (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["question"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    try:
        indexer = get_indexer()

        if name == "semantic_search":
            query = arguments.get("query", "")
            repos = arguments.get("repos", None)
            language = arguments.get("language", None)
            limit = arguments.get("limit", 10)

            # Perform semantic search
            results = indexer.embedding_store.semantic_search(
                query=query,
                n_results=limit,
                repo_filter=repos,
                language_filter=language,
            )

            if not results:
                return [
                    TextContent(
                        type="text", text=f"No results found for query: '{query}'"
                    )
                ]

            # Format results
            output = [f"Found {len(results)} results for '{query}':\n"]
            for i, result in enumerate(results, 1):
                output.append(f"\n{i}. {result.file_path}")
                if result.symbol_name:
                    output.append(f"   Symbol: {result.symbol_name}")
                output.append(f"   Repo: {result.repo_name}")
                output.append(
                    f"   Lines: {result.metadata.get('start_line', '?')}-{result.metadata.get('end_line', '?')}"
                )
                output.append(f"   Relevance: {result.score:.4f}")

                # Code preview
                preview = result.code_text[:200].replace("\n", "\n   ")
                output.append(f"   Code:\n   {preview}")
                if len(result.code_text) > 200:
                    output.append("   ...")

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "find_definition":
            symbol = arguments.get("symbol", "")
            repos = arguments.get("repos", None)

            # Find by exact symbol name
            results = indexer.embedding_store.find_by_symbol(
                symbol_name=symbol, repo_filter=repos
            )

            if not results:
                return [
                    TextContent(
                        type="text", text=f"No definition found for symbol: '{symbol}'"
                    )
                ]

            # Format results
            output = [f"Found {len(results)} definition(s) for '{symbol}':\n"]
            for i, result in enumerate(results, 1):
                output.append(
                    f"\n{i}. {result.file_path}:{result.metadata.get('start_line', '?')}"
                )
                output.append(f"   Repo: {result.repo_name}")
                output.append(
                    f"   Type: {result.metadata.get('chunk_type', 'unknown')}"
                )
                output.append(
                    f"   Code:\n   {result.code_text[:300].replace(chr(10), chr(10) + '   ')}"
                )

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "find_references":
            symbol = arguments.get("symbol", "")
            repos = arguments.get("repos", None)

            # Use semantic search to find references
            results = indexer.embedding_store.semantic_search(
                query=f"usage of {symbol} function or class",
                n_results=10,
                repo_filter=repos,
            )

            if not results:
                return [
                    TextContent(
                        type="text", text=f"No references found for symbol: '{symbol}'"
                    )
                ]

            output = [f"Found {len(results)} potential reference(s) to '{symbol}':\n"]
            for i, result in enumerate(results, 1):
                output.append(
                    f"\n{i}. {result.file_path}:{result.metadata.get('start_line', '?')}"
                )
                output.append(f"   Repo: {result.repo_name}")
                if result.symbol_name:
                    output.append(f"   In: {result.symbol_name}")

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "find_related_code":
            file_path = arguments.get("file_path", "")
            repo = arguments.get("repo", "")
            limit = arguments.get("limit", 10)

            # Find related code by file
            results = indexer.embedding_store.find_related_by_file(
                file_path=file_path, repo_name=repo, n_results=limit
            )

            if not results:
                return [
                    TextContent(
                        type="text", text=f"No related code found for {file_path}"
                    )
                ]

            output = [f"Found {len(results)} related file(s) to {file_path}:\n"]
            for i, result in enumerate(results, 1):
                output.append(f"\n{i}. {result.file_path}")
                if result.symbol_name:
                    output.append(f"   Symbol: {result.symbol_name}")
                output.append(f"   Similarity: {result.score:.4f}")

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "get_repo_stats":
            repo_name = arguments.get("repo_name", "")

            stats = indexer.get_repo_stats(repo_name)

            if not stats:
                return [
                    TextContent(type="text", text=f"Repository '{repo_name}' not found")
                ]

            output = [f"Statistics for '{repo_name}':\n"]
            output.append(f"  Path: {stats.get('repo_path', 'N/A')}")
            output.append(f"  Git branch: {stats.get('git_branch', 'N/A')}")
            output.append(
                f"  Git commit: {stats.get('git_commit', 'N/A')[:8] if stats.get('git_commit') else 'N/A'}"
            )
            output.append(f"  Files indexed: {stats.get('files_indexed', 0)}")
            output.append(f"  Chunks indexed: {stats.get('chunks_indexed', 0)}")
            output.append(f"  Languages: {', '.join(stats.get('languages', []))}")

            if "dependencies" in stats:
                deps = stats["dependencies"]
                output.append(f"\n  Dependencies:")
                output.append(f"    Total: {deps.get('total_dependencies', 0)}")
                output.append(f"    Internal: {deps.get('internal_dependencies', 0)}")
                output.append(f"    External: {deps.get('external_dependencies', 0)}")
                output.append(
                    f"    External packages: {deps.get('external_packages', 0)}"
                )

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "reindex_repo":
            repo_name = arguments.get("repo_name", "")
            force = arguments.get("force", False)

            if repo_name not in indexer.repo_indexers:
                return [
                    TextContent(
                        type="text",
                        text=f"Repository '{repo_name}' not found in stack. Use add_repo_to_stack first.",
                    )
                ]

            repo_indexer = indexer.repo_indexers[repo_name]
            result = repo_indexer.reindex(force=force)

            output = [f"Reindexed '{repo_name}':\n"]
            output.append(f"  Files processed: {result.files_processed}")
            output.append(f"  Files skipped: {result.files_skipped}")
            output.append(f"  Chunks created: {result.chunks_created}")
            output.append(f"  Chunks indexed: {result.chunks_indexed}")

            if result.errors:
                output.append(f"\n  Errors ({len(result.errors)}):")
                for error in result.errors[:5]:
                    output.append(f"    - {error}")

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "add_repo_to_stack":
            repo_path = arguments.get("repo_path", "")
            repo_name = arguments.get("repo_name", "")

            # Verify path exists
            if not Path(repo_path).exists():
                return [
                    TextContent(
                        type="text", text=f"Error: Path '{repo_path}' does not exist"
                    )
                ]

            # Add and index the repo
            result = indexer.add_repo(
                repo_path=repo_path, repo_name=repo_name, auto_index=True
            )

            output = [f"Added and indexed '{repo_name}':\n"]
            output.append(f"  Path: {repo_path}")
            output.append(f"  Files processed: {result.files_processed}")
            output.append(f"  Files skipped: {result.files_skipped}")
            output.append(f"  Chunks indexed: {result.chunks_indexed}")

            if result.errors:
                output.append(f"\n  Errors: {len(result.errors)}")

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "remove_repo":
            repo_name = arguments.get("repo_name", "")

            deleted_count = indexer.remove_repo(repo_name)

            return [
                TextContent(
                    type="text",
                    text=f"Removed '{repo_name}' from stack. Deleted {deleted_count} chunks.",
                )
            ]

        elif name == "list_repos":
            repos = indexer.list_repos()

            if not repos:
                return [
                    TextContent(
                        type="text",
                        text="No repositories indexed. Use add_repo_to_stack to add one.",
                    )
                ]

            output = [f"Indexed repositories ({len(repos)}):\n"]
            for repo in repos:
                stats = indexer.embedding_store.get_repo_stats(repo)
                output.append(f"\n  • {repo}")
                output.append(f"    Files: {len(stats.get('files', []))}")
                output.append(f"    Chunks: {stats.get('chunk_count', 0)}")
                output.append(f"    Languages: {', '.join(stats.get('languages', []))}")

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "get_cross_repo_dependencies":
            cross_deps = indexer.get_cross_repo_dependencies()

            if not cross_deps:
                return [
                    TextContent(
                        type="text", text="No cross-repository dependencies found."
                    )
                ]

            output = [f"Found {len(cross_deps)} cross-repository dependencies:\n"]
            for dep in cross_deps:
                output.append(f"\n  {dep['source_repo']} → {dep['target_repo']}")
                output.append(f"    Package: {dep['package']}")

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "suggest_missing_repos":
            suggestions = indexer.suggest_missing_repos()

            if not suggestions:
                return [
                    TextContent(
                        type="text",
                        text="No missing repositories detected. Your stack looks complete!",
                    )
                ]

            output = [f"Suggested repositories to add ({len(suggestions)}):\n"]
            for suggestion in suggestions:
                output.append(f"\n  • {suggestion}")
            output.append(
                "\n\nThese packages are imported but not indexed. Consider adding them to your stack."
            )

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "get_stack_status":
            stats = indexer.get_stack_status()

            output = [f"Repository Stack Status:\n"]
            output.append(f"\n  Total Repositories: {stats['total_repos']}")
            output.append(f"  Total Files Indexed: {stats['total_files_indexed']}")
            output.append(f"  Total Chunks Indexed: {stats['total_chunks_indexed']}\n")

            output.append(f"\n  Status Breakdown:")
            for status, count in stats["by_status"].items():
                if count > 0:
                    output.append(f"    {status}: {count}")

            return [TextContent(type="text", text="\n".join(output))]

        elif name == "answer_question":
            question = arguments.get("question", "")
            repos = arguments.get("repos", None)
            context_limit = arguments.get("context_limit", 10)

            if not question:
                return [
                    TextContent(
                        type="text", text="Error: question parameter is required"
                    )
                ]

            # Retrieve relevant code context using semantic search
            search_results = indexer.embedding_store.semantic_search(
                query=question, n_results=context_limit, repo_filter=repos
            )

            if not search_results:
                return [
                    TextContent(
                        type="text",
                        text=f"No relevant code found for question: '{question}'",
                    )
                ]

            # Build context from search results - concise format for agent
            # Collect file paths for reference
            file_refs = []
            for result in search_results:
                file_ref = (
                    f"{result.file_path}:{result.metadata.get('start_line', '?')}"
                )
                if file_ref not in file_refs:
                    file_refs.append(file_ref)

            # Build compact context for the agent
            output = []
            output.append(
                f"Found {len(search_results)} relevant code snippets. Analyzing to answer: '{question}'\n"
            )

            for i, result in enumerate(search_results, 1):
                # Concise format - just enough for agent to understand context
                symbol = f" ({result.symbol_name})" if result.symbol_name else ""
                output.append(
                    f"{i}. {result.file_path}:{result.metadata.get('start_line', '?')}{symbol}"
                )
                output.append(f"```{result.metadata.get('language', '')}")
                output.append(result.code_text)
                output.append("```")

            # Add file reference list at the end
            output.append(f"\nRelevant files:")
            for ref in file_refs:
                output.append(f"- {ref}")

            output.append(
                "\nAnalyze the code above and provide a clear answer, referencing specific files where appropriate."
            )

            return [TextContent(type="text", text="\n".join(output))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
