# Implementation Plan: UI-TARS Vision-Guided Job Scraping

## Tasks

- [ ] 1. Set up UI-TARS model client
  - [ ] 1.1 Create `agents/ui_tars_agent/model_client.py`
  - [ ] 1.2 Implement Ollama client for local UI-TARS
  - [ ] 1.3 Implement Hugging Face API fallback
  - [ ] 1.4 Add screenshot encoding and action parsing

- [ ] 2. Create UI-TARS Browser Agent
  - [ ] 2.1 Create `agents/ui_tars_agent/agent.py`
  - [ ] 2.2 Implement `navigate_to_search(portal_url, query, location)`
  - [ ] 2.3 Implement screenshot capture + analysis loop
  - [ ] 2.4 Implement action execution via PyAutoGUI
  - [ ] 2.5 Implement popup detection and dismissal
  - [ ] 2.6 Implement scroll-and-extract loop

- [ ] 3. Create prompts and configurations
  - [ ] 3.1 Create `agents/ui_tars_agent/prompts.py`
  - [ ] 3.2 Define navigation prompts for each portal type
  - [ ] 3.3 Create `agents/ui_tars_agent/config.py`

- [ ] 4. Integrate with existing pipeline
  - [ ] 4.1 Modify `agents/chat_agent/agent.py` to use UI-TARS
  - [ ] 4.2 Keep fallback to existing browser agent
  - [ ] 4.3 Add UI-TARS status endpoint to `api/main.py`

- [ ] 5. Test and validate
  - [ ] 5.1 Test navigation on Naukri
  - [ ] 5.2 Test on Indeed, LinkedIn, CutShort
  - [ ] 5.3 Test popup handling
  - [ ] 5.4 Test scroll and pagination
  - [ ] 5.5 Verify job extraction and saving

## Notes
- UI-TARS model runs locally via Ollama (free, unlimited)
- Fallback to Mistral Pixtral / Gemini if Ollama unavailable
- Keep CloakBrowser for stealth
- Keep existing JavaScript extraction (faster than vision)
