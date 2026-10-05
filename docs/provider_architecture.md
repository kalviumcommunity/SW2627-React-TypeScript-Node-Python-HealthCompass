# HealthCompass Provider Architecture

HealthCompass now supports dual provider modes for embeddings and chat generation, allowing the system to work with only a Groq API key by default, with optional OpenAI support.

## Default / Free Setup

The default configuration requires only:

```
GROQ_API_KEY=your_groq_api_key_here
```

With this configuration:

- **Embeddings**: Local sentence-transformers model (`sentence-transformers/all-MiniLM-L6-v2`)
- **Chat**: Groq API (Llama models)
- **Cost**: Free for embeddings, Groq has free tier
- **Privacy**: All embeddings computed locally

## Optional Hybrid Setup

To use OpenAI embeddings instead of local ones:

```
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_PROVIDER=openai
```

With this configuration:

- **Embeddings**: OpenAI (`text-embedding-3-small`)
- **Chat**: Groq API (Llama models)
- **Cost**: OpenAI embedding costs apply

## Configuration Options

### Chat Provider

```bash
CHAT_PROVIDER=groq  # Default
CHAT_PROVIDER=openai  # Optional
```

**Groq (Default):**
```bash
GROQ_API_KEY=your_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
```

**OpenAI (Optional):**
```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o-mini
```

### Embedding Provider

```bash
EMBEDDING_PROVIDER=local  # Default
EMBEDDING_PROVIDER=openai  # Optional
```

**Local (Default):**
```bash
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**OpenAI (Optional):**
```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
```

## Important: Embedding Provider Isolation

**Embedding providers cannot be mixed within the same vector collection.**

This is because different embedding models use different vector spaces:

- Local sentence-transformers: 384 dimensions
- OpenAI text-embedding-3-small: 1536 dimensions
- OpenAI text-embedding-3-large: 3072 dimensions

The system automatically uses provider-specific collection names:

- `healthcompass_documents_local` for local embeddings
- `healthcompass_documents_openai` for OpenAI embeddings

**When switching embedding providers, you must re-index your documents.**

To re-index:

1. Change `EMBEDDING_PROVIDER` in your `.env` file
2. Delete the old ChromaDB collection (or use a new `CHROMA_DB_PATH`)
3. Run the ingestion pipeline again

Example:

```bash
# Switch from local to OpenAI embeddings
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_key

# Clear old data
rm -rf data/chroma_db

# Re-index documents
python -m healthcompass.ingestion.cli
```

## Architecture

### Default Mode (Groq + Local)

```
Documents
   ↓
Local Embeddings (sentence-transformers)
   ↓
ChromaDB (healthcompass_documents_local)
   ↓
User Query
   ↓
Local Query Embedding
   ↓
ChromaDB Similarity Search
   ↓
Top-K Relevant Chunks
   ↓
Context Injection
   ↓
Groq LLM
   ↓
Grounded Answer + Sources
```

### Optional Hybrid Mode (Groq + OpenAI)

```
Documents
   ↓
OpenAI Embeddings
   ↓
ChromaDB (healthcompass_documents_openai)
   ↓
User Query
   ↓
OpenAI Query Embedding
   ↓
ChromaDB Similarity Search
   ↓
Top-K Relevant Chunks
   ↓
Context Injection
   ↓
Groq LLM
   ↓
Grounded Answer + Sources
```

## Provider Abstraction

The system uses a clean provider abstraction:

```python
from healthcompass.providers import get_embedding_provider, get_chat_provider

# Get configured embedding provider
embedding_provider = get_embedding_provider()
embeddings = embedding_provider.embed_documents(texts)

# Get configured chat provider
chat_provider = get_chat_provider()
answer = chat_provider.generate(prompt)
```

Both providers expose the same interface regardless of which backend is configured.

## API Changes

The `/health` endpoint now reports provider configuration:

```json
{
  "status": "healthy",
  "chat_provider": "groq",
  "embedding_provider": "local",
  "chat_model": "llama-3.3-70b-versatile",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

## Migration from OpenAI-Only Setup

If you previously used OpenAI for both embeddings and chat:

1. Add `GROQ_API_KEY` to your `.env`
2. Set `CHAT_PROVIDER=groq`
3. Set `EMBEDDING_PROVIDER=local` (default)
4. Re-index documents to use local embeddings

Your system will now:
- Use local embeddings (no OpenAI cost)
- Use Groq for chat generation (often cheaper/faster)
- Maintain the same RAG pipeline and grounding behavior

## Testing

Tests are provided for the provider architecture:

```bash
pytest tests/test_providers.py
```

Tests mock all external API calls and do not require real API keys.
