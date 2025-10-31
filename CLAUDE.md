# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment
- Python version: 3.10.11
- Package manager: uv
- Install dependencies: `uv sync` or `uv add <package>`
- **Project Type**: Local development project - NOT a distributable package
- **No packaging/building**: Do not add build systems, entry points, or package configuration to pyproject.toml

## Key Design Patterns
- **Functional style**: Pure functions return results rather than performing side effects
- **Dependency injection**: Dependencies passed as parameters for testability
- **Return values**: Functions return rich result objects rather than performing side effects
- **Separation of I/O and logic**: Business logic separated from I/O operations

## Security Best Practices
- **Secrets management**: NEVER pass credentials as function parameters or tool arguments
  - **Always use environment variables** for API keys, secrets, tokens, passwords
  - Read credentials at module initialization, not per-request
  - Credentials should never appear in logs, conversation history, or MCP protocol messages
  - Example: `API_KEY = os.getenv("API_KEY")` at module level, NOT as tool parameter
- **Input validation**: Validate and sanitize all user inputs
  - Use type hints and runtime validation for API inputs
  - Validate enum values, ranges, and formats
  - Reject malformed or unexpected input early
- **Common vulnerabilities**: Be aware of OWASP top 10
  - **No SQL injection**: Use parameterized queries, never string concatenation
  - **No command injection**: Avoid shell=True, validate inputs to subprocess calls
  - **No XSS**: Sanitize any HTML output, escape user content
  - **No path traversal**: Validate file paths, use Path().resolve() to prevent ../.. attacks
- **Security in code review**: Every PR must consider security implications
  - Are credentials exposed in tool schemas or function signatures?
  - Could user input be used maliciously?
  - Are we logging sensitive data?
  - Does documentation match implementation for security-critical features?

## Commands
- Run application: `PYTHONPATH=src uv run uvicorn main:app --reload`
- Run tests: `uv run pytest -n auto`
- Type check: `uv run pyrefly check`
- Lint code: `uv run ruff check .`
- Format code: `uv run ruff format .`
- ALWAYS preserve history when renaming by favoring `git mv file1 file2` over `mv file1 file2`
- ALWAYS preserve history when deleting by favoring `git rm file` over `rm file`
- Use the GitHub CLI command `gh` to interact with GitHub

## Code Style Guidelines
- **Imports**: Standard library first, then third-party, then local modules (alphabetized)
- **Formatting**: 4 spaces indentation, max line length ~100 chars, double quotes for strings
- **Types**: Use type annotations for all function parameters and return values
  - Use modern python typing syntax. Prefer str | None over Optional[str]. Prefer list over List and dict over Dict.
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error handling**: Use specific exception types with detailed error messages
- **Logging**: Use Python's logging module with appropriate log levels
  - **CRITICAL**: `logger.exception()` automatically captures the exception and stack trace
  - **NEVER pass the exception as a parameter**: `logger.exception("Message")` NOT `logger.exception(f"Message: {e}")`
  - The exception variable in the except clause is automatically included by Python's logging system
  - Examples:
    ```python
    # ✅ CORRECT - logger.exception() automatically includes exception details
    try:
        result = risky_operation()
    except Exception:
        logger.exception("Failed to perform operation")  # Exception auto-captured
        raise

    # ❌ WRONG - Redundant and incorrect
    try:
        result = risky_operation()
    except Exception as e:
        logger.exception(f"Failed to perform operation: {e}")  # DON'T DO THIS
        raise
    ```
- **Comments**: Write self-documenting code that minimizes the need for comments
  - **Avoid low-value comments** that restate what the code already says clearly
  - **Good comments explain WHY**, not what (the code shows what)
  - **Use expressive names** instead of comments whenever possible
  - **Acceptable comments**: Complex algorithms, non-obvious performance optimizations, business logic rationale, workarounds for library bugs
  - **Unacceptable comments**: Obvious statements, redundant descriptions, commented-out code
- **Principles**:
  - Prioritize simplicity, readability, and maintainability
  - Favor a functional style over object-oriented
  - Functions should be pure and avoid side effects
  - Follow best practices and Pythonic idioms
  - Favor slightly longer but descriptive variable names over comments
  - Favor comprehensions over loops. Favor nested loops over nested comprehensions

## Documentation
- All functions should have docstrings describing purpose and parameters
- New features should include usage examples

## Development Methodology
- **ALWAYS use Test-Driven Development (TDD)** for new features and bug fixes
  - Write comprehensive tests BEFORE implementing functionality
  - Cover success cases, error scenarios, edge cases, and backward compatibility
  - Use tests to drive design decisions and catch issues early
  - Aim for high test coverage with meaningful assertions
- **Contextual Flexibility**: While TDD is the mandate, limited flexibility may be warranted in specific scenarios
  - **Exploration phase**: Brief spikes without tests to learn and validate assumptions are acceptable
  - **Learning unknown domains**: When exploring unfamiliar APIs or algorithms, spike first to understand
  - **Critical constraint**: Any exploration MUST be followed by codifying insights with proper tests
  - **Refactor immediately**: Convert exploratory code to test-driven implementation once understanding is gained
  - **Default assumption**: If unsure whether flexibility applies, choose TDD
- **Test Categories**: Write tests for multiple scenarios
  - Happy path: Normal operation with valid inputs
  - Error handling: Network issues, invalid data, error conditions
  - Edge cases: Missing attributes, empty data, boundary conditions
  - Integration: Multiple components working together
  - Backward compatibility: Ensure existing functionality continues to work

## Architecture and Testing Philosophy
- **Prefer architectural fixes over complex mocking**: When tests require intricate mocking, consider if the code architecture needs improvement
  - **Red flag**: Functions with multiple responsibilities that require mocking many dependencies
  - **Solution**: Separate concerns - functions should do one thing well and return results
  - **Example**: Instead of a function that processes data AND sends notifications, separate into processing (returns results) + notification (uses results)
  - **Benefit**: Pure functions are easier to test, understand, and maintain

## Testing Best Practices
- **Risk-based test prioritization**: Focus testing effort where it provides maximum value
  - **Module/service boundaries**: Prefer behavior-focused tests at stable interfaces where invariants are well-defined
  - **Algorithmic cores**: Use property-based tests for parsing, transformation, and calculation logic to cover broad input spaces
  - **Critical paths**: Maintain small set of high-value end-to-end smoke tests for essential user workflows
  - **Contract tests**: Test service boundaries to reduce reliance on mocks and prevent interface drift
- **Design for testability**: Write code that's naturally easy to test without complex setup
  - **Return values over side effects**: Functions should return results rather than perform hidden actions
  - **Dependency injection**: Pass dependencies as parameters rather than hard-coding them
  - **Pure functions**: Prefer functions that produce the same output for the same input without side effects
- **Sophisticated mocking philosophy - treat mocks with suspicion**:
  - **Mock only true externalities**: Networks, time, randomness, and expensive resources (APIs, external services)
  - **Environment dependencies**: System clock, random number generation, environment variables
  - **NEVER perform real external actions during tests**: Always mock external integrations (APIs, webhooks, notifications)
  - **Prefer state-based assertions**: Test "what" the system produces, not "how" it produces it
  - **Avoid interaction verification**: Don't assert specific method calls unless the interaction itself is the behavior being tested
- **Mocking patterns**:
  - Use `@patch("module.function")` for simple function mocking
  - For async functions: `mock_func.return_value = asyncio.Future(); mock_func.return_value.set_result(result)`
  - Use dependency injection to make mocking easier: `def func(client=None): client = client or create_default_client()`
- **Test isolation**: Each test should be independent and not affect other tests
- **Use meaningful test data**: Create realistic test scenarios that reflect actual usage patterns

## Identifying Architecture Issues
Look for these patterns that suggest refactoring opportunities:
- **Functions doing multiple unrelated things** (processing + notification + logging + I/O operations)
- **Heavy mocking requirements** (>3 mocks per test suggests tight coupling)
- **Side effects in unexpected places** (`asyncio.run()` in the middle of sync functions)
- **Hard to test edge cases** (when mocking setup is more complex than the actual test)
- **Difficulty reusing code** (functions can't be called without triggering unwanted side effects)

## Refactoring Strategies
- **Return data structures**: Create dataclasses/TypedDicts to return rich results instead of void functions
- **Separate I/O from logic**: Keep business logic pure, move I/O to caller or dedicated functions
- **Single Responsibility Principle**: Each function should have one clear, well-defined purpose
- **Composition over inheritance**: Build complex behavior by combining simple functions
- **Dependency injection**: Make dependencies explicit parameters rather than hidden imports

## Test Code Maintainability
- **Treat tests as first-class code**: Apply the same quality standards to test code as production code
  - **Refactor test code**: Extract common setup, use helper functions, eliminate duplication
  - **Co-locate tests with behavior**: Keep tests close to the behavior they specify, not necessarily the implementation
  - **Remove brittle tests**: Delete tests that assert incidental structure rather than essential behavior
  - **Test names as documentation**: Use descriptive test names that clearly explain the scenario being tested
- **Test code smells to avoid**:
  - **Testing implementation details**: Focus on observable behavior, not internal method calls
  - **Excessive setup**: If test setup is complex, the design may need simplification
  - **Duplicative assertions**: Avoid testing the same behavior across multiple layers
  - **Magic numbers and strings**: Use meaningful constants and test data factories

## Workflow
- Follow modular design pattern seen in existing code
- Ensure proper environment variable handling with dotenv
- **Test-first approach**: Write tests before implementation code
- Always run linter, type checker, and all tests before committing code
- Use descriptive test names that clearly explain what is being tested
