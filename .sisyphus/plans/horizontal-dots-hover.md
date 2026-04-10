# Plan: Three-Dot Menu - Horizontal & Hover-Only

## TL;DR
Change the conversation actions menu from vertical dots to horizontal dots, and make it appear only when hovering over a chat item.

## Context
User wants to improve the chat sidebar UI by:
1. Changing three-dot menu icon from vertical (⋮) to horizontal (⋯) orientation
2. Making the menu button appear only on hover (currently always visible)

## Work Objectives
- Change SVG icon from vertical to horizontal dots
- Add hover state visibility for the menu button
- Ensure menu still functions correctly when visible

## Analysis

### Current Implementation
- **Location:** Lines 182-230 in `ChatSidebar.svelte`
- **Current icon:** Vertical dots (`M12 5v.01M12 12h.01M12 19h.01`)
- **Visibility:** Always visible

### Changes Needed
1. **SVG Path:** Change from vertical to horizontal dots
   - Current: Three dots stacked vertically
   - New: Three dots arranged horizontally
   
2. **Hover Visibility:**
   - Add CSS to hide button by default
   - Show on parent hover
   - Keep visible when menu is open (activeActionsId === conv.id)

## TODOs

### Task 1: Change icon to horizontal dots
**File:** `app/src/features/chat/ChatSidebar.svelte`
**Lines:** ~194-199

**Current SVG path:**
```svg
<path
  stroke-linecap="round"
  stroke-linejoin="round"
  stroke-width="2"
  d="M12 5v.01M12 12h.01M12 19h.01"
/>
```

**New SVG path (horizontal):**
```svg
<path
  stroke-linecap="round"
  stroke-linejoin="round"
  stroke-width="2"
  d="M5 12h.01M12 12h.01M19 12h.01"
/>
```

### Task 2: Make button hover-only visible
**File:** `app/src/features/chat/ChatSidebar.svelte`
**Lines:** ~183-201

**Current button classes:**
```
class="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-md"
```

**New button classes:**
```
class="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
```

**Parent container needs:**
Add `group` class to the parent div (around line 173-181) to enable group-hover.

### Task 3: Keep visible when menu is open
Add conditional class: `opacity-100` when `activeActionsId === conv.id`

**Acceptance Criteria:**
- [ ] Three dots appear horizontally (⋯) instead of vertically (⋮)
- [ ] Menu button hidden by default, shows on hover
- [ ] Menu button stays visible when dropdown menu is open
- [ ] Dropdown menu still functions correctly
- [ ] Smooth opacity transition on hover

## Implementation Details

### SVG Path Reference
- **Vertical dots:** `M12 5v.01M12 12h.01M12 19h.01` (y-axis variation)
- **Horizontal dots:** `M5 12h.01M12 12h.01M19 12h.01` (x-axis variation)

### CSS Classes for Hover
- Parent: `group` (enables group-hover on children)
- Button default: `opacity-0` (hidden)
- Button hover: `group-hover:opacity-100` (visible on parent hover)
- Button active: `opacity-100` (visible when menu open)
- Transition: `transition-opacity` (smooth fade)

## Verification
1. Load app with chat sidebar
2. Verify dots are horizontal (⋯)
3. Verify menu button hidden on non-hovered items
4. Hover over conversation - button should appear
5. Click button - menu opens, button stays visible
6. Click elsewhere - menu closes, button hides

## Commit Strategy
- Commit message: `ui: change menu to horizontal dots, show on hover`
- Files: `app/src/features/chat/ChatSidebar.svelte`
