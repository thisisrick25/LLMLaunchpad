---
phase: 3-basic-chat-interface
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true
requirements: [CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06]
user_setup: []

must_haves:
  truths:
    - "User can send a message and receive a streaming response"
    - "Messages persist in SQLite database after refresh"
    - "Conversation history is maintained and accessible"
    - "Auto-scrolling works when new messages arrive"
    - "Error handling displays meaningful messages to user"
  artifacts:
    - path: "app/src/features/chat/ChatPanel.svelte"
      provides: "Main chat interface with message display and input"
      min_lines: 100
    - path: "app/src/features/chat/ChatSidebar.svelte"
      provides: "Conversation history list"
      min_lines: 150
    - path: "app/src/features/chat/chat.ts"
      provides: "Chat state management with streaming logic"
      exports: ["sendMessage", "loadConversation", "newConversation"]
    - path: "server/src/llmlaunchpad/routes/chat.py"
      provides: "Chat completion endpoints with SSE streaming"
      exports: ["/chat/completions POST", "/chat/abort POST"]
    - path: "server/src/llmlaunchpad/database.py"
      provides: "SQLite database with conversations and messages tables"
      contains: "CREATE TABLE conversations"
    - path: "app/src/shared/types.ts"
      provides: "TypeScript types for chat messages and conversations"
      exports: ["ChatMessage", "ChatRequest", "ChatResponse", "StreamChunk"]
  key_links:
    - from: "app/src/features/chat/chat.ts"
      to: "/chat/completions"
      via: "api.streamChat() call"
      pattern: "api\\.streamChat"
    - from: "app/src/features/chat/ChatPanel.svelte"
      to: "app/src/features/chat/chat.ts"
      via: "chatStore.sendMessage() call"
      pattern: "chatStore\\.sendMessage"
    - from: "server/src/llmlaunchpad/routes/chat.py"
      to: "server/src/llmlaunchpad/database.py"
      via: "save_message() function calls"
      pattern: "save_message"
    - from: "app/src/features/chat/chat.ts"
      to: "server/src/llmlaunchpad/database.py"
      via: "api.getConversation() and api.getConversations() calls"
      pattern: "api\\.getConversation"

<objective>
Verify and complete the basic chat interface with message display, streaming responses, and conversation persistence using SQLite.

Purpose: Enable users to have conversations with locally running models through a functional UI.
Output: Working chat interface that sends messages, displays streaming responses, and persists conversations.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
@$HOME/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md

# Current implementation status
@app/src/features/chat/ChatPanel.svelte
@app/src/features/chat/ChatSidebar.svelte
@app/src/features/chat/chat.ts
@server/src/llmlaunchpad/routes/chat.py
@server/src/llmlaunchpad/database.py
@app/src/shared/api.ts
@app/src/shared/types.ts
</context>

<tasks>

<task type="auto">
  <name>Task 1: Verify backend chat API streaming functionality</name>
  <files>server/src/llmlaunchpad/routes/chat.py</files>
  <action>
    Verify the chat completion endpoint properly handles streaming responses:
    1. Check that /chat/completions POST endpoint accepts stream=true parameter
    2. Verify SSE streaming format is correctly implemented (data: {...}\n\n)
    3. Confirm that assistant responses are saved to database after streaming completes
    4. Test error handling for when llama-server is not running
    5. Verify conversation ID generation and persistence
    Reference existing implementation to ensure it meets requirements.
  </action>
  <verify>
    python -m pytest server/tests/test_chat_errors.py -xvs
  </verify>
  <done>
    Backend chat API correctly handles streaming requests, saves messages to database, and returns proper SSE format.
  </done>
</task>

<task type="auto">
  <name>Task 2: Verify frontend chat store streaming logic</name>
  <files>app/src/features/chat/chat.ts</files>
  <action>
    Examine and verify the chat store's sendMessage method properly handles:
    1. Adding user message to messages array
    2. Setting isStreaming flag and clearing streamingContent
    3. Calling api.streamChat with correct parameters
    4. Processing StreamChunk objects and updating streamingContent
    5. Adding assistant message when stream completes
    6. Error handling and resetting streaming state
    7. Refreshing conversations list after message exchange
    Ensure the implementation correctly interfaces with the backend API.
  </action>
  <verify>
    cd app && npx svelte-kit sync && echo "Frontend build verification: Store compiles without errors"
  </verify>
  <done>
    Frontend chat store correctly manages message state, handles streaming responses, and updates UI appropriately.
  </done>
</task>

<task type="checkpoint:human-verify">
  <name>Task 3: Verify end-to-end chat functionality</name>
  <what-built>
    Complete chat interface with backend API, frontend store, and UI components
  </what-built>
  <how-to-verify>
    1. Start the backend server: python -m server.src.llmlaunchpad.main
    2. Start the frontend dev server: npm run dev (in app directory)
    3. Open browser to http://localhost:5173
    4. Verify backend status shows llama-server is running (or start it via UI)
    5. Type a message in the chat input and press Enter
    6. Observe:
       - User message appears immediately in chat
       - Streaming response appears character-by-character with cursor animation
       - When complete, assistant message is added to chat history
       - Chat auto-scrolls to show latest messages
    7. Refresh the page and verify conversation persists
    8. Test sending multiple messages in same conversation
    9. Verify error handling by stopping llama-server and attempting to send message
    10. Test New Chat button clears current conversation
    11. Verify chat sidebar shows conversation history
    12. Test conversation export functionality (JSON/Markdown)
  </resume-signal>
    Type "approved" if all functionality works correctly, or describe any issues encountered
  </resume-signal>
</task>

</tasks>

<verification>
Verify that all must-haves are satisfied:
- User can send message and receive streaming response (Task 3)
- Messages persist in SQLite database after refresh (Task 3)
- Conversation history is maintained and accessible (Task 3)
- Auto-scrolling works when new messages arrive (Task 3, ChatPanel.svelte afterUpdate)
- Error handling displays meaningful messages to user (Task 3)
</verification>

<success_criteria>
Chat interface is fully functional:
- Messages send and receive with streaming display
- Conversations persist across page refreshes via SQLite
- Auto-scrolling shows latest messages
- Error states are handled gracefully
- Conversation history accessible via sidebar
</success_criteria>

<output>
After completion, create .planning/phases/3-basic-chat-interface/3-basic-chat-interface-01-SUMMARY.md
</output>