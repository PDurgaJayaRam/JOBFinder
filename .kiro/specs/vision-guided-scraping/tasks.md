# Implementation Plan: Vision-Guided Adaptive Scraping

## Overview

This implementation plan transforms the job scraping system from brittle CSS selectors to adaptive vision-guided navigation. The system uses AI vision models (Mistral Pixtral 12B and Gemini 2.5 Flash) to analyze screenshots and decide navigation actions, executes via PyAutoGUI + CloakBrowser, and combines vision-guided navigation with JavaScript-based extraction for optimal performance.

The implementation follows a component-based architecture with 6 main components: Vision Agent, Browser Controller (enhanced), Hybrid Extractor, Rate Limiter, Portal Adapter, and Scraping Orchestrator. The system supports 8 major job portals with zero portal-specific navigation logic.

## Tasks

- [ ] 1. Set up core data models and type definitions
  - [ ] 1.1 Create data models module with Pydantic models
    - Create `agents/vision_scraper/models.py`
    - Implement `ActionType` enum (CLICK, TYPE, SCROLL, WAIT, GOAL_ACHIEVED, ERROR)
    - Implement `ActionDecision` model with validation rules
    - Implement `NavigationStatus` enum (SUCCESS, FAILED, RATE_LIMITED, TIMEOUT)
    - Implement `NavigationResult` model
    - Implement `JobData` model with field validation
    - Implement `ScrapingResult` model
    - Implement `PageState` model
    - Implement `ActionResult` model
    - Add validation methods for coordinates, URLs, and required fields
    - _Requirements: 1.2, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 9.1, 9.2_

  - [ ]* 1.2 Write property test for data model validation
    - **Property 5: Extraction Completeness**
    - **Validates: Requirements 5.5, 6.1, 6.2, 6.3, 6.4, 6.5**
    - Generate random JobData instances
    - Verify all required fields are non-empty
    - Verify source_url and apply_url are valid URLs
    - Verify source matches portal name
    - Verify extracted_at is ISO 8601 format

  - [ ]* 1.3 Write property test for action decision validation
    - **Property 4: Action Validity**
    - **Validates: Requirements 9.2, 9.6**
    - Generate random ActionDecision instances with various action types
    - For CLICK/TYPE actions, verify coordinates are within bounds
    - For TYPE actions, verify text is non-empty
    - For SCROLL actions, verify direction and amount are valid
    - Verify confidence is between 0.0 and 1.0

- [ ] 2. Implement Rate Limiter component
  - [ ] 2.1 Create Rate Limiter class
    - Create `agents/vision_scraper/rate_limiter.py`
    - Implement `RateLimiter` class with provider tracking
    - Implement `check_availability(provider)` method
    - Implement `wait_for_capacity(provider)` method
    - Implement `record_request(provider)` method
    - Implement `get_next_available_provider()` method
    - Implement `get_rate_limit_status()` method
    - Add sliding window rate limit tracking (60-second window)
    - Configure Mistral limit: 2 RPM, Gemini limit: 15 RPM
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 2.2 Write property test for rate limit compliance
    - **Property 2: Rate Limit Compliance**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.6**
    - Generate sequence of API calls with random timing
    - Verify Mistral never exceeds 2 requests per 60-second window
    - Verify Gemini never exceeds 15 requests per 60-second window
    - Verify counters reset after 60 seconds
    - Verify wait times are calculated correctly

  - [ ]* 2.3 Write unit tests for Rate Limiter
    - Test check_availability returns correct boolean
    - Test record_request updates counters
    - Test get_next_available_provider fallback logic
    - Test rate limit status reporting
    - Test edge case: both providers at capacity

- [ ] 3. Implement Multi-Provider AI Client
  - [ ] 3.1 Create Multi-Provider AI Client class
    - Create `agents/vision_scraper/multi_provider_client.py`
    - Implement `MultiProviderAIClient` class
    - Implement `vision_complete(image, prompt, model, provider)` method
    - Add Mistral Pixtral 12B integration
    - Add Gemini 2.5 Flash integration
    - Implement base64 image encoding
    - Implement JSON response parsing
    - Add retry logic (up to 2 retries on failure)
    - Integrate with Rate Limiter for provider selection
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [ ]* 3.2 Write property test for provider fallback
    - **Property 7: Provider Fallback**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    - Simulate Mistral rate limit scenarios
    - Verify automatic fallback to Gemini
    - Verify request succeeds without failing
    - Verify both providers can be used in sequence

  - [ ]* 3.3 Write unit tests for Multi-Provider AI Client
    - Test vision_complete with Mistral provider
    - Test vision_complete with Gemini provider
    - Test retry logic on API failure
    - Test JSON parsing of vision responses
    - Test error handling for invalid responses

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Enhance Browser Controller with PyAutoGUI support
  - [ ] 5.1 Add coordinate-based action methods to Browser Controller
    - Modify `agents/browser_agent/browser_controller.py`
    - Add `click_at_coordinates(x, y)` method using PyAutoGUI
    - Add `type_text_at_coordinates(x, y, text)` method
    - Add `scroll_page(direction, amount)` method
    - Add `get_page_state()` method returning PageState
    - Add `is_browser_crashed()` method
    - Enhance `take_screenshot()` to handle browser crash detection
    - Add ActionResult return types to all action methods
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [ ]* 5.2 Write property test for screenshot capture reliability
    - **Property 9: Screenshot Capture Reliability**
    - **Validates: Requirements 4.2, 12.2, 12.3, 12.4**
    - Test screenshot capture in various browser states
    - Verify valid base64 string returned when browser is running
    - Verify error returned when browser is crashed
    - Verify screenshot completes within 5 seconds

  - [ ]* 5.3 Write unit tests for Browser Controller enhancements
    - Test click_at_coordinates executes PyAutoGUI click
    - Test type_text_at_coordinates clicks then types
    - Test scroll_page scrolls in correct direction
    - Test get_page_state returns accurate PageState
    - Test browser crash detection

- [ ] 6. Implement Vision Agent component
  - [ ] 6.1 Create Vision Agent class with navigation logic
    - Create `agents/vision_scraper/vision_agent.py`
    - Implement `VisionAgent` class
    - Implement `navigate_to_search(portal_url, query, location)` method
    - Implement navigation loop with max_steps limit (10 steps)
    - Implement goal-based prompt generation
    - Implement screenshot capture at each step
    - Implement action execution via Browser Controller
    - Add navigation result tracking (steps, actions, screenshots)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ] 6.2 Implement screenshot analysis and action decision
    - Implement `analyze_screenshot(screenshot, goal, context)` method
    - Build structured vision prompts with goal and available actions
    - Call Multi-Provider AI Client with rate limit awareness
    - Parse vision model JSON responses into ActionDecision
    - Implement retry logic for invalid JSON responses
    - Add confidence score validation
    - _Requirements: 1.2, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7_

  - [ ] 6.3 Implement action execution and validation
    - Implement `execute_action(action)` method
    - Validate ActionDecision before execution
    - Execute CLICK actions via Browser Controller
    - Execute TYPE actions via Browser Controller
    - Execute SCROLL actions via Browser Controller
    - Handle WAIT actions with appropriate delays
    - Handle GOAL_ACHIEVED status
    - Handle ERROR status with descriptive messages
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [ ] 6.4 Implement popup detection and dismissal
    - Implement `handle_popup()` method
    - Detect popups, overlays, cookie banners in screenshots
    - Implement dismiss strategies (close button, ESC key, click outside)
    - Retry dismissal up to 3 times
    - Return success/failure status
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 6.5 Write property test for navigation termination
    - **Property 1: Navigation Termination**
    - **Validates: Requirements 1.3, 1.5, 1.6, 1.7**
    - Generate random portal URLs, queries, and locations
    - Verify navigation terminates within max_steps
    - Verify final status is SUCCESS, FAILED, or TIMEOUT
    - Verify steps_taken <= max_steps

  - [ ]* 6.6 Write unit tests for Vision Agent
    - Test navigate_to_search completes successfully
    - Test analyze_screenshot returns valid ActionDecision
    - Test execute_action handles all action types
    - Test handle_popup detects and dismisses popups
    - Test navigation timeout after max_steps
    - Test error handling for invalid responses

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement Portal Adapter component
  - [ ] 8.1 Create Portal Adapter class
    - Create `agents/vision_scraper/portal_adapter.py`
    - Implement `PortalAdapter` class
    - Define PORTALS dictionary with 8 portals (Naukri, Indeed, LinkedIn, TimesJobs, Shine, Foundit, CutShort, Glassdoor)
    - Implement `get_portal_url(portal_name)` method
    - Implement `build_search_url(portal_name, query, location)` method
    - Implement `get_portal_config(portal_name)` method
    - Implement `list_supported_portals()` method
    - Add proper URL encoding for query parameters
    - Add error handling for invalid portal names
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 8.2 Write unit tests for Portal Adapter
    - Test get_portal_url for all 8 portals
    - Test build_search_url with various queries and locations
    - Test URL encoding of special characters
    - Test error handling for invalid portal names
    - Test list_supported_portals returns all 8 portals

- [ ] 9. Implement Hybrid Extractor component
  - [ ] 9.1 Create Hybrid Extractor class with JavaScript extraction
    - Create `agents/vision_scraper/hybrid_extractor.py`
    - Implement `HybridExtractor` class
    - Implement `extract_jobs(portal_name, max_jobs)` method
    - Implement `extract_with_javascript()` method
    - Reuse existing JavaScript extraction scripts from Browser Controller
    - Implement job data validation
    - Implement deduplication by source_url
    - Add extracted_at timestamp to all jobs
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7_

  - [ ] 9.2 Implement vision-based extraction fallback
    - Implement `extract_with_vision()` method
    - Use Vision Agent to analyze page and extract job data
    - Parse vision model responses into JobData objects
    - Validate extracted data
    - Fall back to vision only when JavaScript fails
    - _Requirements: 5.3, 11.3_

  - [ ] 9.3 Implement scroll and pagination handling
    - Implement `scroll_and_extract(max_jobs)` method
    - Scroll down to load more results
    - Wait 2 seconds after each scroll for content to load
    - Extract jobs incrementally
    - Track seen_urls to avoid duplicates
    - Stop after max_scroll_attempts (5) or when no new jobs found
    - _Requirements: 5.6, 5.7, 5.8, 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7_

  - [ ]* 9.4 Write property test for job deduplication
    - **Property 3: Job Deduplication**
    - **Validates: Requirements 5.4**
    - Generate extraction results with duplicate source_urls
    - Verify no duplicate source_urls in final results
    - Verify all jobs have unique source_urls

  - [ ]* 9.5 Write property test for extraction method determinism
    - **Property 8: Extraction Method Determinism**
    - **Validates: Requirements 5.1, 5.2, 5.3**
    - Test extraction with JavaScript succeeding
    - Verify vision extraction is NOT attempted
    - Test extraction with JavaScript failing
    - Verify vision extraction IS attempted

  - [ ]* 9.6 Write property test for max jobs limit
    - **Property 10: Max Jobs Limit**
    - **Validates: Requirements 5.8**
    - Generate extraction with various max_jobs values
    - Verify returned list length <= max_jobs
    - Test with scrolling and pagination

  - [ ]* 9.7 Write unit tests for Hybrid Extractor
    - Test extract_jobs with JavaScript extraction
    - Test extract_jobs with vision fallback
    - Test scroll_and_extract pagination
    - Test job validation and filtering
    - Test deduplication logic

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement Scraping Orchestrator component
  - [ ] 11.1 Create Scraping Orchestrator class
    - Create `agents/vision_scraper/scraping_orchestrator.py`
    - Implement `ScrapingOrchestrator` class
    - Initialize all components (Vision Agent, Hybrid Extractor, Rate Limiter, Portal Adapter)
    - Implement dependency injection for components
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

  - [ ] 11.2 Implement single portal scraping workflow
    - Implement `scrape_portal(portal_name, query, location, max_jobs)` method
    - Start browser via Browser Controller
    - Build search URL via Portal Adapter
    - Navigate to search results via Vision Agent
    - Extract jobs via Hybrid Extractor
    - Save jobs to database
    - Close browser and cleanup resources
    - Return ScrapingResult with metrics
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

  - [ ] 11.3 Implement multi-portal batch scraping
    - Implement `scrape_all_portals(query, location, max_jobs_per_portal)` method
    - Iterate through all 8 supported portals
    - Execute scraping sequentially to respect rate limits
    - Continue with remaining portals if one fails
    - Aggregate results across all portals
    - Return dictionary mapping portal names to ScrapingResults
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7_

  - [ ] 11.4 Implement error recovery and retry logic
    - Implement `handle_scraping_error(portal_name, error)` method
    - Retry vision API calls with exponential backoff (up to 2 retries)
    - Restart browser on crash and retry navigation once
    - Handle rate limit waits automatically
    - Handle navigation timeouts gracefully
    - Clean up resources on unrecoverable errors
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7_

  - [ ]* 11.5 Write property test for browser state consistency
    - **Property 6: Browser State Consistency**
    - **Validates: Requirements 4.7, 24.1, 24.2, 24.3, 24.4, 24.5**
    - Simulate various error scenarios during scraping
    - Verify browser is always closed after operation
    - Verify resources are cleaned up
    - Verify no zombie processes remain

  - [ ]* 11.6 Write unit tests for Scraping Orchestrator
    - Test scrape_portal completes successfully
    - Test scrape_all_portals iterates all portals
    - Test error recovery on browser crash
    - Test error recovery on navigation timeout
    - Test database persistence
    - Test resource cleanup on errors

- [ ] 12. Add logging and observability
  - [ ] 12.1 Implement comprehensive logging
    - Add logging to all components
    - Log scraping operation start (portal, query, location)
    - Log navigation steps (action type, coordinates, reasoning)
    - Log API calls (provider, model, response time)
    - Log rate limit hits (provider, wait time)
    - Log errors (type, message, stack trace)
    - Log scraping completion (jobs found, time elapsed, success status)
    - Log extraction method fallback events
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

  - [ ]* 12.2 Write unit tests for logging
    - Test log messages are generated for key events
    - Test log levels are appropriate (INFO, WARNING, ERROR)
    - Test error logs include stack traces

- [ ] 13. Add configuration management
  - [ ] 13.1 Create configuration module
    - Create `agents/vision_scraper/config.py`
    - Define configuration dataclass with all settings
    - Load rate limits from config (Mistral RPM, Gemini RPM)
    - Load browser settings (headless mode, viewport size)
    - Load navigation settings (max_steps, timeout)
    - Load extraction settings (max_jobs, scroll_attempts)
    - Validate configuration on startup
    - Fail fast with clear error messages if invalid
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_

  - [ ]* 13.2 Write unit tests for configuration
    - Test configuration loading from file
    - Test configuration validation
    - Test default values
    - Test error handling for invalid config

- [ ] 14. Integrate with existing FastAPI backend
  - [ ] 14.1 Create FastAPI endpoints for vision-guided scraping
    - Modify `api/main.py`
    - Add POST `/api/v2/scrape/portal` endpoint
    - Add POST `/api/v2/scrape/all-portals` endpoint
    - Add GET `/api/v2/scrape/status` endpoint for rate limit status
    - Implement request validation with Pydantic models
    - Implement response formatting
    - Add error handling and status codes
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

  - [ ] 14.2 Add database integration
    - Reuse existing database models from `database/models.py`
    - Implement job saving logic in Scraping Orchestrator
    - Handle duplicate jobs (update existing records)
    - Implement transaction management
    - Add error handling for database failures
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

  - [ ]* 14.3 Write integration tests for API endpoints
    - Test POST /api/v2/scrape/portal endpoint
    - Test POST /api/v2/scrape/all-portals endpoint
    - Test GET /api/v2/scrape/status endpoint
    - Test error responses
    - Test database persistence

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Performance optimization and testing
  - [ ] 16.1 Optimize performance for timing requirements
    - Ensure navigation completes within 60 seconds
    - Ensure JavaScript extraction completes within 10 seconds for 50 jobs
    - Ensure vision extraction completes within 120 seconds for 50 jobs
    - Ensure single portal scraping completes within 3 minutes
    - Ensure all 8 portals scraping completes within 25 minutes
    - Add performance monitoring and metrics
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_

  - [ ]* 16.2 Write performance tests
    - Test navigation timing with various portals
    - Test extraction timing with JavaScript
    - Test extraction timing with vision
    - Test single portal scraping timing
    - Test multi-portal scraping timing

- [ ] 17. Create module initialization and exports
  - [ ] 17.1 Create package structure
    - Create `agents/vision_scraper/__init__.py`
    - Export main classes (VisionAgent, ScrapingOrchestrator, etc.)
    - Create `agents/vision_scraper/README.md` with usage examples
    - Document configuration options
    - Document API endpoints

- [ ] 18. End-to-end integration testing
  - [ ]* 18.1 Write end-to-end integration tests
    - Test complete scraping workflow for one portal
    - Test complete scraping workflow for all portals
    - Test error recovery scenarios
    - Test rate limit handling across providers
    - Test popup handling
    - Test database persistence
    - Test API endpoint integration

- [ ] 19. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all 25 functional requirements are covered
  - Verify all 10 correctness properties are tested
  - Verify integration with existing Phase 1 components
  - Verify API endpoints are functional
  - Verify database persistence works correctly

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests validate universal correctness properties from the design
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- The implementation uses Python with async/await, Pydantic models, and type hints
- The system integrates with existing Phase 1 components (Browser Controller, Database, FastAPI)
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- All components follow single-responsibility principle for maintainability
- Configuration is externalized for easy tuning and extensibility
- Comprehensive logging enables debugging and monitoring
- Error recovery ensures reliability and resilience

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "5.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "6.1"] },
    { "id": 5, "tasks": ["6.2", "6.3", "6.4"] },
    { "id": 6, "tasks": ["6.5", "6.6", "8.1"] },
    { "id": 7, "tasks": ["8.2", "9.1"] },
    { "id": 8, "tasks": ["9.2", "9.3"] },
    { "id": 9, "tasks": ["9.4", "9.5", "9.6", "9.7"] },
    { "id": 10, "tasks": ["11.1"] },
    { "id": 11, "tasks": ["11.2", "11.3", "11.4"] },
    { "id": 12, "tasks": ["11.5", "11.6", "12.1"] },
    { "id": 13, "tasks": ["12.2", "13.1"] },
    { "id": 14, "tasks": ["13.2", "14.1", "14.2"] },
    { "id": 15, "tasks": ["14.3", "16.1"] },
    { "id": 16, "tasks": ["16.2", "17.1"] },
    { "id": 17, "tasks": ["18.1"] }
  ]
}
```
