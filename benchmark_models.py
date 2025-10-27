#!/usr/bin/env python3
"""
Benchmark script to compare embedding models on code search quality
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

from mcpindexer.chunker import CodeChunk
from mcpindexer.embeddings import EmbeddingStore

# Sample code chunks representing real-world scenarios
SAMPLE_CHUNKS = [
    CodeChunk(
        chunk_id="test:auth:1",
        file_path="auth/authenticate.py",
        repo_name="test-repo",
        language="python",
        chunk_type="function",
        code_text="""def authenticate_user(username: str, password: str) -> bool:
    \"\"\"Verify user credentials and return authentication status\"\"\"
    hashed_password = hash_password(password)
    user = database.get_user(username)
    return user and user.password_hash == hashed_password""",
        start_line=10,
        end_line=15,
        symbol_name="authenticate_user",
        parent_class=None,
        imports=["bcrypt", "database"],
        context_text="Function: authenticate_user\n\ndef authenticate_user(username: str, password: str) -> bool:\n    \"\"\"Verify user credentials and return authentication status\"\"\"\n    hashed_password = hash_password(password)\n    user = database.get_user(username)\n    return user and user.password_hash == hashed_password",
        token_count=60,
    ),
    CodeChunk(
        chunk_id="test:api:1",
        file_path="api/endpoints.py",
        repo_name="test-repo",
        language="python",
        chunk_type="function",
        code_text="""@app.post("/api/login")
async def login_endpoint(credentials: LoginRequest):
    \"\"\"Handle user login requests\"\"\"
    if authenticate_user(credentials.username, credentials.password):
        return {"token": generate_jwt_token(credentials.username)}
    raise HTTPException(status_code=401, detail="Invalid credentials")""",
        start_line=25,
        end_line=31,
        symbol_name="login_endpoint",
        parent_class=None,
        imports=["fastapi", "authenticate_user"],
        context_text="Function: login_endpoint\n\n@app.post(\"/api/login\")\nasync def login_endpoint(credentials: LoginRequest):\n    \"\"\"Handle user login requests\"\"\"\n    if authenticate_user(credentials.username, credentials.password):\n        return {\"token\": generate_jwt_token(credentials.username)}\n    raise HTTPException(status_code=401, detail=\"Invalid credentials\")",
        token_count=70,
    ),
    CodeChunk(
        chunk_id="test:db:1",
        file_path="database/models.py",
        repo_name="test-repo",
        language="python",
        chunk_type="class",
        code_text="""class User:
    \"\"\"User model representing authenticated users\"\"\"
    def __init__(self, username: str, email: str, password_hash: str):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.now()""",
        start_line=5,
        end_line=11,
        symbol_name="User",
        parent_class=None,
        imports=["datetime"],
        context_text="Class: User\n\nclass User:\n    \"\"\"User model representing authenticated users\"\"\"\n    def __init__(self, username: str, email: str, password_hash: str):\n        self.username = username\n        self.email = email\n        self.password_hash = password_hash\n        self.created_at = datetime.now()",
        token_count=55,
    ),
    CodeChunk(
        chunk_id="test:utils:1",
        file_path="utils/crypto.py",
        repo_name="test-repo",
        language="python",
        chunk_type="function",
        code_text="""def hash_password(password: str) -> str:
    \"\"\"Hash a password using bcrypt\"\"\"
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()""",
        start_line=8,
        end_line=11,
        symbol_name="hash_password",
        parent_class=None,
        imports=["bcrypt"],
        context_text="Function: hash_password\n\ndef hash_password(password: str) -> str:\n    \"\"\"Hash a password using bcrypt\"\"\"\n    salt = bcrypt.gensalt()\n    return bcrypt.hashpw(password.encode(), salt).decode()",
        token_count=45,
    ),
    CodeChunk(
        chunk_id="test:frontend:1",
        file_path="frontend/LoginForm.tsx",
        repo_name="test-repo",
        language="typescript",
        chunk_type="function",
        code_text="""function LoginForm() {
    const handleSubmit = async (username: string, password: string) => {
        const response = await fetch('/api/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        return response.json();
    };
}""",
        start_line=15,
        end_line=23,
        symbol_name="LoginForm",
        parent_class=None,
        imports=["react"],
        context_text="Function: LoginForm\n\nfunction LoginForm() {\n    const handleSubmit = async (username: string, password: string) => {\n        const response = await fetch('/api/login', {\n            method: 'POST',\n            body: JSON.stringify({ username, password })\n        });\n        return response.json();\n    };\n}",
        token_count=65,
    ),
]

# Test queries that should find specific chunks
TEST_QUERIES = [
    {
        "query": "How do I authenticate a user?",
        "expected_chunks": ["test:auth:1", "test:api:1"],
        "description": "Authentication logic"
    },
    {
        "query": "password hashing implementation",
        "expected_chunks": ["test:utils:1"],
        "description": "Crypto/hashing function"
    },
    {
        "query": "user data model with email",
        "expected_chunks": ["test:db:1"],
        "description": "Data model"
    },
    {
        "query": "login API endpoint",
        "expected_chunks": ["test:api:1", "test:frontend:1"],
        "description": "API and frontend login"
    },
    {
        "query": "bcrypt password security",
        "expected_chunks": ["test:utils:1", "test:auth:1"],
        "description": "Security-related code"
    },
]


def benchmark_model(model_name: str, temp_db_path: str):
    """Benchmark a specific embedding model"""
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"{'='*60}\n")

    # Create store with this model
    store = EmbeddingStore(
        db_path=temp_db_path,
        collection_name=f"benchmark_{model_name.replace('/', '_')}",
        model_name=model_name
    )

    # Measure indexing time
    print(f"Indexing {len(SAMPLE_CHUNKS)} code chunks...")
    start_time = time.time()
    store.add_chunks(SAMPLE_CHUNKS)
    index_time = time.time() - start_time
    print(f"✓ Indexing completed in {index_time:.2f}s")

    # Test search quality
    total_correct = 0
    total_queries = 0
    query_times = []

    print(f"\nRunning {len(TEST_QUERIES)} test queries...\n")

    for test in TEST_QUERIES:
        query = test["query"]
        expected = test["expected_chunks"]
        description = test["description"]

        # Measure query time
        start_time = time.time()
        results = store.semantic_search(query, n_results=3)
        query_time = time.time() - start_time
        query_times.append(query_time)

        # Check if expected chunks are in top results
        result_ids = [r.chunk_id for r in results]
        found = [chunk_id for chunk_id in expected if chunk_id in result_ids]

        total_queries += 1
        if found:
            total_correct += 1
            status = "✓"
        else:
            status = "✗"

        print(f"{status} {description}")
        print(f"   Query: '{query}'")
        print(f"   Expected: {expected}")
        print(f"   Got top 3: {result_ids[:3]}")
        print(f"   Found: {found} ({query_time*1000:.1f}ms)\n")

    # Calculate metrics
    accuracy = (total_correct / total_queries) * 100
    avg_query_time = sum(query_times) / len(query_times)

    # Cleanup
    store.reset()

    return {
        "model": model_name,
        "index_time": index_time,
        "avg_query_time": avg_query_time,
        "accuracy": accuracy,
        "correct": total_correct,
        "total": total_queries,
    }


def main():
    """Run benchmark comparison"""
    print("\n" + "="*60)
    print("Embedding Model Comparison Benchmark")
    print("="*60)

    # Create temporary directory for databases
    temp_dir = tempfile.mkdtemp()

    try:
        models = [
            "sentence-transformers/all-MiniLM-L6-v2",          # Current default - fast
            "sentence-transformers/all-mpnet-base-v2",         # Best quality general
            "sentence-transformers/multi-qa-mpnet-base-dot-v1", # Optimized for search
            "sentence-transformers/msmarco-bert-base-dot-v5",  # Trained on search queries
            # "jinaai/jina-embeddings-v2-base-code",           # Code-specific (skip, poor results)
        ]

        results = []
        for model in models:
            result = benchmark_model(model, temp_dir)
            results.append(result)

        # Print comparison
        print("\n" + "="*60)
        print("RESULTS SUMMARY")
        print("="*60)

        for result in results:
            print(f"\nModel: {result['model']}")
            print(f"  Indexing Time:    {result['index_time']:.2f}s")
            print(f"  Avg Query Time:   {result['avg_query_time']*1000:.1f}ms")
            print(f"  Search Accuracy:  {result['accuracy']:.1f}% ({result['correct']}/{result['total']})")

        # Show winner
        print("\n" + "="*60)
        best_accuracy = max(results, key=lambda x: x['accuracy'])
        fastest_index = min(results, key=lambda x: x['index_time'])
        fastest_query = min(results, key=lambda x: x['avg_query_time'])

        print(f"Best Accuracy:       {best_accuracy['model']} ({best_accuracy['accuracy']:.1f}%)")
        print(f"Fastest Indexing:    {fastest_index['model']} ({fastest_index['index_time']:.2f}s)")
        print(f"Fastest Queries:     {fastest_query['model']} ({fastest_query['avg_query_time']*1000:.1f}ms)")
        print("="*60 + "\n")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
