# Recorded chatbot transcript evaluations

This project tests recorded, non-live conversations with pytest and DeepEval.

## Transcript fixtures

The eight supplied raw files live in `transcripts/` with their original names:

`conversation-01-return.txt` through `conversation-08-order-status.txt`.

The test module parses `AI AGENT >` and `CALLER >` timeline entries directly. Deterministic scenario contracts are maintained in the test module, including expected facts, consent requirements, privacy rules, and prohibited claims.

## Install and run

```powershell
python -m pip install -e .
# Copy .env.example to .env and enter the key locally.
pytest -m deterministic
pytest -m llm_judge
pytest
```

The deterministic suite validates all eight records and flags transcript defects without network access. The DeepEval suite has one case per transcript and sends the caller input, agent output, and raw transcript context to the configured ChatGPT judge. It defaults to `gpt-4o` and reads `OPENAI_JUDGE_MODEL` from `.env` when provided.
