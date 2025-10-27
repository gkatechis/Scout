"""
Code chunking strategy for semantic search

Respects code boundaries (functions, classes) while maintaining
target chunk size of ~200-300 tokens. Adds context metadata.
"""

from dataclasses import dataclass
from typing import List, Optional

from mcpindexer.parser import CodeSymbol, ParsedFile


@dataclass
class CodeChunk:
    """Represents a chunk of code for embedding"""

    chunk_id: str  # Unique identifier
    file_path: str
    repo_name: str
    language: str
    chunk_type: str  # function, class, module, file
    code_text: str
    start_line: int
    end_line: int

    # Context metadata
    symbol_name: Optional[str]  # Name of function/class if applicable
    parent_class: Optional[str]  # Parent class name if method
    imports: List[str]  # Relevant imports for this chunk

    # For retrieval
    context_text: str  # Enhanced text with file path and structure
    token_count: int  # Approximate token count


class CodeChunker:
    """
    Chunks code at logical boundaries while respecting token limits
    """

    TARGET_MIN_TOKENS = 100  # Minimum chunk size
    TARGET_MAX_TOKENS = 300  # Maximum chunk size
    CHARS_PER_TOKEN = 4  # Rough estimate: 1 token ≈ 4 chars

    def __init__(self, repo_name: str):
        """
        Initialize chunker for a repository

        Args:
            repo_name: Name of the repository being chunked
        """
        self.repo_name = repo_name
        self.chunk_counter = 0

    def chunk_file(self, parsed_file: ParsedFile) -> List[CodeChunk]:
        """
        Chunk a parsed file into semantic units

        Strategy:
        1. Each class becomes a chunk (if under max size)
        2. Each top-level function becomes a chunk
        3. Large classes are split by methods
        4. Very small chunks are merged

        Args:
            parsed_file: ParsedFile object from parser

        Returns:
            List of CodeChunk objects
        """
        chunks = []

        # Extract imports for context
        import_statements = [imp.module for imp in parsed_file.imports]

        # Chunk classes
        for cls in parsed_file.classes:
            cls_chunks = self._chunk_class(cls, parsed_file, import_statements)
            chunks.extend(cls_chunks)

        # Chunk standalone functions (not part of classes)
        for func in parsed_file.functions:
            # Skip if function is part of a class (already chunked)
            if self._is_function_in_class(func, parsed_file.classes):
                continue

            func_chunk = self._chunk_function(
                func, parsed_file, import_statements, parent_class=None
            )
            if func_chunk:
                chunks.append(func_chunk)

        # If file has no functions/classes, create a file-level chunk
        if not chunks:
            chunks.append(self._chunk_entire_file(parsed_file, import_statements))

        return chunks

    def _chunk_class(
        self, cls: CodeSymbol, parsed_file: ParsedFile, imports: List[str]
    ) -> List[CodeChunk]:
        """Chunk a class definition"""
        chunks = []
        token_count = self._estimate_tokens(cls.text)

        # If class is small enough, keep it as one chunk
        if token_count <= self.TARGET_MAX_TOKENS:
            chunks.append(
                CodeChunk(
                    chunk_id=self._generate_chunk_id(),
                    file_path=parsed_file.file_path,
                    repo_name=self.repo_name,
                    language=parsed_file.language.value,
                    chunk_type="class",
                    code_text=cls.text,
                    start_line=cls.start_line,
                    end_line=cls.end_line,
                    symbol_name=cls.name,
                    parent_class=None,
                    imports=imports,
                    context_text=self._build_context(
                        parsed_file.file_path, cls.name, None, cls.text
                    ),
                    token_count=token_count,
                )
            )
        else:
            # Split large class by methods
            # But first, create a chunk for the class header/definition
            class_header = self._extract_class_header(cls, parsed_file)
            if class_header:
                chunks.append(
                    CodeChunk(
                        chunk_id=self._generate_chunk_id(),
                        file_path=parsed_file.file_path,
                        repo_name=self.repo_name,
                        language=parsed_file.language.value,
                        chunk_type="class_definition",
                        code_text=class_header,
                        start_line=cls.start_line,
                        end_line=min(
                            cls.start_line + 50, cls.end_line
                        ),  # First ~50 lines
                        symbol_name=cls.name,
                        parent_class=None,
                        imports=imports,
                        context_text=self._build_context(
                            parsed_file.file_path, cls.name, None, class_header
                        ),
                        token_count=self._estimate_tokens(class_header),
                    )
                )

            # Then chunk the methods
            methods = self._extract_methods_from_class(cls, parsed_file)

            for method in methods:
                method_chunk = self._chunk_function(
                    method, parsed_file, imports, parent_class=cls.name
                )
                if method_chunk:
                    chunks.append(method_chunk)

        return chunks

    def _chunk_function(
        self,
        func: CodeSymbol,
        parsed_file: ParsedFile,
        imports: List[str],
        parent_class: Optional[str],
    ) -> Optional[CodeChunk]:
        """Chunk a function definition"""
        token_count = self._estimate_tokens(func.text)

        # Skip very small functions (less than min threshold)
        if token_count < self.TARGET_MIN_TOKENS:
            # Could merge with neighbors, but for now just skip
            # TODO: Implement merging strategy
            pass

        return CodeChunk(
            chunk_id=self._generate_chunk_id(),
            file_path=parsed_file.file_path,
            repo_name=self.repo_name,
            language=parsed_file.language.value,
            chunk_type="function",
            code_text=func.text,
            start_line=func.start_line,
            end_line=func.end_line,
            symbol_name=func.name,
            parent_class=parent_class,
            imports=imports,
            context_text=self._build_context(
                parsed_file.file_path, func.name, parent_class, func.text
            ),
            token_count=token_count,
        )

    def _chunk_entire_file(
        self, parsed_file: ParsedFile, imports: List[str]
    ) -> CodeChunk:
        """Create a chunk from entire file (when no functions/classes found)"""
        token_count = self._estimate_tokens(parsed_file.raw_code)

        # Truncate if too large
        code_text = parsed_file.raw_code
        if token_count > self.TARGET_MAX_TOKENS:
            target_chars = self.TARGET_MAX_TOKENS * self.CHARS_PER_TOKEN
            code_text = code_text[:target_chars] + "\n... (truncated)"
            token_count = self.TARGET_MAX_TOKENS

        return CodeChunk(
            chunk_id=self._generate_chunk_id(),
            file_path=parsed_file.file_path,
            repo_name=self.repo_name,
            language=parsed_file.language.value,
            chunk_type="file",
            code_text=code_text,
            start_line=0,
            end_line=len(parsed_file.raw_code.splitlines()),
            symbol_name=None,
            parent_class=None,
            imports=imports,
            context_text=self._build_context(
                parsed_file.file_path, None, None, code_text
            ),
            token_count=token_count,
        )

    def _extract_methods_from_class(
        self, cls: CodeSymbol, parsed_file: ParsedFile
    ) -> List[CodeSymbol]:
        """Extract methods that belong to a class"""
        methods = []

        for func in parsed_file.functions:
            # Check if function is within class boundaries
            if cls.start_byte <= func.start_byte < cls.end_byte:
                methods.append(func)

        return methods

    def _is_function_in_class(
        self, func: CodeSymbol, classes: List[CodeSymbol]
    ) -> bool:
        """Check if a function is inside a class"""
        for cls in classes:
            if cls.start_byte <= func.start_byte < cls.end_byte:
                return True
        return False

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text"""
        return len(text) // self.CHARS_PER_TOKEN

    def _generate_chunk_id(self) -> str:
        """Generate unique chunk ID"""
        self.chunk_counter += 1
        return f"{self.repo_name}:chunk:{self.chunk_counter}"

    def _extract_class_header(
        self, cls: CodeSymbol, parsed_file: ParsedFile
    ) -> Optional[str]:
        """
        Extract class header/definition (first ~50 lines or up to first method)

        This captures the class declaration, includes, inheritance, and attributes
        but excludes method definitions for large classes.
        """
        lines = cls.text.splitlines()

        # Take first 50 lines or up to TARGET_MAX_TOKENS, whichever is smaller
        max_lines = 50
        header_lines = []

        for i, line in enumerate(lines[:max_lines]):
            # Stop if we estimate we've hit the token limit
            current_text = "\n".join(header_lines + [line])
            if self._estimate_tokens(current_text) > self.TARGET_MAX_TOKENS:
                break
            header_lines.append(line)

        if header_lines:
            return "\n".join(header_lines)

        return None

    def _build_context(
        self,
        file_path: str,
        symbol_name: Optional[str],
        parent_class: Optional[str],
        code_text: str,
    ) -> str:
        """
        Build enhanced context text for better retrieval

        Format: "File: {path} | Symbol: {name} | Class: {class}\n{code}"
        """
        parts = [f"File: {file_path}"]

        if parent_class:
            parts.append(f"Class: {parent_class}")

        if symbol_name:
            if parent_class:
                parts.append(f"Method: {symbol_name}")
            else:
                parts.append(f"Function: {symbol_name}")

        context_header = " | ".join(parts)
        return f"{context_header}\n\n{code_text}"
