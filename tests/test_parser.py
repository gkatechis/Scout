"""
Tests for the multi-language code parser
"""
import pytest
from mcpindexer.parser import CodeParser, LanguageType


# Test code samples for each language
PYTHON_CODE = '''
import os
from typing import List, Optional
from .local_module import helper

class UserManager:
    def __init__(self):
        pass

    def create_user(self, name: str) -> None:
        print(f"Creating user: {name}")

def authenticate_user(username: str) -> bool:
    return username in ["alice", "bob"]
'''

JAVASCRIPT_CODE = '''
import { createServer } from 'http';
import express from 'express';
import { helper } from './local';

class UserManager {
    constructor() {
        this.users = [];
    }

    createUser(name) {
        console.log(`Creating user: ${name}`);
    }
}

function authenticateUser(username) {
    return ['alice', 'bob'].includes(username);
}
'''

TYPESCRIPT_CODE = '''
import { Server } from 'http';
import express from 'express';
import { Helper } from './local';

class UserManager {
    users: string[] = [];

    createUser(name: string): void {
        console.log(`Creating user: ${name}`);
    }
}

function authenticateUser(username: string): boolean {
    return ['alice', 'bob'].includes(username);
}
'''

RUBY_CODE = '''
require 'json'
require_relative 'local_helper'

class UserManager
  def initialize
    @users = []
  end

  def create_user(name)
    puts "Creating user: #{name}"
  end
end

def authenticate_user(username)
  ['alice', 'bob'].include?(username)
end
'''

GO_CODE = '''
package main

import (
    "fmt"
    "strings"
)

type UserManager struct {
    users []string
}

func (um *UserManager) CreateUser(name string) {
    fmt.Printf("Creating user: %s\\n", name)
}

func AuthenticateUser(username string) bool {
    return username == "alice" || username == "bob"
}
'''


class TestCodeParser:
    """Tests for CodeParser class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = CodeParser()

    def test_parser_initialization(self):
        """Test that parser initializes with all languages"""
        assert len(self.parser.parsers) == 6
        assert LanguageType.PYTHON in self.parser.parsers
        assert LanguageType.JAVASCRIPT in self.parser.parsers
        assert LanguageType.TYPESCRIPT in self.parser.parsers
        assert LanguageType.RUBY in self.parser.parsers
        assert LanguageType.GO in self.parser.parsers

    def test_detect_language_python(self):
        """Test language detection for Python files"""
        assert self.parser.detect_language("test.py") == LanguageType.PYTHON
        assert self.parser.detect_language("/path/to/file.py") == LanguageType.PYTHON

    def test_detect_language_javascript(self):
        """Test language detection for JavaScript files"""
        assert self.parser.detect_language("test.js") == LanguageType.JAVASCRIPT
        assert self.parser.detect_language("test.mjs") == LanguageType.JAVASCRIPT
        assert self.parser.detect_language("test.cjs") == LanguageType.JAVASCRIPT

    def test_detect_language_typescript(self):
        """Test language detection for TypeScript files"""
        assert self.parser.detect_language("test.ts") == LanguageType.TYPESCRIPT
        assert self.parser.detect_language("test.tsx") == LanguageType.TSX

    def test_detect_language_ruby(self):
        """Test language detection for Ruby files"""
        assert self.parser.detect_language("test.rb") == LanguageType.RUBY

    def test_detect_language_go(self):
        """Test language detection for Go files"""
        assert self.parser.detect_language("test.go") == LanguageType.GO

    def test_detect_language_unknown(self):
        """Test language detection for unsupported files"""
        assert self.parser.detect_language("test.cpp") is None
        assert self.parser.detect_language("test.java") is None

    def test_parse_python_functions(self):
        """Test parsing Python functions"""
        parsed = self.parser.parse_file("test.py", PYTHON_CODE)

        assert parsed is not None
        assert parsed.language == LanguageType.PYTHON
        assert len(parsed.functions) >= 1

        # Find the authenticate_user function
        auth_func = next((f for f in parsed.functions if "authenticate" in f.name.lower()), None)
        assert auth_func is not None
        assert "authenticate_user" in auth_func.name

    def test_parse_python_classes(self):
        """Test parsing Python classes"""
        parsed = self.parser.parse_file("test.py", PYTHON_CODE)

        assert len(parsed.classes) >= 1

        # Find the UserManager class
        user_class = next((c for c in parsed.classes if "UserManager" in c.name), None)
        assert user_class is not None
        assert user_class.name == "UserManager"

    def test_parse_python_imports(self):
        """Test parsing Python imports"""
        parsed = self.parser.parse_file("test.py", PYTHON_CODE)

        assert len(parsed.imports) >= 2

        # Check for external import
        external_imports = [i for i in parsed.imports if i.is_external]
        assert len(external_imports) >= 1

        # Check for local import
        local_imports = [i for i in parsed.imports if not i.is_external]
        assert len(local_imports) >= 1

    def test_parse_javascript_functions(self):
        """Test parsing JavaScript functions"""
        parsed = self.parser.parse_file("test.js", JAVASCRIPT_CODE)

        assert parsed is not None
        assert parsed.language == LanguageType.JAVASCRIPT
        assert len(parsed.functions) >= 1

    def test_parse_javascript_classes(self):
        """Test parsing JavaScript classes"""
        parsed = self.parser.parse_file("test.js", JAVASCRIPT_CODE)

        assert len(parsed.classes) >= 1
        user_class = next((c for c in parsed.classes if "UserManager" in c.name), None)
        assert user_class is not None

    def test_parse_typescript_functions(self):
        """Test parsing TypeScript functions"""
        parsed = self.parser.parse_file("test.ts", TYPESCRIPT_CODE)

        assert parsed is not None
        assert parsed.language == LanguageType.TYPESCRIPT
        assert len(parsed.functions) >= 1

    def test_parse_typescript_classes(self):
        """Test parsing TypeScript classes"""
        parsed = self.parser.parse_file("test.ts", TYPESCRIPT_CODE)

        assert len(parsed.classes) >= 1

    def test_parse_ruby_functions(self):
        """Test parsing Ruby functions"""
        parsed = self.parser.parse_file("test.rb", RUBY_CODE)

        assert parsed is not None
        assert parsed.language == LanguageType.RUBY
        assert len(parsed.functions) >= 1

    def test_parse_ruby_classes(self):
        """Test parsing Ruby classes"""
        parsed = self.parser.parse_file("test.rb", RUBY_CODE)

        assert len(parsed.classes) >= 1

    def test_parse_go_functions(self):
        """Test parsing Go functions"""
        parsed = self.parser.parse_file("test.go", GO_CODE)

        assert parsed is not None
        assert parsed.language == LanguageType.GO
        assert len(parsed.functions) >= 1

    def test_parse_go_types(self):
        """Test parsing Go type declarations"""
        parsed = self.parser.parse_file("test.go", GO_CODE)

        # Go structs show up as class definitions
        assert len(parsed.classes) >= 1

    def test_parse_unsupported_language(self):
        """Test parsing unsupported file returns None"""
        parsed = self.parser.parse_file("test.cpp", "int main() { return 0; }")
        assert parsed is None

    def test_code_symbol_attributes(self):
        """Test that CodeSymbol has all required attributes"""
        parsed = self.parser.parse_file("test.py", PYTHON_CODE)

        if parsed.functions:
            func = parsed.functions[0]
            assert hasattr(func, 'type')
            assert hasattr(func, 'name')
            assert hasattr(func, 'start_byte')
            assert hasattr(func, 'end_byte')
            assert hasattr(func, 'start_line')
            assert hasattr(func, 'end_line')
            assert hasattr(func, 'text')
            assert func.start_line >= 0
            assert func.end_line >= func.start_line

    def test_import_statement_attributes(self):
        """Test that ImportStatement has all required attributes"""
        parsed = self.parser.parse_file("test.py", PYTHON_CODE)

        if parsed.imports:
            imp = parsed.imports[0]
            assert hasattr(imp, 'module')
            assert hasattr(imp, 'symbols')
            assert hasattr(imp, 'start_line')
            assert hasattr(imp, 'is_external')
            assert isinstance(imp.symbols, list)
            assert isinstance(imp.is_external, bool)

    def test_parsed_file_attributes(self):
        """Test that ParsedFile has all required attributes"""
        parsed = self.parser.parse_file("test.py", PYTHON_CODE)

        assert hasattr(parsed, 'file_path')
        assert hasattr(parsed, 'language')
        assert hasattr(parsed, 'functions')
        assert hasattr(parsed, 'classes')
        assert hasattr(parsed, 'imports')
        assert hasattr(parsed, 'raw_code')
        assert parsed.raw_code == PYTHON_CODE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
