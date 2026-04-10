# Plan: Remove Message Count from Chat Sidebar

## TL;DR
Remove the message count display from the conversation list in the chat sidebar. Currently shows "Today · 4 msgs" - should just show "Today".

## Context
The user wants to simplify the chat sidebar by removing the message count indicator that appears next to each conversation's date.

## Work Objectives
- Remove `{conv.message_count} msgs` text from ChatSidebar.svelte
- Keep only the date formatting

## TODOs
- [ ] Remove message count from conversation list item display

### Task 1: Remove message count display
**File:** `app/src/features/chat/ChatSidebar.svelte`
**Line:** ~179
**Change:** 
- FROM: `{formatDate(conv.updated_at)} · {conv.message_count} msgs`
- TO: `{formatDate(conv.updated_at)}`

**Acceptance Criteria:**
- [ ] Message count no longer appears in conversation list
- [ ] Date still displays correctly
- [ ] UI layout remains clean

## Verification
- Open app and view chat sidebar
- Verify conversations show only date, not "X msgs"

## Commit Strategy
- Commit message: "ui: remove message count from chat sidebar"
- Files: `app/src/features/chat/ChatSidebar.svelte`
