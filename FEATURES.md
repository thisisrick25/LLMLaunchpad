# LLMLaunchpad - Future Features & Enhancements

This document tracks potential features and enhancements for future development.

## Search & Retrieval

### Semantic Search with pgvector

**Current:** SQLite with FTS5 full-text search for exact keyword matching

**Proposed Enhancement:**
Add vector-based semantic search alongside FTS5 for conceptually similar content discovery.

**Implementation Sketch:**

```python
# Add pgvector for semantic search
# Keep SQLite for chat history
# Hybrid: FTS5 for exact, pgvector for semantic

async def search_chats(query: str, semantic: bool = False):
    if semantic:
        # Generate embedding
        query_vec = await embed(query)
        # Vector similarity search in pgvector
        return await vector_search(query_vec)
    else:
        # FTS5 search in SQLite
        return await fts5_search(query)
```

**Benefits:**
- Find conversations by concept, not just keywords
- "Find chats about memory" → finds "context window", "conversation history"
- Useful for RAG (Retrieval Augmented Generation) with chat history

**Embedding Model:**
- `all-MiniLM-L6-v2` (23MB) → 384-dim vectors
- Fast, small, perfect for local use

**Storage Impact:**
- ~1.5KB per message (384-dim float32)
- 100K messages ≈ 150MB for vectors

**When to Implement:**
- When users request "find similar conversations"
- For semantic topic clustering
- When adding RAG with chat history context

---

## Model Management

### Model Quantization Tools
**Idea:** Built-in GGUF quantization - convert FP16 models to Q4_K_M, Q5_K_M, etc.
**Benefit:** Users can optimize models for their hardware without command line tools.

### Model Comparison
**Idea:** Side-by-side chat with two models responding to same prompt.
**Benefit:** A/B testing which model works better for specific tasks.

### Model Library / Presets
**Idea:** Pre-configured model profiles with optimal settings per model.
**Benefit:** One-click setup for popular models (temperature, context, GPU layers).

---

## Chat Features

### Chat Templates & Prompt Library
**Idea:** Save and reuse system prompts; categorized prompt templates (coding, writing, analysis).
**Benefit:** Consistent personality and faster workflow.

### Voice Input/Output (TTS/STT)
**Idea:** Speech-to-text for input, text-to-speech for responses.
**Benefit:** Hands-free interaction, accessibility.

### Image Understanding (Multimodal)
**Idea:** Support vision models (LLaVA, BakLLaVA) for image chat.
**Benefit:** Analyze screenshots, photos, diagrams.

### Chat Sharing & Export
**Idea:** Share chats via link (local network), export to PDF/Word with formatting.
**Benefit:** Collaboration and documentation.

---

## RAG & Knowledge Management

### Document Upload & Indexing
**Idea:** Upload PDFs, Markdown, text files; index for RAG queries.
**Benefit:** Chat with your documents.

### Knowledge Base Management
**Idea:** Organize documents into collections/projects; choose which KB to query.
**Benefit:** Context-aware responses for different domains.

### Web Scraping Context
**Idea:** Paste URLs to fetch and include webpage content in chat context.
**Benefit:** Current information without copy-paste.

---

## Performance & Hardware

### GPU Memory Visualization
**Idea:** Real-time VRAM usage graph, layer allocation visualization.
**Benefit:** Optimize offloading settings visually.

### Performance Profiler
**Idea:** Track tokens/sec, time-to-first-token, memory usage per session.
**Benefit:** Identify bottlenecks, compare model performance.

### Dynamic Batching
**Idea:** Batch multiple requests for better GPU utilization.
**Benefit:** Higher throughput for multi-user scenarios.

---

## Integrations

### MCP (Model Context Protocol)
**Idea:** Support Anthropic's MCP for tool calling (file system, web search, APIs).
**Benefit:** Extensible tool ecosystem.

### Cloud Model Switching
**Idea:** Seamless fallback to OpenAI/Claude when local model can't handle request.
**Benefit:** Best of both worlds - local privacy + cloud power.

### Plugin System
**Idea:** Python/JS plugins for custom tools, preprocessors, postprocessors.
**Benefit:** Community extensions.

---

## Developer Tools

### Prompt Playground
**Idea:** Test prompts with different models side-by-side, save favorites.
**Benefit:** Prompt engineering without chat overhead.

### Token Usage Tracking
**Idea:** Track tokens used per conversation, model, day.
**Benefit:** Cost estimation for cloud, performance analysis.

### Debug Mode
**Idea:** Show raw API requests/responses, timing breakdown.
**Benefit:** Troubleshooting and learning.

---

## Backup & Migration

### Import from Other Platforms
**Idea:** Import ChatGPT, Claude, Ollama conversation exports.
**Benefit:** Consolidate chat history.

### Cloud Backup Options
**Idea:** Optional encrypted backup to S3, Google Drive, etc.
**Benefit:** Data safety without vendor lock-in.

---

## How to Add a New Feature Idea

1. Add a new section with the feature name
2. Describe current state (if any)
3. Proposed enhancement
4. Benefits
5. Implementation notes (optional)

## Feature Prioritization

### High Impact / Low Effort
- [ ] Chat templates/prompts library
- [ ] Model presets/profiles
- [ ] Export to PDF

### High Impact / High Effort
- [ ] Semantic search (pgvector)
- [ ] Document upload & RAG
- [ ] MCP tool support

### Nice to Have
- [ ] Voice input/output
- [ ] GPU memory visualization
- [ ] Theme customization
