---
phase: 6-conversation-history-search
plan: 01
type: feature
objective: Implement persistent chat history with search and export capabilities.
context:
- @ROADMAP.md: Phase 6 requirements
- @AGENTS.md: Database and search specifications
- @PROJECT.md: Data locations and model
- @server/src/llmlaunchpad/database.py: Existing FTS5 setup
- @server/src/llmlaunchpad/routes/conversations.py: Existing conversation routes
- @app/src/features/chat/chat.ts: Existing chat store
- @app/src/features/chat/ChatSidebar.svelte: Existing sidebar UI
- @app/src/shared/api.ts: Existing API client
- @app/src/shared/types.ts: Existing TypeScript types

Requirements from ROADMAP.md:
- Full-text search (SQLite FTS5) on chat history
- Conversation export (JSON and Markdown formats)
- Auto-generated conversation titles with manual edit capability
- Conversation search with highlighting
- Infinite retention (no auto-deletion)
- Conversation sidebar with search/filter capabilities
- Message timestamps and role indicators

Success Criteria:
- Users can search conversation history and find relevant messages
- Users can export conversations in JSON or Markdown format
- Conversation titles are auto-generated from first message and can be edited
- Search results highlight matching terms
- All existing chat functionality continues to work