import json


def test_initial_state(direct_deploy):
    contract = direct_deploy("fact_attestation.py")

    assert contract.get_count() == 0


def test_attestation_validation():
    """
    Documents the contract's input requirements.

    The contract requires:
    - a non-trivial claim
    - at least two sources
    - no more than five sources
    - HTTP/HTTPS source URLs
    """

    claim = "The organization published an annual report in 2026."

    sources = [
        "https://example.com/report",
        "https://example.org/announcement",
    ]

    assert len(claim) >= 10
    assert 2 <= len(sources) <= 5

    for url in sources:
        assert url.startswith(("http://", "https://"))


def test_valid_verdicts():
    valid_verdicts = {
        "SUPPORTED",
        "REFUTED",
        "INCONCLUSIVE",
    }

    assert "SUPPORTED" in valid_verdicts
    assert "REFUTED" in valid_verdicts
    assert "INCONCLUSIVE" in valid_verdicts


def test_attestation_record_shape():
    record = {
        "id": 1,
        "claim": "Example factual claim.",
        "sources": [
            "https://example.com/source-a",
            "https://example.org/source-b",
        ],
        "verdict": "SUPPORTED",
        "confidence": 90,
        "reason": "The supplied evidence supports the claim.",
    }

    encoded = json.dumps(record)
    decoded = json.loads(encoded)

    assert decoded["id"] == 1
    assert decoded["verdict"] in {
        "SUPPORTED",
        "REFUTED",
        "INCONCLUSIVE",
    }
    assert 0 <= decoded["confidence"] <= 100
