# Requirements Document

## Introduction

This document specifies the requirements for a vision-guided adaptive web scraping system that uses AI vision models (Mistral Pixtral 12B and Gemini 2.5 Flash) to navigate job portals and extract job listings. The system eliminates brittle CSS selector dependencies by using screenshot analysis for navigation and combines vision-guided navigation with JavaScript-based extraction for optimal performance. The system supports 8 major job portals (Naukri, Indeed, LinkedIn, TimesJobs, Shine, Foundit, CutShort, Glassdoor) with zero portal-specific navigation logic.

## Glossary

- **Vision_Agent**: Component that analyzes screenshots using AI vision models and decides navigation actions
- **Browser_Controller**: Component that manages CloakBrowser lifecycle and executes actions via PyAutoGUI
- **Hybrid_Extractor**: Component that extracts job data using JavaScript (primary) and vision (fallback)
- **Rate_Limiter**: Component that enforces API rate limits across multiple AI providers
- **Portal_Adapter**: Component that provides universal interface for all supported job portals
- **Scraping_Orchestrator**: Component that coordinates the complete scraping workflow
- **Multi_Provider_AI_Client**: Client that manages requests to Mistral and Gemini vision APIs
- **ActionDecision**: Structured data representing a navigation action (click, type, scroll, etc.)
- **NavigationResult**: Structured data representing the outcome of a navigation workflow
- **JobData**: Structured data representing an extracted job listing
- **ScrapingResult**: Structured data representing the complete outcome of a portal scraping operation
- **CloakBrowser**: Stealth browser implementation that avoids bot detection
- **PyAutoGUI**: Library for executing coordinate-based UI automation
- **RPM**: Requests Per Minute - rate limit measurement
- **Mistral_Pixtral**: Mistral's vision model (2 RPM free tier limit)
- **Gemini_Flash**: Google's Gemini 2.5 Flash vision model (15 RPM free tier limit)

## Requirements

### Requirement 1: Vision-Guided Navigation

**User Story:** As a scraping system, I want to navigate job portals using vision analysis, so that I can adapt to UI changes without manual selector updates.

#### Acceptance Criteria

1. WHEN the Vision_Agent receives a portal URL, search query, and location, THE Vision_Agent SHALL navigate to the search results page using vision-guided actions
2. WHEN the Vision_Agent analyzes a screenshot, THE Vision_Agent SHALL return a valid ActionDecision within 10 seconds
3. WHEN the Vision_Agent executes navigation, THE Vision_Agent SHALL complete within 10 steps or terminate with a clear status (SUCCESS, FAILED, TIMEOUT)
4. WHEN a navigation step is executed, THE Vision_Agent SHALL capture a screenshot before and after the action
5. WHEN the search results page is reached, THE Vision_Agent SHALL return NavigationResult with status SUCCESS
6. WHEN navigation cannot proceed, THE Vision_Agent SHALL return NavigationResult with status FAILED and descriptive error message
7. WHEN max_steps is reached without achieving the goal, THE Vision_Agent SHALL return NavigationResult with status TIMEOUT

### Requirement 2: Multi-Provider AI Integration

**User Story:** As a scraping system, I want to use multiple AI vision providers with automatic fallback, so that I can maximize throughput within free tier limits.

#### Acceptance Criteria

1. WHEN the Vision_Agent needs to analyze a screenshot, THE Multi_Provider_AI_Client SHALL check Mistral availability first
2. WHEN Mistral is available, THE Multi_Provider_AI_Client SHALL use Mistral Pixtral 12B for vision analysis
3. WHEN Mistral is rate limited, THE Multi_Provider_AI_Client SHALL automatically fall back to Gemini 2.5 Flash
4. WHEN both providers are rate limited, THE Multi_Provider_AI_Client SHALL wait until the next provider becomes available
5. WHEN a vision API call is made, THE Multi_Provider_AI_Client SHALL include the screenshot as base64 encoded image
6. WHEN a vision API call completes, THE Multi_Provider_AI_Client SHALL parse the response into a structured ActionDecision
7. WHEN a vision API call fails, THE Multi_Provider_AI_Client SHALL retry up to 2 times before returning an error

### Requirement 3: Rate Limit Enforcement

**User Story:** As a scraping system, I want to enforce API rate limits across providers, so that I stay within free tier quotas and avoid service disruption.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce a maximum of 2 requests per minute for Mistral Pixtral
2. THE Rate_Limiter SHALL enforce a maximum of 15 requests per minute for Gemini 2.5 Flash
3. WHEN a request is made, THE Rate_Limiter SHALL record the timestamp for the provider
4. WHEN checking availability, THE Rate_Limiter SHALL only count requests within the last 60 seconds
5. WHEN 60 seconds have elapsed since last reset, THE Rate_Limiter SHALL reset the request counter for that provider
6. WHEN a provider is at capacity, THE Rate_Limiter SHALL return false for check_availability
7. WHEN both providers are at capacity, THE Rate_Limiter SHALL calculate and return the wait time until next availability

### Requirement 4: Browser Control and Automation

**User Story:** As a scraping system, I want to control a stealth browser and execute coordinate-based actions, so that I can interact with job portals without being detected as a bot.

#### Acceptance Criteria

1. WHEN the Browser_Controller starts, THE Browser_Controller SHALL launch CloakBrowser with stealth settings enabled
2. WHEN the Browser_Controller takes a screenshot, THE Browser_Controller SHALL return a base64 encoded image string
3. WHEN the Browser_Controller receives click coordinates, THE Browser_Controller SHALL execute the click using PyAutoGUI
4. WHEN the Browser_Controller receives type action, THE Browser_Controller SHALL click the coordinates then type the text
5. WHEN the Browser_Controller receives scroll action, THE Browser_Controller SHALL scroll the page in the specified direction and amount
6. WHEN the Browser_Controller executes JavaScript, THE Browser_Controller SHALL return the script result or error
7. WHEN the Browser_Controller closes, THE Browser_Controller SHALL terminate the browser process and clean up resources
8. WHEN the browser crashes, THE Browser_Controller SHALL detect the crash and return an error status

### Requirement 5: Hybrid Job Extraction

**User Story:** As a scraping system, I want to extract job data using JavaScript with vision fallback, so that I can achieve fast extraction while maintaining adaptability.

#### Acceptance Criteria

1. WHEN the Hybrid_Extractor extracts jobs, THE Hybrid_Extractor SHALL attempt JavaScript extraction first
2. WHEN JavaScript extraction succeeds, THE Hybrid_Extractor SHALL return the extracted jobs without attempting vision extraction
3. WHEN JavaScript extraction fails or returns empty results, THE Hybrid_Extractor SHALL fall back to vision-based extraction
4. WHEN extracting jobs, THE Hybrid_Extractor SHALL deduplicate by source_url
5. WHEN extracting jobs, THE Hybrid_Extractor SHALL validate that each job has required fields (title, company, source_url, apply_url)
6. WHEN the extracted job count is less than max_jobs, THE Hybrid_Extractor SHALL scroll down and extract more jobs
7. WHEN scrolling yields no new jobs after 5 attempts, THE Hybrid_Extractor SHALL stop scrolling and return accumulated jobs
8. WHEN extraction completes, THE Hybrid_Extractor SHALL return a list with length <= max_jobs

### Requirement 6: Job Data Validation

**User Story:** As a scraping system, I want to validate extracted job data, so that I only store complete and accurate job listings.

#### Acceptance Criteria

1. WHEN a job is extracted, THE Hybrid_Extractor SHALL verify that title is non-empty
2. WHEN a job is extracted, THE Hybrid_Extractor SHALL verify that company is non-empty
3. WHEN a job is extracted, THE Hybrid_Extractor SHALL verify that source_url is a valid URL
4. WHEN a job is extracted, THE Hybrid_Extractor SHALL verify that apply_url is a valid URL
5. WHEN a job is extracted, THE Hybrid_Extractor SHALL verify that source matches the portal_name
6. WHEN a job is extracted, THE Hybrid_Extractor SHALL add an extracted_at timestamp in ISO 8601 format
7. WHEN a job fails validation, THE Hybrid_Extractor SHALL exclude it from the results and log the validation failure

### Requirement 7: Portal Adapter Interface

**User Story:** As a scraping system, I want a universal interface for all job portals, so that I can add new portals without changing core scraping logic.

#### Acceptance Criteria

1. THE Portal_Adapter SHALL support 8 job portals: Naukri, Indeed, LinkedIn, TimesJobs, Shine, Foundit, CutShort, Glassdoor
2. WHEN given a portal name, THE Portal_Adapter SHALL return the base URL for that portal
3. WHEN building a search URL, THE Portal_Adapter SHALL properly encode the query and location parameters
4. WHEN given an invalid portal name, THE Portal_Adapter SHALL raise a descriptive error
5. WHEN listing supported portals, THE Portal_Adapter SHALL return all 8 portal names
6. THE Portal_Adapter SHALL contain no portal-specific scraping or navigation logic

### Requirement 8: Popup and Overlay Handling

**User Story:** As a scraping system, I want to automatically detect and dismiss popups, so that navigation can proceed without manual intervention.

#### Acceptance Criteria

1. WHEN the Vision_Agent detects a popup in a screenshot, THE Vision_Agent SHALL attempt to dismiss it
2. WHEN dismissing a popup, THE Vision_Agent SHALL try clicking dismiss buttons, close icons, or clicking outside the popup
3. WHEN a popup is successfully dismissed, THE Vision_Agent SHALL return true and continue navigation
4. WHEN no popup is detected, THE Vision_Agent SHALL return false and proceed with normal navigation
5. WHEN a popup cannot be dismissed after 3 attempts, THE Vision_Agent SHALL return NavigationResult with status FAILED
6. WHEN checking for popups, THE Vision_Agent SHALL analyze the screenshot for overlay elements, cookie banners, and sign-in prompts

### Requirement 9: Action Decision Validation

**User Story:** As a scraping system, I want to validate action decisions from vision models, so that I only execute safe and valid actions.

#### Acceptance Criteria

1. WHEN the Vision_Agent receives an ActionDecision, THE Vision_Agent SHALL verify that action_type is a valid enum value
2. WHEN action_type is CLICK or TYPE, THE Vision_Agent SHALL verify that coordinates are within screenshot bounds
3. WHEN action_type is TYPE, THE Vision_Agent SHALL verify that text is non-empty
4. WHEN action_type is SCROLL, THE Vision_Agent SHALL verify that direction is "up" or "down"
5. WHEN action_type is SCROLL, THE Vision_Agent SHALL verify that amount is a positive integer
6. WHEN coordinates are invalid, THE Vision_Agent SHALL clamp them to valid viewport bounds
7. WHEN an ActionDecision is invalid, THE Vision_Agent SHALL log the validation error and request a new decision

### Requirement 10: Scraping Orchestration

**User Story:** As a scraping system, I want to orchestrate the complete scraping workflow, so that all components work together to produce reliable results.

#### Acceptance Criteria

1. WHEN the Scraping_Orchestrator receives a scrape request, THE Scraping_Orchestrator SHALL start the browser
2. WHEN the browser is started, THE Scraping_Orchestrator SHALL invoke the Vision_Agent to navigate to search results
3. WHEN navigation succeeds, THE Scraping_Orchestrator SHALL invoke the Hybrid_Extractor to extract jobs
4. WHEN jobs are extracted, THE Scraping_Orchestrator SHALL save them to the database
5. WHEN scraping completes or fails, THE Scraping_Orchestrator SHALL close the browser
6. WHEN scraping completes, THE Scraping_Orchestrator SHALL return a ScrapingResult with success status and metrics
7. WHEN scraping fails, THE Scraping_Orchestrator SHALL return a ScrapingResult with failure status and error message
8. WHEN scraping all portals, THE Scraping_Orchestrator SHALL execute each portal sequentially to respect rate limits

### Requirement 11: Error Recovery and Retry Logic

**User Story:** As a scraping system, I want to recover from transient errors, so that temporary issues don't cause complete scraping failures.

#### Acceptance Criteria

1. WHEN a vision API call fails, THE Vision_Agent SHALL retry up to 2 times with exponential backoff
2. WHEN the browser crashes, THE Scraping_Orchestrator SHALL restart the browser and retry navigation once
3. WHEN JavaScript extraction fails, THE Hybrid_Extractor SHALL fall back to vision extraction without failing the request
4. WHEN a popup cannot be dismissed, THE Vision_Agent SHALL retry with alternative dismiss strategies
5. WHEN rate limits are exceeded, THE Rate_Limiter SHALL wait for capacity and retry automatically
6. WHEN navigation times out, THE Scraping_Orchestrator SHALL log the timeout and return a TIMEOUT status
7. WHEN an unrecoverable error occurs, THE Scraping_Orchestrator SHALL clean up resources and return a descriptive error

### Requirement 12: Screenshot Capture and Management

**User Story:** As a scraping system, I want to capture and manage screenshots throughout navigation, so that I can analyze page state and debug issues.

#### Acceptance Criteria

1. WHEN a navigation step begins, THE Vision_Agent SHALL capture a screenshot of the current page state
2. WHEN a screenshot is captured, THE Browser_Controller SHALL return it as a base64 encoded PNG or JPEG
3. WHEN the browser is in a valid state, THE Browser_Controller SHALL successfully capture a screenshot within 5 seconds
4. WHEN the browser has crashed, THE Browser_Controller SHALL return an error instead of attempting screenshot capture
5. WHEN navigation completes, THE Vision_Agent SHALL include all captured screenshots in the NavigationResult
6. WHEN a full page screenshot is requested, THE Browser_Controller SHALL scroll and stitch multiple screenshots if needed

### Requirement 13: Coordinate-Based Action Execution

**User Story:** As a scraping system, I want to execute actions at specific screen coordinates, so that I can interact with UI elements without relying on selectors.

#### Acceptance Criteria

1. WHEN the Browser_Controller receives click coordinates, THE Browser_Controller SHALL move the mouse to those coordinates using PyAutoGUI
2. WHEN the mouse is positioned, THE Browser_Controller SHALL execute a click action
3. WHEN the Browser_Controller receives type action, THE Browser_Controller SHALL click the coordinates first to focus the element
4. WHEN the element is focused, THE Browser_Controller SHALL type the text character by character with realistic delays
5. WHEN typing completes, THE Browser_Controller SHALL wait 500ms for the page to process the input
6. WHEN an action fails, THE Browser_Controller SHALL return an ActionResult with failure status and error details
7. WHEN an action succeeds, THE Browser_Controller SHALL return an ActionResult with success status

### Requirement 14: Vision Prompt Engineering

**User Story:** As a scraping system, I want to provide clear and structured prompts to vision models, so that I get consistent and actionable responses.

#### Acceptance Criteria

1. WHEN analyzing a screenshot, THE Vision_Agent SHALL include the current goal in the prompt
2. WHEN analyzing a screenshot, THE Vision_Agent SHALL list all available action types in the prompt
3. WHEN analyzing a screenshot, THE Vision_Agent SHALL request JSON formatted responses
4. WHEN analyzing a screenshot, THE Vision_Agent SHALL include context about previous actions if available
5. WHEN analyzing a screenshot, THE Vision_Agent SHALL specify the expected JSON schema in the prompt
6. WHEN the vision model returns invalid JSON, THE Vision_Agent SHALL retry with a simplified prompt
7. WHEN retries fail, THE Vision_Agent SHALL return an ActionDecision with action_type ERROR

### Requirement 15: Database Persistence

**User Story:** As a scraping system, I want to persist extracted jobs to a database, so that job data is available for downstream processing.

#### Acceptance Criteria

1. WHEN jobs are extracted, THE Scraping_Orchestrator SHALL save each job to the SQLite database
2. WHEN saving a job, THE Scraping_Orchestrator SHALL store all JobData fields
3. WHEN a job with the same source_url already exists, THE Scraping_Orchestrator SHALL update the existing record
4. WHEN database save fails, THE Scraping_Orchestrator SHALL log the error but continue processing remaining jobs
5. WHEN all jobs are saved, THE Scraping_Orchestrator SHALL commit the database transaction
6. WHEN scraping fails before extraction, THE Scraping_Orchestrator SHALL not save any partial data

### Requirement 16: Performance and Timing

**User Story:** As a scraping system, I want to complete scraping operations efficiently, so that users get results in reasonable time.

#### Acceptance Criteria

1. WHEN navigating to search results, THE Vision_Agent SHALL complete within 60 seconds or timeout
2. WHEN extracting jobs with JavaScript, THE Hybrid_Extractor SHALL complete within 10 seconds for 50 jobs
3. WHEN extracting jobs with vision, THE Hybrid_Extractor SHALL complete within 120 seconds for 50 jobs
4. WHEN analyzing a screenshot, THE Vision_Agent SHALL receive a response from the AI provider within 10 seconds
5. WHEN scraping a single portal, THE Scraping_Orchestrator SHALL complete within 3 minutes
6. WHEN scraping all 8 portals, THE Scraping_Orchestrator SHALL complete within 25 minutes
7. WHEN waiting for rate limit capacity, THE Rate_Limiter SHALL calculate and report accurate wait times

### Requirement 17: Logging and Observability

**User Story:** As a system operator, I want comprehensive logging of scraping operations, so that I can monitor performance and debug issues.

#### Acceptance Criteria

1. WHEN a scraping operation starts, THE Scraping_Orchestrator SHALL log the portal name, query, and location
2. WHEN a navigation step is executed, THE Vision_Agent SHALL log the action type, coordinates, and reasoning
3. WHEN an API call is made, THE Multi_Provider_AI_Client SHALL log the provider, model, and response time
4. WHEN rate limits are hit, THE Rate_Limiter SHALL log the provider and wait time
5. WHEN an error occurs, THE component SHALL log the error type, message, and stack trace
6. WHEN scraping completes, THE Scraping_Orchestrator SHALL log the total jobs extracted, time elapsed, and success status
7. WHEN extraction method falls back from JavaScript to vision, THE Hybrid_Extractor SHALL log the fallback event

### Requirement 18: Configuration and Extensibility

**User Story:** As a developer, I want to configure system behavior and add new portals easily, so that the system can adapt to changing requirements.

#### Acceptance Criteria

1. THE system SHALL load rate limits from configuration (Mistral RPM, Gemini RPM)
2. THE system SHALL load browser settings from configuration (headless mode, viewport size)
3. THE system SHALL load navigation settings from configuration (max_steps, timeout)
4. THE system SHALL load extraction settings from configuration (max_jobs, scroll_attempts)
5. WHEN adding a new portal, THE developer SHALL only need to add an entry to Portal_Adapter.PORTALS
6. WHEN changing AI providers, THE developer SHALL only need to update Multi_Provider_AI_Client configuration
7. THE system SHALL validate configuration on startup and fail fast with clear error messages if invalid

### Requirement 19: Action Result Tracking

**User Story:** As a scraping system, I want to track the results of executed actions, so that I can verify success and handle failures appropriately.

#### Acceptance Criteria

1. WHEN an action is executed, THE Browser_Controller SHALL return an ActionResult object
2. WHEN an action succeeds, THE ActionResult SHALL have success status and execution time
3. WHEN an action fails, THE ActionResult SHALL have failure status and error message
4. WHEN a click action is executed, THE ActionResult SHALL indicate whether the click was registered
5. WHEN a type action is executed, THE ActionResult SHALL indicate whether the text was entered
6. WHEN a scroll action is executed, THE ActionResult SHALL indicate the final scroll position
7. WHEN navigation completes, THE NavigationResult SHALL include all ActionResults for executed actions

### Requirement 20: Vision Model Response Parsing

**User Story:** As a scraping system, I want to reliably parse vision model responses, so that I can convert natural language decisions into structured actions.

#### Acceptance Criteria

1. WHEN the vision model returns a response, THE Vision_Agent SHALL attempt to parse it as JSON
2. WHEN JSON parsing succeeds, THE Vision_Agent SHALL extract action_type, coordinates, text, direction, amount, reasoning, and confidence
3. WHEN JSON parsing fails, THE Vision_Agent SHALL log the raw response and retry with a clearer prompt
4. WHEN required fields are missing, THE Vision_Agent SHALL return an ActionDecision with action_type ERROR
5. WHEN confidence is below 0.5, THE Vision_Agent SHALL log a warning but still execute the action
6. WHEN the response contains invalid action_type, THE Vision_Agent SHALL return an ActionDecision with action_type ERROR
7. WHEN parsing succeeds, THE Vision_Agent SHALL validate the ActionDecision before returning it

### Requirement 21: Scroll and Pagination Handling

**User Story:** As a scraping system, I want to handle paginated results by scrolling, so that I can extract more jobs than fit on the initial screen.

#### Acceptance Criteria

1. WHEN the initial extraction yields fewer jobs than max_jobs, THE Hybrid_Extractor SHALL scroll down to load more results
2. WHEN scrolling, THE Hybrid_Extractor SHALL wait 2 seconds for new content to load
3. WHEN new content loads, THE Hybrid_Extractor SHALL extract jobs from the updated page
4. WHEN no new jobs are found after scrolling, THE Hybrid_Extractor SHALL stop scrolling
5. WHEN max_scroll_attempts (5) is reached, THE Hybrid_Extractor SHALL stop scrolling and return accumulated jobs
6. WHEN scrolling, THE Hybrid_Extractor SHALL track seen_urls to avoid extracting duplicates
7. WHEN the page cannot scroll further, THE Hybrid_Extractor SHALL detect the end of results and stop

### Requirement 22: JavaScript Extraction Scripts

**User Story:** As a scraping system, I want to execute JavaScript extraction scripts in the browser, so that I can quickly extract structured data from the DOM.

#### Acceptance Criteria

1. WHEN extracting jobs, THE Hybrid_Extractor SHALL execute a JavaScript script in the page context
2. WHEN the script executes, THE Browser_Controller SHALL return the script result as a Python object
3. WHEN the script finds job elements, THE script SHALL extract title, company, location, source_url, and apply_url
4. WHEN the script encounters missing fields, THE script SHALL use empty string or null as appropriate
5. WHEN the script completes, THE script SHALL return an array of job objects
6. WHEN the script throws an error, THE Browser_Controller SHALL catch it and return an empty array
7. WHEN JavaScript is disabled or blocked, THE Hybrid_Extractor SHALL fall back to vision extraction

### Requirement 23: Goal Achievement Detection

**User Story:** As a scraping system, I want to detect when navigation goals are achieved, so that I can stop navigating and begin extraction.

#### Acceptance Criteria

1. WHEN analyzing a screenshot, THE Vision_Agent SHALL determine if the current goal is achieved
2. WHEN search results are visible on the page, THE Vision_Agent SHALL return ActionDecision with action_type GOAL_ACHIEVED
3. WHEN the goal is achieved, THE Vision_Agent SHALL stop the navigation loop
4. WHEN the goal is not achieved, THE Vision_Agent SHALL return an action to progress toward the goal
5. WHEN the goal cannot be achieved, THE Vision_Agent SHALL return ActionDecision with action_type ERROR
6. WHEN GOAL_ACHIEVED is returned, THE NavigationResult SHALL have status SUCCESS
7. WHEN the goal is ambiguous, THE Vision_Agent SHALL use confidence scores to decide whether to continue

### Requirement 24: Resource Cleanup

**User Story:** As a scraping system, I want to properly clean up resources after scraping, so that I don't leak memory or leave processes running.

#### Acceptance Criteria

1. WHEN scraping completes successfully, THE Scraping_Orchestrator SHALL close the browser
2. WHEN scraping fails, THE Scraping_Orchestrator SHALL close the browser before returning
3. WHEN the browser is closed, THE Browser_Controller SHALL terminate the browser process
4. WHEN the browser process is terminated, THE Browser_Controller SHALL release all file handles and network connections
5. WHEN multiple scraping operations run sequentially, THE system SHALL not accumulate zombie processes
6. WHEN the system shuts down, THE system SHALL close all open browsers and database connections
7. WHEN an exception occurs, THE system SHALL ensure cleanup happens in a finally block

### Requirement 25: Multi-Portal Batch Scraping

**User Story:** As a user, I want to scrape all supported portals in one operation, so that I can gather comprehensive job listings efficiently.

#### Acceptance Criteria

1. WHEN scraping all portals, THE Scraping_Orchestrator SHALL iterate through all 8 supported portals
2. WHEN scraping each portal, THE Scraping_Orchestrator SHALL respect rate limits between portals
3. WHEN a portal scraping fails, THE Scraping_Orchestrator SHALL continue with remaining portals
4. WHEN all portals are scraped, THE Scraping_Orchestrator SHALL return a dictionary mapping portal names to ScrapingResults
5. WHEN scraping all portals, THE Scraping_Orchestrator SHALL aggregate total jobs found across all portals
6. WHEN scraping all portals, THE Scraping_Orchestrator SHALL report individual success/failure status for each portal
7. WHEN rate limits are hit during batch scraping, THE Scraping_Orchestrator SHALL wait and continue rather than failing

## Non-Functional Requirements

### NFR 1: Reliability

**User Story:** As a user, I want the scraping system to be reliable, so that I can depend on it for regular job searches.

#### Acceptance Criteria

1. THE system SHALL successfully complete scraping operations 95% of the time under normal conditions
2. WHEN transient errors occur, THE system SHALL retry and recover without manual intervention
3. WHEN a portal changes its UI, THE system SHALL adapt using vision guidance without code changes
4. WHEN the browser crashes, THE system SHALL restart and retry without losing progress
5. THE system SHALL handle network interruptions gracefully with appropriate timeouts and retries

### NFR 2: Performance

**User Story:** As a user, I want scraping operations to complete quickly, so that I can get job results without long waits.

#### Acceptance Criteria

1. THE system SHALL complete single portal scraping in under 3 minutes for 50 jobs
2. THE system SHALL complete all 8 portals scraping in under 25 minutes for 50 jobs per portal
3. THE system SHALL use JavaScript extraction (fast) whenever possible before falling back to vision (slow)
4. THE system SHALL minimize unnecessary screenshots and API calls
5. THE system SHALL execute actions with minimal delays while maintaining realistic human-like timing

### NFR 3: Scalability

**User Story:** As a system operator, I want the system to scale within free tier limits, so that I can maximize throughput without incurring costs.

#### Acceptance Criteria

1. THE system SHALL support up to 17 vision API calls per minute (2 Mistral + 15 Gemini)
2. THE system SHALL automatically distribute load across providers to maximize throughput
3. THE system SHALL handle multiple sequential scraping operations without degradation
4. THE system SHALL support adding new portals without performance impact on existing portals
5. THE system SHALL efficiently manage memory and not leak resources during long-running operations

### NFR 4: Maintainability

**User Story:** As a developer, I want the system to be maintainable, so that I can fix bugs and add features easily.

#### Acceptance Criteria

1. THE system SHALL have clear separation of concerns with single-responsibility components
2. THE system SHALL use well-defined interfaces between components
3. THE system SHALL have comprehensive logging for debugging and monitoring
4. THE system SHALL use type hints and validation for all data models
5. THE system SHALL have no portal-specific logic in core components (only in Portal_Adapter)

### NFR 5: Extensibility

**User Story:** As a developer, I want to extend the system easily, so that I can add new portals and features without major refactoring.

#### Acceptance Criteria

1. THE system SHALL support adding new job portals by only updating Portal_Adapter configuration
2. THE system SHALL support adding new AI providers by only updating Multi_Provider_AI_Client
3. THE system SHALL support adding new extraction methods without changing the Hybrid_Extractor interface
4. THE system SHALL use dependency injection for component initialization
5. THE system SHALL use configuration files for all tunable parameters

### NFR 6: Security

**User Story:** As a system operator, I want the system to be secure, so that API keys and user data are protected.

#### Acceptance Criteria

1. THE system SHALL load API keys from environment variables, not hardcoded values
2. THE system SHALL not log API keys or sensitive credentials
3. THE system SHALL use HTTPS for all external API calls
4. THE system SHALL validate and sanitize all user inputs (queries, locations)
5. THE system SHALL use CloakBrowser stealth features to avoid bot detection and IP bans

### NFR 7: Observability

**User Story:** As a system operator, I want to observe system behavior, so that I can monitor health and diagnose issues.

#### Acceptance Criteria

1. THE system SHALL log all scraping operations with timestamps and outcomes
2. THE system SHALL track and report rate limit usage for each provider
3. THE system SHALL measure and report timing for each operation phase (navigation, extraction, saving)
4. THE system SHALL capture and store screenshots for failed navigation attempts
5. THE system SHALL provide status endpoints for monitoring system health

### NFR 8: Adaptability

**User Story:** As a user, I want the system to adapt to portal changes, so that scraping continues working without manual updates.

#### Acceptance Criteria

1. THE system SHALL use vision-guided navigation that adapts to UI changes automatically
2. THE system SHALL fall back from JavaScript to vision extraction when DOM structure changes
3. THE system SHALL handle new popup types without code changes
4. THE system SHALL detect and adapt to different page layouts across portals
5. THE system SHALL learn from successful navigation patterns to improve future performance

### NFR 9: Cost Efficiency

**User Story:** As a system operator, I want to minimize API costs, so that the system remains economical to operate.

#### Acceptance Criteria

1. THE system SHALL operate entirely within free tier limits (Mistral 2 RPM, Gemini 15 RPM)
2. THE system SHALL prefer JavaScript extraction (free) over vision extraction (API cost)
3. THE system SHALL minimize redundant API calls by caching and reusing results
4. THE system SHALL use the most cost-effective provider (Gemini) when both are available
5. THE system SHALL provide visibility into API usage to prevent unexpected costs

### NFR 10: Usability

**User Story:** As a user, I want the system to be easy to use, so that I can start scraping with minimal configuration.

#### Acceptance Criteria

1. THE system SHALL provide a simple API endpoint for scraping: POST /scrape with portal, query, location
2. THE system SHALL return structured JSON results with clear success/failure indicators
3. THE system SHALL provide helpful error messages when scraping fails
4. THE system SHALL support both single portal and all portals scraping modes
5. THE system SHALL include example usage code and documentation
