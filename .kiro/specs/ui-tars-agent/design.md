# UI-TARS Vision-Guided Job Scraping Agent

## Overview

Replace the current autonomous browser agent with **UI-TARS** (ByteDance's open-source GUI agent model) for fully adaptive, self-healing job portal scraping. UI-TARS analyzes screenshots and returns precise action coordinates — no hardcoded selectors needed.

## Architecture

```
User Request ("Find Python jobs in Bangalore")
    ↓
Chat Agent (existing - intent routing, skill matching)
    ↓
UI-TARS Browser Agent (NEW)
    ├── Takes screenshot of portal
    ├── UI-TARS model decides: click/type/scroll coordinates
    ├── Executes via PyAutoGUI on CloakBrowser
    └── Extracts jobs via existing JavaScript extraction
    ↓
Job Saver (existing - dedup + ATS scoring)
    ↓
Dashboard (existing)
```

## Why UI-TARS Over Current Approach

| Feature | Current (Pixtral+Gemini) | UI-TARS |
|---------|--------------------------|---------|
| Action precision | Returns JSON with coordinates | Returns exact (x,y) + action type natively |
| Model specialization | General vision model | Trained specifically for GUI automation |
| Local execution | No (API only) | ✅ Yes via Ollama (free, unlimited) |
| Rate limits | Mistral: 2 RPM, Gemini: 15 RPM | None (local) |
| Cost | API calls consume tokens | Free (runs on your GPU/CPU) |
| Selector dependency | Partial (still uses JS extraction) | Zero (pure vision-guided) |
| Self-healing | Limited | Full (sees page like a human) |

## Implementation Plan

### Phase 2.5: UI-TARS Integration (Estimated: 1 week)

#### Step 1: Set Up UI-TARS Model
- Install Ollama: `ollama pull ui-tars` (or use Hugging Face API as fallback)
- Model: `bytedance-research/UI-TARS-7B-DPO` (7B parameters, runs on 8GB VRAM)
- Alternative: `ui-tars-72b` for better accuracy (needs 48GB VRAM)

#### Step 2: Create UI-TARS Agent Module
- File: `agents/ui_tars_agent/agent.py`
- Methods:
  - `navigate_to_search(portal_url, query, location)` — Main entry point
  - `analyze_screenshot(screenshot)` — Call UI-TARS model
  - `execute_action(action)` — PyAutoGUI click/type/scroll at coordinates
  - `extract_jobs()` — Reuse existing JS extraction after navigation
  - `handle_popup()` — Detect and dismiss popups via vision

#### Step 3: UI-TARS Prompt Engineering
- System prompt: "You are a browser automation agent. Navigate to job search results."
- Input: Screenshot + goal description
- Output: `{"action": "click", "coordinate": [x, y]}` or `{"action": "type", "coordinate": [x, y], "text": "..."}`

#### Step 4: Integration with Existing Pipeline
- Replace `autonomous_agent.py` calls with `ui_tars_agent`
- Keep CloakBrowser for stealth (UI-TARS controls it)
- Keep existing JavaScript extraction (faster than vision extraction)
- Keep job saver, chat agent, dashboard unchanged

#### Step 5: Fallback Strategy
- Primary: Local Ollama (free, unlimited)
- Fallback: Mistral Pixtral (if Ollama unavailable)
- Fallback: Gemini 2.5 Flash (if both fail)

## Technical Requirements

### Hardware
- **Minimum:** 8GB VRAM (GPU) or 16GB RAM (CPU, slower)
- **Recommended:** 16GB+ VRAM for 7B model
- **Current system:** Windows, Python 3.12 — compatible

### Software
- Ollama (https://ollama.ai) — runs UI-TARS locally
- PyAutoGUI (already installed) — executes actions
- CloakBrowser (already installed) — stealth browser
- Pillow (already installed) — screenshot processing

### Model Options
| Model | Size | VRAM | Quality | Speed |
|-------|------|------|---------|-------|
| UI-TARS-7B-DPO | 7B | 8GB | Good | Fast |
| UI-TARS-72B-DPO | 72B | 48GB | Excellent | Slow |
| Hugging Face API | Cloud | N/A | Good | Medium |

## Files to Create/Modify

### New Files
- `agents/ui_tars_agent/__init__.py`
- `agents/ui_tars_agent/agent.py` — Main UI-TARS agent
- `agents/ui_tars_agent/model_client.py` — Ollama/HF API client
- `agents/ui_tars_agent/prompts.py` — System prompts for navigation

### Modified Files
- `agents/browser_agent/autonomous_agent.py` — Replace with UI-TARS calls
- `agents/chat_agent/agent.py` — Route to UI-TARS instead of old browser agent
- `api/main.py` — Add UI-TARS status endpoint

### Unchanged Files
- `agents/browser_agent/browser_controller.py` — CloakBrowser wrapper (keep)
- `agents/job_saver.py` — Job saving (keep)
- `database/models.py` — Database schema (keep)
- `frontend/` — UI (keep)

## Success Criteria

- [ ] UI-TARS navigates to search results on Naukri without selectors
- [ ] Handles popup dismissal automatically
- [ ] Scrolls to load more jobs when needed
- [ ] Works on all 8+ portals (Naukri, Indeed, LinkedIn, etc.)
- [ ] No hardcoded selectors in navigation logic
- [ ] Runs locally via Ollama (free, no rate limits)
- [ ] Falls back to Mistral/Gemini if Ollama unavailable
- [ ] Integrates seamlessly with existing chat interface

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| UI-TARS model too slow on CPU | Use 7B model, or fallback to API |
| Model returns invalid coordinates | Add validation + retry logic |
| Ollama not available on Windows | Use Hugging Face Inference API as fallback |
| Model doesn't understand Indian job portals | Fine-tune prompt with portal-specific examples |

## Next Steps

1. **Install Ollama** on Windows
2. **Pull UI-TARS model**: `ollama pull ui-tars`
3. **Create `agents/ui_tars_agent/`** module
4. **Test navigation** on Naukri
5. **Integrate** with existing pipeline
6. **Test all portals**

---

*Created: 2026-05-18*
*Status: Planning — awaiting approval to begin implementation*
