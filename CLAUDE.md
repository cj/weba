# CLAUDE.md - Weba Project Commands

This document contains important commands and procedures for working with the optimized weba project.

## Initialization and Setup

```bash
# Install dependencies
uv pip install -e .

# Run tests to verify installation
make test

# Run linting checks
make check
```

## Important Environment Variables

The weba project uses the following environment variables for configuration:

```bash
# Set LRU cache size (default is None/disabled)
export WEBA_LRU_CACHE_SIZE=256  # Set to desired cache size

# HTML parser configuration
export WEBA_HTML_PARSER="html.parser"  # Default
export WEBA_XML_PARSER="xml"          # Default
```

## Development Workflow

When making changes to improve performance or fix bugs:

1. Run tests before and after changes
2. Ensure all type annotations are properly maintained
3. Use proper pyright ignore format when necessary: `# pyright: ignore[reportUnknownArgumentType]`
4. Verify all examples have clear output documentation

## Critical Files for Performance

The following files contain performance-critical code that has been optimized:

- `weba/tag.py` - Contains Tag class with optimized attribute handling
- `weba/component.py` - Contains optimized component initialization and caching
- `weba/ui.py` - Contains HTML generation with optimized string handling

## Common Performance Pitfalls

1. Be careful with list comprehensions for collections with unknown types
2. Avoid unbounded caches - always set size limits
3. Use proper type annotations to help the type checker
4. Test with both small and large HTML structures

## Testing Commands

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_component.py

# Run specific test
python -m pytest tests/test_ui.py::test_ui_attributes
```

## Linting Commands

```bash
# Run all linting
make check

# Check specific file
pyright weba/tag.py

# Apply auto-fixes with ruff
ruff check --fix weba/
```

Remember to always maintain type safety according to the project conventions, and ensure all tests pass after making changes.
