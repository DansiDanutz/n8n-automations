import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = json.loads((ROOT / "src/workflow.json").read_text())
NODES = {node["name"]: node for node in WORKFLOW["nodes"]}


def test_webhook_requires_header_authentication():
    webhook = NODES["Lead Capture Webhook"]
    assert webhook["parameters"]["authentication"] == "headerAuth"
    assert webhook["credentials"]["httpHeaderAuth"]["id"] == "lead-webhook-auth"


def test_untrusted_input_is_validated_before_ai():
    validate = NODES["Validate Lead Input"]
    code = validate["parameters"]["jsCode"]
    assert "maxLengths" in code
    assert "escapeHtml" in code
    assert "Invalid lead email" in code
    assert WORKFLOW["connections"]["Lead Capture Webhook"]["main"][0][0]["node"] == "Validate Lead Input"
    assert WORKFLOW["connections"]["Validate Lead Input"]["main"][0][0]["node"] == "AI Lead Scorer"


def test_model_output_is_constrained_before_routing():
    validate = NODES["Validate AI Score"]
    code = validate["parameters"]["jsCode"]
    assert "['hot', 'warm', 'cold']" in code
    assert "Math.max(1, Math.min(10" in code
    assert WORKFLOW["connections"]["AI Lead Scorer"]["main"][0][0]["node"] == "Validate AI Score"
    assert WORKFLOW["connections"]["Validate AI Score"]["main"][0][0]["node"] == "Route by Segment"


def test_container_runtime_is_pinned():
    assert "FROM n8nio/n8n:2.31.6" in (ROOT / "Dockerfile").read_text()
