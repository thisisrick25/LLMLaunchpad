---
phase: 4-persistent-chat-history-search
plan: 01
type: feature
autonomous: true
objective: Implement full-text search with SQLite FTS5, chat history persistence, and conversation management features.
context:
- @ROADMAP.md: Phase 6 requirements (misnumbered as phase 4 in request)
- @AGENTS.md: Database and search specifications
- @PROJECT.md: Data locations and model
- @server/src/llmlaunchpad/database.py: Existing FTS5 setup
- @server/src/llmlaunchpad/routes/conversations.py: Existing conversation routes
- @app/src/features/chat/chat.ts: Existing chat store
- @app/src/features/chat/ChatSidebar.svelte: Existing sidebar UI
- @app/src/shared/api.ts: Existing API client
- @app/src/shared/types.ts: Existing TypeScript types

Requirements from request:
- Full-text search (SQLite FTS5) on chat history
- Conversation export (JSON and Markdown formats)
- Auto-generated conversation titles with manual edit capability
- Conversation search with highlighting
- Infinite retention (no auto-deletion)
- Conversation sidebar with search/filter capabilities
- Message timestamps and role indicators

Success Criteria:
- Users can search conversation history and find relevant messages using FTS5
- Users can export conversations in JSON or Markdown format
- Conversation titles are auto-generated from first message and can be edited
- Search results highlight matching terms
- All existing chat functionality continues to work
- Sidebar search uses actual FTS5 message content search, not just title filtering

Deviation Handling:
- Rule 1: Auto-fix bugs (broken behavior, errors, incorrect output)
- Rule 2: Auto-add missing critical functionality (missing error handling, no input validation)
- Rule 3: Auto-fix blocking issues (missing dependency, wrong types, broken imports)
- Rule 4: Ask about architectural changes (significant structural modification)

Tasks:
1. Update ChatSidebar.svelte to use FTS5 search via chatStore.search() instead of client-side title filtering
2. Modify search results display to show conversations with matching messages and highlight search terms
3. Ensure search input properly triggers FTS5 search and displays loading states
4. Verify existing export functionality works (JSON and Markdown)
5. Confirm auto-generated conversation titles work correctly
6. Test that all existing chat functionality persists after changes