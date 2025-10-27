"""
Multi-language code parser using tree-sitter

Supports: JavaScript, TypeScript, Python, Ruby, Go
Extracts: Functions, classes, imports, method calls
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

import tree_sitter_go
import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_ruby
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser, Query, QueryCursor


class LanguageType(Enum):
    """Supported programming languages"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    TSX = "tsx"
    RUBY = "ruby"
    GO = "go"


@dataclass
class CodeSymbol:
    """Represents a code symbol (function, class, etc.)"""

    type: str  # function_definition, class_definition, etc.
    name: str
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int
    text: str


@dataclass
class ImportStatement:
    """Represents an import/require statement"""

    module: str
    symbols: List[str]  # imported symbols (empty for wildcard imports)
    start_line: int
    is_external: bool  # True if importing from external package


@dataclass
class ParsedFile:
    """Result of parsing a file"""

    file_path: str
    language: LanguageType
    functions: List[CodeSymbol]
    classes: List[CodeSymbol]
    imports: List[ImportStatement]
    raw_code: str


class CodeParser:
    """Multi-language code parser using tree-sitter"""

    def __init__(self):
        """Initialize parsers for all supported languages"""
        self.parsers = {
            LanguageType.PYTHON: Parser(Language(tree_sitter_python.language())),
            LanguageType.JAVASCRIPT: Parser(
                Language(tree_sitter_javascript.language())
            ),
            LanguageType.TYPESCRIPT: Parser(
                Language(tree_sitter_typescript.language_typescript())
            ),
            LanguageType.TSX: Parser(Language(tree_sitter_typescript.language_tsx())),
            LanguageType.RUBY: Parser(Language(tree_sitter_ruby.language())),
            LanguageType.GO: Parser(Language(tree_sitter_go.language())),
        }

        # Query patterns for each language
        self.queries = self._init_queries()

    def _init_queries(self) -> dict:
        """Initialize query patterns for each language"""
        return {
            LanguageType.PYTHON: {
                "functions": "(function_definition name: (identifier) @func.name) @func.def",
                "classes": "(class_definition name: (identifier) @class.name) @class.def",
                "imports": "[(import_statement) (import_from_statement)] @import",
            },
            LanguageType.JAVASCRIPT: {
                "functions": "(function_declaration name: (identifier) @func.name) @func.def",
                "classes": "(class_declaration name: (identifier) @class.name) @class.def",
                "imports": "[(import_statement) (import_clause)] @import",
            },
            LanguageType.TYPESCRIPT: {
                "functions": "(function_declaration name: (identifier) @func.name) @func.def",
                "classes": "(class_declaration name: (type_identifier) @class.name) @class.def",
                "imports": "(import_statement) @import",
            },
            LanguageType.TSX: {
                "functions": "(function_declaration name: (identifier) @func.name) @func.def",
                "classes": "(class_declaration name: (type_identifier) @class.name) @class.def",
                "imports": "(import_statement) @import",
            },
            LanguageType.RUBY: {
                "functions": "(method name: (identifier) @func.name) @func.def",
                "classes": "(class name: (constant) @class.name) @class.def",
                "imports": '(call method: (identifier) @method (#match? @method "^(require|require_relative|load)$")) @import',
            },
            LanguageType.GO: {
                "functions": "(function_declaration name: (identifier) @func.name) @func.def",
                "classes": "(type_declaration (type_spec name: (type_identifier) @class.name)) @class.def",
                "imports": "(import_declaration) @import",
            },
        }

    def detect_language(self, file_path: str) -> Optional[LanguageType]:
        """Detect language from file extension"""
        path = Path(file_path)
        extension = path.suffix.lower()

        mapping = {
            ".py": LanguageType.PYTHON,
            ".js": LanguageType.JAVASCRIPT,
            ".mjs": LanguageType.JAVASCRIPT,
            ".cjs": LanguageType.JAVASCRIPT,
            ".ts": LanguageType.TYPESCRIPT,
            ".tsx": LanguageType.TSX,
            ".rb": LanguageType.RUBY,
            ".go": LanguageType.GO,
        }

        return mapping.get(extension)

    def parse_file(
        self, file_path: str, code: Optional[str] = None
    ) -> Optional[ParsedFile]:
        """
        Parse a code file and extract symbols

        Args:
            file_path: Path to the file
            code: Optional code content (if None, reads from file_path)

        Returns:
            ParsedFile object or None if language not supported
        """
        language = self.detect_language(file_path)
        if not language:
            return None

        # Read code if not provided
        if code is None:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

        # Parse the code
        parser = self.parsers[language]
        tree = parser.parse(bytes(code, "utf-8"))

        # Extract symbols
        functions = self._extract_functions(tree, code, language)
        classes = self._extract_classes(tree, code, language)
        imports = self._extract_imports(tree, code, language)

        return ParsedFile(
            file_path=file_path,
            language=language,
            functions=functions,
            classes=classes,
            imports=imports,
            raw_code=code,
        )

    def _extract_functions(
        self, tree, code: str, language: LanguageType
    ) -> List[CodeSymbol]:
        """Extract function definitions"""
        return self._extract_symbols(tree, code, language, "functions", "func")

    def _extract_classes(
        self, tree, code: str, language: LanguageType
    ) -> List[CodeSymbol]:
        """Extract class definitions"""
        return self._extract_symbols(tree, code, language, "classes", "class")

    def _extract_symbols(
        self,
        tree,
        code: str,
        language: LanguageType,
        query_type: str,
        capture_prefix: str,
    ) -> List[CodeSymbol]:
        """Generic symbol extraction"""
        symbols = []
        query_pattern = self.queries[language].get(query_type)
        if not query_pattern:
            return symbols

        try:
            lang_obj = Language(self._get_language_capsule(language))
            query = Query(lang_obj, query_pattern)
            cursor = QueryCursor(query)
            captures = cursor.captures(tree.root_node)

            # Group captures by definition node
            name_key = f"{capture_prefix}.name"
            def_key = f"{capture_prefix}.def"

            if def_key in captures:
                for def_node in captures[def_key]:
                    # Find corresponding name
                    name = "unknown"
                    if name_key in captures:
                        for name_node in captures[name_key]:
                            if (
                                def_node.start_byte
                                <= name_node.start_byte
                                <= def_node.end_byte
                            ):
                                name = code[name_node.start_byte : name_node.end_byte]
                                break

                    symbols.append(
                        CodeSymbol(
                            type=def_node.type,
                            name=name,
                            start_byte=def_node.start_byte,
                            end_byte=def_node.end_byte,
                            start_line=def_node.start_point[0],
                            end_line=def_node.end_point[0],
                            text=code[def_node.start_byte : def_node.end_byte],
                        )
                    )
        except Exception as e:
            # Silently skip query errors for now
            pass

        return symbols

    def _extract_imports(
        self, tree, code: str, language: LanguageType
    ) -> List[ImportStatement]:
        """Extract import statements"""
        imports = []
        query_pattern = self.queries[language].get("imports")
        if not query_pattern:
            return imports

        try:
            lang_obj = Language(self._get_language_capsule(language))
            query = Query(lang_obj, query_pattern)
            cursor = QueryCursor(query)
            captures = cursor.captures(tree.root_node)

            if "import" in captures:
                for import_node in captures["import"]:
                    import_text = code[import_node.start_byte : import_node.end_byte]
                    module, symbols, is_external = self._parse_import_statement(
                        import_text, language
                    )

                    imports.append(
                        ImportStatement(
                            module=module,
                            symbols=symbols,
                            start_line=import_node.start_point[0],
                            is_external=is_external,
                        )
                    )
        except Exception as e:
            # Silently skip query errors for now
            pass

        return imports

    def _parse_import_statement(
        self, import_text: str, language: LanguageType
    ) -> tuple[str, List[str], bool]:
        """
        Parse import statement to extract module and symbols

        Returns: (module_name, symbols, is_external)
        """
        # Simplified parsing - can be enhanced later
        module = ""
        symbols = []
        is_external = True

        if language == LanguageType.PYTHON:
            # Examples: "import os", "from foo import bar", "from .local import x"
            if "from" in import_text:
                parts = (
                    import_text.replace("from ", "").replace("import ", "|").split("|")
                )
                if len(parts) >= 2:
                    module = parts[0].strip()
                    symbols = [s.strip() for s in parts[1].split(",")]
            else:
                module = import_text.replace("import ", "").strip()

            is_external = not module.startswith(".")

        elif language in [
            LanguageType.JAVASCRIPT,
            LanguageType.TYPESCRIPT,
            LanguageType.TSX,
        ]:
            # Examples: "import { x } from 'module'", "import x from 'module'"
            if "from" in import_text:
                parts = import_text.split("from")
                if len(parts) >= 2:
                    module = parts[1].strip().strip("'\"")

            is_external = not (module.startswith("./") or module.startswith("../"))

        elif language == LanguageType.RUBY:
            # Examples: "require 'module'", "require_relative 'local'"
            module = (
                import_text.replace("require", "")
                .replace("require_relative", "")
                .strip()
                .strip("'\"")
            )
            is_external = "require_relative" not in import_text

        elif language == LanguageType.GO:
            # Examples: "import \"fmt\"", "import ( \"os\" \"fmt\" )"
            # Simplified - just extract quoted strings
            import re

            matches = re.findall(r'"([^"]+)"', import_text)
            if matches:
                module = matches[0]  # Take first import
            is_external = True  # Go imports are typically external packages

        return module, symbols, is_external

    def _get_language_capsule(self, language: LanguageType):
        """Get the raw language capsule for a given language"""
        mapping = {
            LanguageType.PYTHON: tree_sitter_python.language(),
            LanguageType.JAVASCRIPT: tree_sitter_javascript.language(),
            LanguageType.TYPESCRIPT: tree_sitter_typescript.language_typescript(),
            LanguageType.TSX: tree_sitter_typescript.language_tsx(),
            LanguageType.RUBY: tree_sitter_ruby.language(),
            LanguageType.GO: tree_sitter_go.language(),
        }
        return mapping[language]
