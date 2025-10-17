#!/usr/bin/env python3
"""
Demo script showing the MCP Indexer pipeline working end-to-end

Steps:
1. Parse sample code files
2. Chunk them into semantic units
3. Generate embeddings and store in ChromaDB
4. Perform semantic searches
"""
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcpindexer.parser import CodeParser
from mcpindexer.chunker import CodeChunker
from mcpindexer.embeddings import EmbeddingStore

# Sample code files to index
SAMPLE_AUTH_PY = '''
import bcrypt
from typing import Optional
from .database import get_user_by_username

class AuthenticationService:
    """Service for handling user authentication"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user with username and password"""
        user = get_user_by_username(username)
        if not user:
            return None

        if bcrypt.checkpw(password.encode(), user['password_hash']):
            return self._generate_token(user)

        return None

    def _generate_token(self, user: dict) -> dict:
        """Generate JWT token for authenticated user"""
        import jwt
        payload = {
            'user_id': user['id'],
            'username': user['username']
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return {'token': token, 'user': user}

def validate_password_strength(password: str) -> bool:
    """Check if password meets security requirements"""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit
'''

SAMPLE_USER_PY = '''
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class User:
    """User model representing a system user"""
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

class UserRepository:
    """Repository for user database operations"""

    def __init__(self, db_connection):
        self.db = db_connection

    def create_user(self, username: str, email: str, password_hash: str) -> User:
        """Create a new user in the database"""
        query = """
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
            RETURNING id, username, email, created_at
        """
        result = self.db.execute(query, (username, email, password_hash))
        row = result.fetchone()
        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            created_at=datetime.fromisoformat(row[3])
        )

    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        query = "SELECT * FROM users WHERE username = ?"
        result = self.db.execute(query, (username,))
        row = result.fetchone()
        if not row:
            return None
        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            created_at=datetime.fromisoformat(row[3])
        )
'''

SAMPLE_API_JS = '''
const express = require('express');
const { AuthenticationService } = require('./auth');

class UserAPI {
    constructor(authService) {
        this.authService = authService;
        this.router = express.Router();
        this.setupRoutes();
    }

    setupRoutes() {
        this.router.post('/login', this.handleLogin.bind(this));
        this.router.post('/register', this.handleRegister.bind(this));
        this.router.get('/profile', this.requireAuth, this.getProfile.bind(this));
    }

    async handleLogin(req, res) {
        const { username, password } = req.body;

        if (!username || !password) {
            return res.status(400).json({ error: 'Missing credentials' });
        }

        const result = await this.authService.authenticate(username, password);

        if (!result) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        res.json({ token: result.token, user: result.user });
    }

    async handleRegister(req, res) {
        const { username, email, password } = req.body;

        // Validate input
        if (!username || !email || !password) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        try {
            const user = await this.authService.registerUser(username, email, password);
            res.status(201).json({ user });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    }

    requireAuth(req, res, next) {
        const token = req.headers.authorization?.split(' ')[1];

        if (!token) {
            return res.status(401).json({ error: 'No token provided' });
        }

        try {
            const decoded = this.authService.verifyToken(token);
            req.user = decoded;
            next();
        } catch (error) {
            res.status(401).json({ error: 'Invalid token' });
        }
    }

    async getProfile(req, res) {
        res.json({ user: req.user });
    }
}

module.exports = { UserAPI };
'''


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_chunk_info(chunk, index: int):
    """Print information about a code chunk"""
    print(f"Chunk {index + 1}:")
    print(f"  Type: {chunk.chunk_type}")
    print(f"  Symbol: {chunk.symbol_name or 'N/A'}")
    print(f"  Lines: {chunk.start_line}-{chunk.end_line}")
    print(f"  Tokens: {chunk.token_count}")
    print(f"  Code preview: {chunk.code_text[:80].strip()}...")
    print()


def print_search_result(result, index: int):
    """Print a search result"""
    print(f"{index + 1}. {result.file_path}")
    print(f"   Repo: {result.repo_name}")
    print(f"   Symbol: {result.symbol_name or 'N/A'}")
    print(f"   Score: {result.score:.4f}")
    print(f"   Preview: {result.code_text[:100].strip()}...")
    print()


def main():
    print_section("MCP Indexer - Complete Pipeline Demo")

    # Create temporary directory for ChromaDB
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary database at: {temp_dir}\n")

    try:
        # Initialize components
        print_section("Step 1: Initialize Components")
        parser = CodeParser()
        chunker = CodeChunker(repo_name="demo-app")
        store = EmbeddingStore(db_path=temp_dir, collection_name="demo")
        print("✓ Parser, Chunker, and EmbeddingStore initialized")

        # Parse files
        print_section("Step 2: Parse Sample Code Files")

        print("Parsing auth.py...")
        auth_parsed = parser.parse_file("auth.py", SAMPLE_AUTH_PY)
        print(f"  Found {len(auth_parsed.functions)} functions")
        print(f"  Found {len(auth_parsed.classes)} classes")
        print(f"  Found {len(auth_parsed.imports)} imports")

        print("\nParsing user.py...")
        user_parsed = parser.parse_file("user.py", SAMPLE_USER_PY)
        print(f"  Found {len(user_parsed.functions)} functions")
        print(f"  Found {len(user_parsed.classes)} classes")
        print(f"  Found {len(user_parsed.imports)} imports")

        print("\nParsing api.js...")
        api_parsed = parser.parse_file("api.js", SAMPLE_API_JS)
        print(f"  Found {len(api_parsed.functions)} functions")
        print(f"  Found {len(api_parsed.classes)} classes")
        print(f"  Found {len(api_parsed.imports)} imports")

        # Chunk files
        print_section("Step 3: Chunk Code into Semantic Units")

        all_chunks = []

        auth_chunks = chunker.chunk_file(auth_parsed)
        print(f"auth.py → {len(auth_chunks)} chunks")
        for i, chunk in enumerate(auth_chunks[:2]):  # Show first 2
            print_chunk_info(chunk, i)
        all_chunks.extend(auth_chunks)

        user_chunks = chunker.chunk_file(user_parsed)
        print(f"user.py → {len(user_chunks)} chunks")
        for i, chunk in enumerate(user_chunks[:2]):
            print_chunk_info(chunk, i)
        all_chunks.extend(user_chunks)

        api_chunks = chunker.chunk_file(api_parsed)
        print(f"api.js → {len(api_chunks)} chunks")
        for i, chunk in enumerate(api_chunks[:2]):
            print_chunk_info(chunk, i)
        all_chunks.extend(api_chunks)

        print(f"Total chunks created: {len(all_chunks)}")

        # Generate embeddings and store
        print_section("Step 4: Generate Embeddings & Store in ChromaDB")
        print("Generating embeddings (this may take a few seconds)...")
        store.add_chunks(all_chunks)
        print(f"✓ Stored {len(all_chunks)} chunks with embeddings")

        # Get repository stats
        stats = store.get_repo_stats("demo-app")
        print(f"\nRepository Stats:")
        print(f"  Total chunks: {stats['chunk_count']}")
        print(f"  Files: {len(stats['files'])}")
        print(f"  Languages: {', '.join(stats['languages'])}")

        # Perform semantic searches
        print_section("Step 5: Semantic Search Queries")

        # Query 1: Find authentication code
        print("Query 1: 'user authentication and login'")
        results = store.semantic_search("user authentication and login", n_results=3)
        for i, result in enumerate(results):
            print_search_result(result, i)

        # Query 2: Find password validation
        print("\nQuery 2: 'password validation security'")
        results = store.semantic_search("password validation security", n_results=3)
        for i, result in enumerate(results):
            print_search_result(result, i)

        # Query 3: Find database operations
        print("\nQuery 3: 'database query user lookup'")
        results = store.semantic_search("database query user lookup", n_results=3)
        for i, result in enumerate(results):
            print_search_result(result, i)

        # Symbol lookup
        print_section("Step 6: Symbol Lookup")

        print("Finding symbol: 'authenticate_user'")
        results = store.find_by_symbol("authenticate_user")
        if results:
            print(f"Found {len(results)} occurrence(s):")
            for i, result in enumerate(results):
                print_search_result(result, i)
        else:
            print("No results found")

        # Language-specific search
        print_section("Step 7: Language-Filtered Search")

        print("Query: 'user registration' (JavaScript only)")
        results = store.semantic_search(
            "user registration",
            n_results=3,
            language_filter="javascript"
        )
        for i, result in enumerate(results):
            print_search_result(result, i)

        print_section("Demo Complete!")
        print("The MCP Indexer successfully:")
        print("  ✓ Parsed multi-language code (Python, JavaScript)")
        print("  ✓ Chunked code at logical boundaries")
        print("  ✓ Generated semantic embeddings")
        print("  ✓ Performed natural language searches")
        print("  ✓ Located symbols and filtered by language")
        print("\nAll components working together! 🎉\n")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Cleaned up temporary database")


if __name__ == "__main__":
    main()
