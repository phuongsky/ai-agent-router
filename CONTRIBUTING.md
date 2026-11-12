# Contributing

1. Open an issue describing the bug or feature.
2. Keep core routing logic IDE-independent.
3. Put IDE-specific configuration only under `adapters/<ide>/`.
4. Add tests for classification, path safety, duplicate handling, and persistence.
5. Run `pytest` and `ruff check .` before submitting a pull request.
6. Do not add telemetry, network calls, or automatic Git operations without an explicit
   design discussion and opt-in.
