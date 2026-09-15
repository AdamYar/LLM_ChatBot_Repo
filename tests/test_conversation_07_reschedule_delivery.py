import os

import pytest

from transcript_test_support import assert_deterministic, run_llm_judge


@pytest.mark.deterministic
def test_conversation_07_reschedule_delivery_deterministic():
    assert_deterministic("conversation-07")


@pytest.mark.llm_judge
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY is required")
def test_conversation_07_reschedule_delivery_chatgpt_judge():
    run_llm_judge("conversation-07")