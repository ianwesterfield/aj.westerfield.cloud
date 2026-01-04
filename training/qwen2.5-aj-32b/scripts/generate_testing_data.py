#!/usr/bin/env python3
"""
Generate testing and debugging training data for AJ fine-tuning.
Covers unit testing, integration testing, debugging techniques, and quality assurance.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"

SYSTEM_PROMPT = "You are AJ, an AI coding assistant. You are helping with testing and debugging strategies."

# =============================================================================
# UNIT TESTING CONCEPTS
# =============================================================================

UNIT_TESTING = [
    {
        "question": "What makes a good unit test?",
        "answer": "FIRST principles: Fast (milliseconds), Independent (no shared state), Repeatable (same result always), Self-validating (pass/fail, no manual check), Timely (written with code). Structure: Arrange-Act-Assert (AAA). One assertion per test when possible. Test names describe scenario: 'should_return_error_when_input_is_null'. Test behavior, not implementation. No logic in tests (no if/loops). Mock external dependencies. 100% deterministic - no flaky tests."
    },
    {
        "question": "How do I decide what to unit test?",
        "answer": "Focus on: business logic, edge cases, complex algorithms, public API. Skip: trivial getters/setters, framework code, pure delegation. Priority: code with high complexity, frequently changing code, code with past bugs. Test pyramid: many unit tests (fast, isolated), fewer integration tests, few E2E tests. Coverage goal: 70-80% is good, 100% often not practical. Test critical paths thoroughly, less critical paths adequately. New bugs = new tests to prevent regression."
    },
    {
        "question": "What is test-driven development (TDD) and when should I use it?",
        "answer": "TDD cycle: Red (write failing test), Green (minimal code to pass), Refactor (improve code, tests still pass). Benefits: forces design thinking, ensures testability, documents behavior, catches regressions. When to use: new features with clear requirements, complex algorithms, bug fixes (test first). When not to use: exploration/prototyping, UI development, learning new APIs. Start small: one test at a time. Don't skip refactor step. Tests are first-class code."
    },
    {
        "question": "How do I test async code properly?",
        "answer": "Python: async def test with pytest-asyncio, await assertions. JavaScript/Jest: return promise or use async/await, done callback for callbacks. Patterns: mock timers (jest.useFakeTimers), control clock (freezegun). Avoid: real sleeps in tests (flaky, slow). Test: successful completion, timeout handling, error propagation, cancellation. For callbacks: use done() or promisify. For streams: collect events, assert on completion. Always set reasonable timeouts. Mock network calls don't need async testing."
    },
    {
        "question": "What is the difference between mocks, stubs, and spies?",
        "answer": "Stub: provides canned responses, no verification. Use for: external services returning data. Mock: verifies interactions (was method called? with what args?). Use for: verifying side effects, outgoing commands. Spy: wraps real object, records calls, can override behavior. Use for: verifying calls while using real implementation. Fake: simplified working implementation (in-memory database). Use for: faster tests with realistic behavior. Rule: stub queries, mock commands. Over-mocking = brittle tests."
    },
    {
        "question": "How do I write tests for error handling?",
        "answer": "Test: exception thrown for invalid input, correct exception type, error message content, error codes/status. Patterns: expect().toThrow(), pytest.raises(), assertThrows(). Test error recovery paths. Test partial failures in batch operations. Don't just catch exceptions - verify specific type. Test error boundaries (React), error middleware (Express). Integration: test error propagation across layers. Document error cases with tests. Each error path should have a test."
    },
    {
        "question": "How do I test private methods?",
        "answer": "Don't test private methods directly. Private methods are implementation details. Test through public API that uses them. If private method needs testing, it might deserve its own class. Options: make method public if truly reusable, extract to utility function, test via public method. In Python: use _method convention, test via public methods. If you must: Python name mangling access, reflection in Java/C#. Better approach: redesign for testability. Private method complexity = design smell."
    },
    {
        "question": "What is property-based testing?",
        "answer": "Generate random inputs, assert properties hold for all inputs. Example: reverse(reverse(list)) == list, sort(list) is always sorted. Tools: Hypothesis (Python), fast-check (JS), QuickCheck (Haskell origin). Benefits: finds edge cases humans miss, tests invariants broadly. Use for: parsers, serialization, mathematical functions, data transformations. Define: generators for input domain, properties that must hold. Shrinking: when failure found, minimize to simplest failing case. Complement, don't replace example-based tests."
    },
    {
        "question": "How do I test code that depends on time?",
        "answer": "Never use real time in tests (slow, flaky). Inject time dependency: pass clock/timer, use time provider interface. Python: freezegun (freeze_time decorator), unittest.mock for datetime. JavaScript: jest.useFakeTimers(), sinon.useFakeTimers(). Test: time boundaries, expiration logic, scheduling, time zones. Advance time programmatically: clock.tick(). Set specific moments: test midnight, DST transitions, leap years. Assert: timeouts fire, schedules execute, time-based calculations correct."
    },
    {
        "question": "How do I organize test files and test suites?",
        "answer": "Mirror source structure: src/foo.py → tests/test_foo.py. Group by feature or component. Naming: test_<what>_<scenario>_<expected>. Fixtures: shared setup in conftest.py (pytest), beforeEach (Jest). Test categories: unit, integration, e2e with markers/directories. Run: unit tests always, integration on commit, e2e on deploy. Keep tests close to code they test. One test file per source file typically. Large test files = split by scenario. Use test utilities for common patterns."
    },
    # === ADDITIONAL UNIT TESTING EXAMPLES ===
    {
        "question": "How do I test code that uses environment variables?",
        "answer": "Don't read env vars directly in business logic - inject configuration. For tests: mock os.environ (Python), process.env (Node). Libraries: pytest-env, dotenv-cli, jest.setup. Pattern: config class/module reads env vars, inject config into classes. Test different configurations by changing injected config. Never rely on system env vars in tests - explicit setup. Clear/restore env vars in teardown. Use .env.test for test-specific values. pytest: monkeypatch.setenv() for temporary changes."
    },
    {
        "question": "How do I test random or non-deterministic code?",
        "answer": "Inject randomness source: pass random.Random instance, seed for reproducibility. Mock random: fixed seed, mock random module. Property-based: use Hypothesis to test across random inputs. For UUIDs: inject ID generator, mock uuid module. Statistical tests: run many times, assert distribution. For ML: set random seeds (numpy, torch, tensorflow). Timestamps: inject clock/time provider. Don't: rely on 'probably works' - make deterministic or test properties."
    },
    {
        "question": "What is snapshot testing and when should I use it?",
        "answer": "Snapshot testing: serialize output, compare to saved 'snapshot'. Use for: complex output (rendered components, serialized data, error messages). Tools: Jest snapshots, pytest-snapshot, syrupy. Benefits: catches unexpected changes, easy to update. Risks: approving wrong snapshots, large diffs hard to review. Best for: UI components, API responses, generated code. Not for: simple assertions, frequently changing output. Review: actually look at snapshot changes, don't blindly update. Keep snapshots small and focused."
    },
    {
        "question": "How do I test GraphQL resolvers?",
        "answer": "Unit test: test resolver functions directly with mocked context/dataSources. Integration test: full GraphQL execution with test schema. Tools: apollo-server-testing, graphql-request, pytest-asyncio for async resolvers. Test: valid queries, validation errors, authorization, N+1 queries (dataloader). Mock: database, external services. Test mutations: verify side effects, return values. Test subscriptions: mock PubSub, verify events. Schema testing: validate schema structure, deprecation warnings."
    },
    {
        "question": "How do I test file system operations?",
        "answer": "Options: temp directories (pytest tmp_path, tempfile), virtual filesystems (pyfakefs, mock-fs), real files with cleanup. Pattern: create temp dir, run tests, cleanup in teardown. Test: read/write, permissions, errors (disk full, not found). pyfakefs: intercepts os/io calls, no real files. Benefits: fast, no cleanup needed, test edge cases. For Go: afero package. Always cleanup: use fixtures with automatic teardown. Avoid: touching real filesystem in tests."
    },
    {
        "question": "How do I test logging output?",
        "answer": "Python: caplog fixture (pytest), LogCapture. JavaScript: mock console, winston-mock. Pattern: capture logs during test, assert on log messages/levels. Test: correct level used, expected message content, structured log fields. Don't test: exact message wording (brittle), log timestamps. Do test: important events logged, error details included, no sensitive data logged. Integration: verify logs are searchable, include correlation IDs. Consider: log assertions indicate behavior testing, might be testing implementation."
    },
    {
        "question": "How do I test CLI applications?",
        "answer": "Tools: Click's CliRunner (Python), execa (Node), subprocess. Test: exit codes, stdout/stderr output, file outputs. Patterns: invoke command, capture output, assert. Test: help text, argument parsing, error messages, interactive prompts. Mock: stdin for input, filesystem for outputs. Click: isolated_filesystem context manager. Consider: test business logic separately from CLI parsing. E2E: full command with real subprocess. Integration: test CLI with real dependencies."
    },
    {
        "question": "How do I test background jobs and workers?",
        "answer": "Unit test: job handler logic in isolation. Integration: with message broker (testcontainers), verify job runs. Mock: queue for unit tests, test job handler directly. Test: job execution, retry logic, error handling, idempotency. Celery: pytest-celery, eager mode for sync execution. Bull/BullMQ: mock queue, test processor. Sidekiq: inline mode for tests. Verify: job enqueued with correct args, side effects happen. Timeout: add reasonable timeouts for async tests."
    },
]

# =============================================================================
# INTEGRATION TESTING
# =============================================================================

INTEGRATION_TESTING = [
    {
        "question": "What is the difference between unit and integration tests?",
        "answer": "Unit tests: single unit in isolation, mocked dependencies, fast (ms), many of them. Integration tests: multiple components together, real dependencies (DB, network), slower (seconds), fewer of them. Unit tests find: logic errors, regressions in unit. Integration tests find: wiring errors, interface mismatches, configuration issues. Test pyramid: base = unit tests, middle = integration, top = E2E. Run unit tests on every save, integration on commit, E2E on deploy pipeline."
    },
    {
        "question": "How do I test database code?",
        "answer": "Options: real database (most accurate), in-memory (H2, SQLite for simpler), test containers (Docker). Setup: transaction per test (rollback), fresh DB per suite, test fixtures. Test: CRUD operations, constraints, transactions, concurrent access. Patterns: repository pattern (easy to mock for unit tests), dedicated test database, migration testing. Fixtures: factory functions over fixtures (more flexible). Clean: truncate tables between tests or use transactions. Don't share data between tests."
    },
    {
        "question": "How do I test REST API endpoints?",
        "answer": "Tools: supertest (Express), TestClient (FastAPI), requests + pytest (Flask). Test: HTTP status codes, response body structure, headers, error responses. Patterns: test client makes requests, assert response. Test: auth (valid/invalid token), validation (bad input), edge cases (empty results, max limits). Setup: seed test data, clean between tests. Mock: external services the API calls. Don't mock: your own API. Integration level: test controller through DB, not just controller isolated."
    },
    {
        "question": "How do I use test containers effectively?",
        "answer": "Test containers: Docker containers for dependencies in tests. Benefits: real services (not mocks), consistent environment, isolated per test suite. Usage: PostgreSQL, Redis, Kafka, Elasticsearch, custom images. Libraries: testcontainers (Python, Java, JS). Pattern: start container in fixture, get connection URL, run tests, cleanup automatic. Performance: reuse containers across test sessions when possible. CI/CD: works with Docker-in-Docker or service containers. Best for integration tests, not unit tests (too slow)."
    },
    {
        "question": "How do I test message queue integrations?",
        "answer": "Tools: testcontainers for RabbitMQ/Kafka, embedded brokers, in-memory fakes. Test: message publishing, consumption, error handling, retry logic. Patterns: send message, wait for processing (with timeout), assert side effects. Challenges: async nature, ordering, timing. Solutions: polling with timeout, assertion helpers, test-specific queues. Test: dead letter handling, poison messages, idempotency. Mock: for unit tests of business logic. Real broker: for integration testing full flow."
    },
    {
        "question": "How do I test external API integrations?",
        "answer": "Options: mock responses (httpretty, responses, nock), record/replay (VCR), contract tests (Pact), real sandbox. Unit tests: mock HTTP layer, test your code's handling. Integration: hit sandbox/staging environment. Contract tests: verify API contract, catch breaking changes early. VCR: record real responses, replay in tests (fast, realistic). Challenges: rate limits, test data management, environment differences. Best practice: separate HTTP layer from business logic, mock at boundary."
    },
    {
        "question": "What are contract tests and when should I use them?",
        "answer": "Contract tests: verify consumer expectations match provider capabilities. Pact: consumer defines expected interactions, provider verifies it can fulfill. Benefits: catch integration issues early, don't need full environment. Use for: microservices communication, API between teams. Consumer-driven: consumer writes tests, provider runs them. Workflow: consumer generates pact file, share via broker, provider verifies. Not replacement for: E2E tests, manual testing. Best for: internal APIs, fast feedback on compatibility."
    },
    {
        "question": "How do I test WebSocket connections?",
        "answer": "Client: websocket-client (Python), ws (Node), browser APIs in tests. Server: test framework's WebSocket support, mock connections. Test: connection establishment, message sending/receiving, disconnection handling, reconnection logic. Patterns: connect, send message, wait for response (timeout), assert. Async handling: use async test support, event-driven assertions. Test: authentication, heartbeat/ping-pong, error scenarios. Mock for unit tests: fake WebSocket that records messages. Integration: real WebSocket server."
    },
]

# =============================================================================
# DEBUGGING TECHNIQUES
# =============================================================================

DEBUGGING = [
    {
        "question": "How do I debug a production issue without breaking production?",
        "answer": "Read-only investigation: check logs (structured logging helps), metrics, traces. Safe actions: add logging dynamically (if supported), check database reads (not writes), reproduce in staging. Avoid: debugging on prod with breakpoints, risky changes. Tools: distributed tracing (find failing request), log aggregation (search across services), APM (performance profile). If must modify: feature flags to isolate, canary deployment for fix, rollback ready. Document: incident timeline, findings for postmortem."
    },
    {
        "question": "How do I use breakpoints effectively?",
        "answer": "Strategic placement: at entry points, before suspected bug, after state changes. Conditional breakpoints: only break when condition true (avoid stepping through loops). Hit count breakpoints: break after N hits. Logpoints: print without stopping (VS Code). Watch expressions: monitor variable values. Don't: set too many breakpoints, leave debug code committed. Step types: into (enter function), over (skip function), out (finish function), continue (to next breakpoint). Debug configuration: launch.json for complex setups."
    },
    {
        "question": "What is rubber duck debugging?",
        "answer": "Explain code line-by-line to rubber duck (or colleague). The act of explanation often reveals the bug. Why it works: forces linear thinking, verbalization catches assumptions, breaks tunnel vision. How: describe what code should do, describe what it actually does, find discrepancy. Similar: write detailed bug report before asking for help, often solve it while writing. Variations: explain to junior dev, write documentation. Effective for: logic errors, misunderstandings, overlooked conditions."
    },
    {
        "question": "How do I debug memory leaks?",
        "answer": "Symptoms: growing memory over time, OOM errors, degraded performance. Tools: heap profiler (Chrome DevTools, py-spy, dotMemory), memory snapshots. Process: take snapshot, perform action, take another snapshot, compare. Look for: objects that should be garbage collected, growing collections, event listener accumulation. Common causes: event listeners not removed, closures holding references, caches without limits, global state growth. Fix: remove listeners, weak references, bounded caches. Production: monitor memory metrics, alert on growth."
    },
    {
        "question": "How do I debug race conditions?",
        "answer": "Symptoms: intermittent failures, works in debug (timing changes), different results on different machines. Detection: stress testing, random sleeps, thread sanitizers. Investigation: add extensive logging (timestamps), review shared state, check synchronization. Common causes: check-then-act without locks, shared mutable state, missing volatile/atomic. Prevention: immutability, proper synchronization, message passing over shared state. Tools: TSan (Thread Sanitizer), race detectors, deterministic testing. Reproduce: increase concurrency, add delays, repeat test many times."
    },
    {
        "question": "How do I debug a slow database query?",
        "answer": "First: get the query (enable slow query log, ORM query logging). Analyze: EXPLAIN ANALYZE (PostgreSQL), EXPLAIN (MySQL). Look for: full table scans, missing indexes, poor join order, excessive rows examined. Common fixes: add indexes (WHERE/JOIN columns), limit result set, optimize query structure. N+1 queries: add eager loading, batching. Check: database statistics are updated, index fragmentation. Monitoring: track query times, alert on slow queries. Consider: query caching, read replicas, denormalization for read-heavy."
    },
    {
        "question": "How do I use logging effectively for debugging?",
        "answer": "Structured logging: JSON format, consistent fields (timestamp, level, trace_id, context). Levels: ERROR (something failed), WARN (potential issue), INFO (significant events), DEBUG (detailed flow). Include: correlation IDs (trace requests), relevant context (user_id, request params), timing info. Don't log: sensitive data, excessive noise, redundant info. Dynamic levels: increase logging temporarily for debugging. Aggregation: centralized logging (ELK, Loki) for searching across services. Pattern: log at boundaries, include enough context to understand without reading code."
    },
    {
        "question": "How do I debug network issues?",
        "answer": "Client-side: browser DevTools Network tab, curl -v, httpie. Server-side: tcpdump, Wireshark, netstat. Proxy: mitmproxy, Charles Proxy (inspect HTTPS). Check: DNS resolution, connection establishment, TLS handshake, request/response. Common issues: DNS failures, firewall blocks, certificate errors, timeout settings, CORS. Debug steps: verify DNS (nslookup), test connectivity (telnet/nc), check TLS (openssl s_client), inspect traffic (proxy). Cloud: VPC flow logs, load balancer logs, WAF logs."
    },
    {
        "question": "How do I approach debugging an unfamiliar codebase?",
        "answer": "Start: read README, understand high-level architecture. Follow the flow: find entry point, trace request path. Tools: IDE navigation (go to definition, find usages), grep for strings. Add logging: at entry points, decision branches. Reproduce bug: minimal repro case. Hypothesize: what could cause this? Test hypotheses. Git blame: who wrote this, why, related changes. Tests: existing tests show intended behavior. Ask: team members who know the area. Document: your findings for next person. Don't: assume you understand without verifying."
    },
    {
        "question": "What is printf debugging and when is it useful?",
        "answer": "Printf debugging: add print statements to trace execution. When useful: quick exploration, remote systems without debugger, async code (debugger changes timing), production issues (via logging). Effective use: include context (variable values, function names), use clear markers (>>>>> HERE), remove when done. Better than debugger for: async flows, multi-threaded code, remote debugging. Worse than debugger for: stepping through logic, inspecting complex state. Modern version: structured logging that can be filtered/searched. Don't: leave debug prints in commits."
    },
]

# =============================================================================
# CODE QUALITY & COVERAGE
# =============================================================================

CODE_QUALITY = [
    {
        "question": "What is a good code coverage percentage?",
        "answer": "80% is generally good target. 100% is often counterproductive (testing trivial code, brittle tests). More important: quality over quantity - testing critical paths thoroughly. Coverage types: line (most common), branch (conditional paths), function. Low coverage areas: review, might be risky. High coverage != no bugs: can have tests that don't assert correctly. Don't: game coverage metrics, write tests just for coverage. Do: focus on business logic, edge cases, error paths. Use coverage to find gaps, not as success metric."
    },
    {
        "question": "How do I write tests that aren't brittle?",
        "answer": "Test behavior, not implementation: assert what, not how. Avoid: testing private methods, over-mocking, asserting internal state. Use: meaningful assertions, stable selectors (data-testid vs CSS classes). Allow: implementation changes without test changes. Patterns: arrange-act-assert clarity, one assertion focus, descriptive names. Reduce coupling: don't rely on test order, don't share state. Refactoring should not break tests (unless behavior changes). If test breaks often: probably testing implementation detail."
    },
    {
        "question": "How do I test legacy code without tests?",
        "answer": "First: characterization tests - capture current behavior (even if wrong). Add seams: dependency injection, extract interfaces for mocking. Pinning tests: high-level tests covering main flows. Then: refactor safely with test coverage. Golden master: snapshot current output, compare after changes. Approval testing: record output, approve or reject changes. Don't: rewrite without tests, assume you understand behavior. Book: 'Working Effectively with Legacy Code' by Feathers. Strategy: strangler fig pattern for gradual improvement."
    },
    {
        "question": "How do I test React components effectively?",
        "answer": "Tools: React Testing Library (recommended), Jest, Vitest. Philosophy: test like user interacts, not implementation details. Query: getByRole, getByText (accessibility-focused). Avoid: getByTestId (unless necessary), testing internal state, snapshot overuse. Test: user interactions (click, type), visible output, accessible behavior. Mock: external APIs (MSW), context providers. Don't mock: child components (usually), hooks (test through component). Patterns: render, interact, assert. Integration over unit: test component in realistic context."
    },
    {
        "question": "What is mutation testing?",
        "answer": "Mutation testing: modify code (mutations), check if tests catch changes. If tests pass with mutation: tests are weak. Mutations: change operators (+ to -), modify conditions, remove statements, change return values. Tools: mutmut (Python), Stryker (JS/TS), PITest (Java). Benefits: finds weak tests, improves test suite quality. Cost: slow (runs tests many times). Use: on critical code, not entire codebase. Survivors: mutations not caught - investigate, add tests. Goal: high mutation score (% of mutations killed)."
    },
    {
        "question": "How do I test microservices in isolation?",
        "answer": "Contract tests: verify service interfaces without full deployment. Consumer-driven contracts (Pact): consumers define expectations. Service virtualization: mock external services with recorded responses. Component tests: service + its database, mocked external services. Test doubles: mock other services, use during development. Strategies: test pyramid per service, integration tests at service boundary. Don't: rely only on E2E tests (slow, brittle). Do: comprehensive unit + contract tests, selective integration tests. CI/CD: run isolated tests on every commit."
    },
    {
        "question": "How do I handle flaky tests?",
        "answer": "Definition: tests that sometimes pass, sometimes fail without code changes. Common causes: timing issues, shared state, external dependencies, ordering dependencies. Debug: run repeatedly (--repeat flag), check for async issues, review resource cleanup. Fixes: wait for conditions (not fixed sleeps), isolate test data, mock time/randomness, fix shared state. Track: quarantine flaky tests, prioritize fixing. Culture: zero tolerance for ignored flaky tests. If can't fix: delete or rewrite test. Flaky tests erode confidence in test suite."
    },
    {
        "question": "How do I test error boundaries and fallbacks?",
        "answer": "Error boundaries (React): throw error in child, verify fallback renders. Test: different error types, recovery mechanisms, error reporting. Patterns: wrapper component that throws conditionally, mock throwing components. Fallback UI: verify meaningful error message displayed. Integration: test full error flow to error boundary. Also test: retry mechanisms, error logging, user actions after error. JavaScript: test uncaught errors, promise rejections. Backend: test error responses, error middleware, graceful degradation. Chaos: inject failures to verify handling."
    },
]

# =============================================================================
# E2E TESTING
# =============================================================================

E2E_TESTING = [
    {
        "question": "When should I write E2E tests vs unit tests?",
        "answer": "E2E tests: critical user journeys, integration across full stack, catch deployment issues. Unit tests: business logic, edge cases, fast feedback, specific component behavior. Test pyramid: many unit (fast), fewer integration, few E2E (slow but valuable). E2E for: checkout flow, authentication, critical business flows. Not E2E for: every feature, error cases (too slow), UI variations. Balance: E2E covers happy path, unit tests cover edge cases. E2E failure: harder to debug but catches real issues."
    },
    {
        "question": "How do I make E2E tests less flaky?",
        "answer": "Wait for elements: explicit waits over fixed sleeps, wait for conditions. Selectors: data-testid (stable), avoid CSS classes/XPath (brittle). Isolation: fresh test data, no shared state between tests. Retries: retry flaky actions (not entire test). Network: mock external services, control test data. Timing: wait for API responses, animations complete. Debug: screenshots on failure, video recording. Maintenance: review failed tests promptly, fix or delete. Tools: Playwright (modern, reliable), Cypress (good DX). Treat flakiness as bug, not acceptable."
    },
    {
        "question": "What tools should I use for E2E testing?",
        "answer": "Playwright: Microsoft, cross-browser, async/await, trace viewer, best reliability. Cypress: popular, good DX, same-origin limitation, automatic waiting. Selenium: oldest, widest browser support, more setup required. Puppeteer: Chrome/Firefox, Google, good for scraping. Choice: Playwright for new projects, Cypress if team knows it. Features needed: cross-browser, mobile viewport, network mocking, visual testing, trace/debug tools. Cloud: BrowserStack, Sauce Labs for device coverage. Headless: faster CI, headed for debugging."
    },
    {
        "question": "How do I structure E2E test suites?",
        "answer": "Organization: by user journey or feature area. Page objects: encapsulate page interactions, selectors, actions. Fixtures: test data setup and cleanup. Configuration: base URL, timeouts, retry settings per environment. Files: separate test files by feature, shared helpers in utilities. Naming: describe user action or journey (should_complete_checkout). Tags: smoke tests (fast, critical), regression (comprehensive). Run strategy: smoke on every commit, full suite nightly/pre-release. Keep: test count manageable, focus on critical paths."
    },
    {
        "question": "How do I test authentication flows end-to-end?",
        "answer": "Login tests: valid credentials, invalid credentials, account locked, MFA flow. Patterns: test via UI once, then use API/cookies for other tests (faster). Authenticated state: save cookies/storage, reuse across tests. OAuth: mock OAuth provider, or use test accounts. Token refresh: test token expiration, refresh flow. Session: test session timeout, concurrent sessions. Security: don't hardcode credentials, use environment variables. Test: logout, session invalidation, protected route access. Playwright: storageState for auth reuse across tests."
    },
    {
        "question": "How do I handle test data in E2E tests?",
        "answer": "Strategies: API seeding (fastest), UI setup (realistic but slow), database fixtures (direct but coupled). Isolation: unique data per test, cleanup after. Naming: include test ID in data (user_test123@email.com). Factory functions: generate test data programmatically. Shared data risks: test interference, order dependencies. Best practice: each test creates its own data, cleans up after. Large datasets: seed once, read-only tests. Reset: truncate tables, restore from snapshot. Avoid: relying on pre-existing data."
    },
]

def main():
    """Generate testing and debugging training examples."""
    all_examples = []
    
    # Unit Testing
    for item in UNIT_TESTING:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "testing",
                "subdomain": "unit_testing",
                "response_type": "concepts"
            }
        })
    
    # Integration Testing
    for item in INTEGRATION_TESTING:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "testing",
                "subdomain": "integration_testing",
                "response_type": "concepts"
            }
        })
    
    # Debugging
    for item in DEBUGGING:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "testing",
                "subdomain": "debugging",
                "response_type": "concepts"
            }
        })
    
    # Code Quality
    for item in CODE_QUALITY:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "testing",
                "subdomain": "code_quality",
                "response_type": "concepts"
            }
        })
    
    # E2E Testing
    for item in E2E_TESTING:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "testing",
                "subdomain": "e2e_testing",
                "response_type": "concepts"
            }
        })
    
    # Save to file
    output_file = DATA_DIR / "testing_debugging.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"  [OK] Saved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
