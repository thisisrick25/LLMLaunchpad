# LLMLaunchpad - Known Issues & Next Steps

## Priority: Critical

### 1. Fix XSS Vulnerability
- **File**: `app/src/features/chat/ChatPanel.svelte`
- **Issue**: `formatContent()` uses `{@html}` without sanitization
- **Fix**: Add DOMPurify or similar HTML sanitizer

## Priority: High

### 2. Add Apple Silicon Support
- **File**: `server/src/llmlaunchpad/hardware.py`
- **Issue**: No Metal/MPS detection for Mac GPU acceleration
- **Fix**: Detect Apple Silicon and report GPU layers for Metal

### 3. Fix Race Conditions
- **File**: `server/src/llmlaunchpad/llama.py`
- **Issue**: Global `_llama_server` variable is not thread-safe
- **Fix**: Use asyncio locks or proper state management

### 4. Database Connection Pooling
- **File**: `server/src/llmlaunchpad/database.py`
- **Issue**: No connection pooling, potential FTS sync issues
- **Fix**: Use aiosqlite properly with connection pool

## Priority: Medium

### 5. Implement Actual Abort
- **File**: `server/src/llmlaunchpad/routes/chat.py`
- **Issue**: Abort endpoint is currently a no-op
- **Fix**: Actually cancel the ongoing request to llama.cpp

### 6. Add Loading States
- **File**: `app/src/features/services/ServiceControls.svelte`
- **Issue**: No visual feedback during server start/stop
- **Fix**: Add spinner/disabled state while operations are in progress

### 7. Add Download Progress
- **File**: `app/src/features/models/ModelSelector.svelte`
- **Issue**: No progress indicator for model downloads
- **Fix**: Stream download progress from backend to frontend

### 8. Add Model Size Warnings
- **File**: `app/src/features/models/ModelSelector.svelte`
- **Issue**: No warning when model may exceed available VRAM/RAM
- **Fix**: Compare model size against detected hardware

## Priority: Low

### 9. Add Dark Mode Toggle
- **Issue**: No way to switch between light/dark themes
- **Fix**: Add theme toggle in UI, persist preference

### 10. Add Basic Tests
- **Directory**: `server/tests/`
- **Issue**: Zero tests exist
- **Fix**: Add API route tests at minimum

---

## Completed Phases

- [x] Phase 1: Architecture Planning
- [x] Phase 2: Project Skeleton
- [x] Phase 3: Backend Implementation
- [x] Phase 4: Frontend Implementation
- [x] Phase 5: Tauri Integration
- [x] Phase 6: Packaging
