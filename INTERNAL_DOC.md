# Internal Documentation

## Modules

- `ai_discussion/utils.py` – helpers for text formatting. Contains `strip_markdown` to remove markdown markup and `format_history` which joins a list of messages.
- `ai_discussion/discusser_base.py` – abstract base class for all discussers. Uses `format_history` for history handling.
- `ai_discussion/discusser.py` – implementation using pluggable AI backends.
- `ai_discussion/simple_discusser.py` – rule based discusser used for tests and simple interactions.
- `ai_discussion/ai_backends.py` – contains `GeminiBackend` and `OpenAIBackend` classes for real API calls.
- `ai_discussion/discussion.py` – high level routine `run_discussion` that coordinates a multi-agent discussion.

## Tests

The `tests/` directory contains unit tests using `pytest`:

- `tests/test_utils.py` – covers markdown stripping and history formatting.
- `tests/test_base.py` – verifies base helper `_format_discussion_history` via a dummy discusser.
- `tests/test_discusser.py` – checks name transliteration for AI discussers.
- `tests/test_simple_discusser.py` – exercises simple discusser consensus logic.

All tests can be executed with `pytest`.

## Improvements

- Introduced `utils.py` with common helper functions.
- Added type hints and Google style docstrings to public functions.
- Refactored `run_discussion` for clarity with explicit parameters and documentation.
- Added minimal unit test suite.

