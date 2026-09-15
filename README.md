# Recorded chatbot transcript evaluations

This project tests recorded, non-live conversations with pytest and DeepEval.

## Transcript fixtures

The eight supplied raw files live in `transcripts/` with their original names:

`conversation-01-return.txt` through `conversation-08-order-status.txt`.

Each test module parses its raw timeline through shared helpers and contains two tests: one deterministic contract test and one ChatGPT judge test. Deterministic scenario contracts include expected facts, consent requirements, privacy rules, and prohibited claims.

## Install and run

```powershell
python -m pip install -e .
# Copy .env.example to .env and enter the key locally.
pytest -m deterministic
pytest -m llm_judge
pytest

# Run one transcript file from the repository root:
pytest -v tests/test_conversation_01_return.py
```

The deterministic suite validates all eight records and flags transcript defects without network access. The DeepEval suite has one case per transcript and sends the caller input, agent output, and raw transcript context to the configured ChatGPT judge. It defaults to `gpt-4o` and reads `OPENAI_JUDGE_MODEL` from `.env` when provided.

These are pytest-native tests that call DeepEval's `assert_test`; use `pytest` rather than `deepeval test run` for an individual transcript file.
