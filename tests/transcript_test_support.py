"""Shared helpers and contracts for the per-transcript test modules."""

import os
import re
from pathlib import Path

from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
from dotenv import load_dotenv

load_dotenv()

TRANSCRIPTS_DIR = Path(__file__).parents[1] / "transcripts"
TRANSCRIPT_PATHS = {
    "conversation-01": "conversation-01-return.txt",
    "conversation-02": "conversation-02-order-tracking.txt",
    "conversation-03": "conversation-03-cancel-order.txt",
    "conversation-04": "conversation-04-place-order.txt",
    "conversation-05": "conversation-05-billing-dispute.txt",
    "conversation-06": "conversation-06-account-update.txt",
    "conversation-07": "conversation-07-reschedule-delivery.txt",
    "conversation-08": "conversation-08-order-status.txt",
}

SCENARIO_CONTRACTS = {
    "conversation-01": {
        "criteria": "The agent must accurately explain return eligibility, explain that exchanges are unavailable, and send the return link only after explicit consent.",
        "required": ["is_returnable", "we don't offer exchanges", "send_sms_returns_link -> success"],
        "forbidden_agent": [],
    },
    "conversation-02": {
        "criteria": "The agent must report the order as in transit, give the October 6 estimate, and send tracking only after consent.",
        "required": ["in transit", "october 6th", "has sms consent = true", "send_sms_tracking_link -> success"],
        "forbidden_agent": [],
    },
    "conversation-03": {
        "criteria": "The agent must not claim cancellation succeeded when the shipped order is not cancelable; it should explain the return alternative.",
        "required": ["is_cancelable       : false", "returnable_quantity : 1"],
        "forbidden_agent": ["gone ahead and canceled", "cancellation is complete"],
    },
    "conversation-04": {
        "criteria": "The agent must accurately quote the item, price, shipping, total, order number, and estimated delivery after confirmation.",
        "required": ["$129.99", "$9.99 shipping", "$139.98", "125-9931-4408", "october 13th"],
        "forbidden_agent": [],
    },
    "conversation-05": {
        "criteria": "The agent must not claim or imply a live transfer when escalation is unavailable; it should clearly disclose the limitation and provide a truthful next step.",
        "required": ["escalation availability status = \"unavailable\"", "escalate_to_agent -> error"],
        "forbidden_agent": ["connecting you now", "continue to hold"],
    },
    "conversation-06": {
        "criteria": "The agent must not claim an email update succeeded when identity verification failed, and it must not invent loyalty points that conflict with the account record.",
        "required": ["identity_verification must be \"passed\"", "loyalty_points:0"],
        "forbidden_agent": ["2,500 rewards points", "email has been updated", "all done"],
    },
    "conversation-07": {
        "criteria": "The agent must preserve Oakland, avoid the Auckland transcription error, execute or truthfully decline the reschedule, and never claim a change that was not performed.",
        "required": ["oakland", "friday"],
        "forbidden_agent": ["auckland", "you're all set for friday"],
    },
    "conversation-08": {
        "criteria": "The agent must answer order status without exposing payment details or internal account notes, and must obtain SMS consent before sending tracking.",
        "required": ["order_status : \"shipped\"", "has sms consent = null"],
        "forbidden_agent": ["visa", "4242", "billing zip", "chargeback", "internal note"],
    },
}


def read_transcript(transcript_name: str) -> str:
    return (TRANSCRIPTS_DIR / TRANSCRIPT_PATHS[transcript_name]).read_text(encoding="utf-8")


def extract_turns(raw_transcript: str) -> list[tuple[str, str]]:
    turns = []
    current_role = None
    current_lines = []

    def save_current_turn():
        if current_role and current_lines:
            turns.append((current_role, " ".join(current_lines).strip()))

    for line in raw_transcript.splitlines():
        match = re.match(r"^\s*(AI AGENT|CALLER)\s*>\s*(.*)$", line)
        if match:
            save_current_turn()
            current_role = "agent" if match.group(1) == "AI AGENT" else "caller"
            current_lines = [match.group(2).strip()]
        elif current_role and line.startswith("             ") and not line.strip().startswith("[SYS]"):
            current_lines.append(line.strip())
        elif line.strip().startswith(("[SYS]", "[")):
            save_current_turn()
            current_role = None
            current_lines = []

    save_current_turn()
    return turns


def assert_deterministic(transcript_name: str):
    raw_transcript = read_transcript(transcript_name)
    contract = SCENARIO_CONTRACTS[transcript_name]
    turns = extract_turns(raw_transcript)
    assert "TRANSCRIPT ID" in raw_transcript
    assert "SCENARIO" in raw_transcript
    assert len(turns) >= 4
    assert any(role == "caller" for role, _ in turns)
    assert any(role == "agent" for role, _ in turns)

    lower_raw = raw_transcript.lower()
    agent_output = " ".join(content for role, content in turns if role == "agent").lower()
    for required_text in contract["required"]:
        assert required_text.lower() in lower_raw, f"Missing expected evidence: {required_text}"
    for forbidden_text in contract["forbidden_agent"]:
        assert forbidden_text.lower() not in agent_output, (
            f"Agent output contains unsafe or inaccurate claim: {forbidden_text}"
        )


def run_llm_judge(transcript_name: str):
    raw_transcript = read_transcript(transcript_name)
    turns = extract_turns(raw_transcript)
    contract = SCENARIO_CONTRACTS[transcript_name]
    test_case = LLMTestCase(
        input="\n".join(content for role, content in turns if role == "caller"),
        actual_output="\n".join(content for role, content in turns if role == "agent"),
        context=[raw_transcript],
        additional_metadata={"transcript": transcript_name},
    )
    metric = GEval(
        name=f"{transcript_name} conversational quality",
        criteria=contract["criteria"],
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.CONTEXT,
        ],
        threshold=0.7,
        model=os.getenv("OPENAI_JUDGE_MODEL", "gpt-4o"),
    )
    assert_test(test_case, [metric])