# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json
import typing


class FactAttestationRegistry(gl.Contract):
    """Source-grounded factual claim verification using GenLayer consensus."""

    claims: DynArray[str]
    source_urls: DynArray[str]
    statuses: DynArray[str]
    verdicts: DynArray[str]
    confidence_scores: DynArray[u32]
    evidence_summaries: DynArray[str]
    verification_results: DynArray[str]
    submitters: DynArray[Address]

    def __init__(self):
        self.claims = DynArray[str]()
        self.source_urls = DynArray[str]()
        self.statuses = DynArray[str]()
        self.verdicts = DynArray[str]()
        self.confidence_scores = DynArray[u32]()
        self.evidence_summaries = DynArray[str]()
        self.verification_results = DynArray[str]()
        self.submitters = DynArray[Address]()

    @gl.public.write
    def submit_claim(self, claim: str, sources: str) -> u32:
        """Submit a claim and comma-separated public source URLs."""
        if len(claim.strip()) == 0:
            raise gl.UserError("Claim cannot be empty")
        if len(claim) > 1000:
            raise gl.UserError("Claim exceeds 1000 characters")
        if len(sources.strip()) == 0:
            raise gl.UserError("At least one source URL is required")

        claim_id = u32(len(self.claims))
        self.claims.append(claim.strip())
        self.source_urls.append(sources.strip())
        self.statuses.append("PENDING")
        self.verdicts.append("UNVERIFIED")
        self.confidence_scores.append(u32(0))
        self.evidence_summaries.append("")
        self.verification_results.append("")
        self.submitters.append(gl.message.sender_address)
        return claim_id

    @gl.public.write
    def verify_claim(self, claim_id: u32) -> str:
        """Fetch submitted sources and reach consensus on a structured verdict."""
        if claim_id >= u32(len(self.claims)):
            raise gl.UserError("Invalid claim ID")
        if self.statuses[claim_id] == "VERIFIED":
            raise gl.UserError("Claim is already verified")

        claim = self.claims[claim_id]
        sources = self.source_urls[claim_id]
        source_list = [url.strip() for url in sources.split(",") if url.strip()]

        if len(source_list) == 0:
            raise gl.UserError("No usable source URLs found")

        task = f"""
Verify the factual claim below using only the supplied source material.

CLAIM:
{claim}

Return JSON with exactly these fields:
{{
  "verdict": "SUPPORTED" | "CONTRADICTED" | "INCONCLUSIVE",
  "confidence": integer from 0 to 100,
  "summary": "brief evidence-grounded explanation",
  "sources": ["URLs actually used"]
}}

Rules:
- Do not invent sources or facts.
- Use INCONCLUSIVE when evidence is missing or materially conflicting.
- Confidence must reflect the strength and agreement of the supplied evidence.
- Keep summary below 600 characters.
"""

        def evaluate_sources():
            evidence_parts = []
            for url in source_list:
                try:
                    response = gl.nondet.web.get(url)
                    body = response.body.decode("utf-8")
                    evidence_parts.append(
                        "SOURCE URL: " + url + "\nCONTENT:\n" + body[:5000]
                    )
                except Exception:
                    evidence_parts.append(
                        "SOURCE URL: " + url + "\nUNAVAILABLE"
                    )

            evidence = "\n\n".join(evidence_parts)[:18000]
            prompt = task + "\n\nSOURCE MATERIAL:\n" + evidence
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            return raw

        def validate_result(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False

            proposed = leader_result.calldata
            if not isinstance(proposed, dict):
                return False

            verdict = proposed.get("verdict", "")
            confidence = proposed.get("confidence", -1)
            summary = proposed.get("summary", "")
            used_sources = proposed.get("sources", [])

            if verdict not in ("SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"):
                return False
            if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
                return False
            if not isinstance(summary, str) or len(summary) == 0 or len(summary) > 600:
                return False
            if not isinstance(used_sources, list):
                return False

            # Independently fetch and evaluate the same sources.
            validator_evidence_parts = []
            for url in source_list:
                try:
                    response = gl.nondet.web.get(url)
                    body = response.body.decode("utf-8")
                    validator_evidence_parts.append(
                        "SOURCE URL: " + url + "\nCONTENT:\n" + body[:5000]
                    )
                except Exception:
                    validator_evidence_parts.append(
                        "SOURCE URL: " + url + "\nUNAVAILABLE"
                    )

            validator_evidence = "\n\n".join(validator_evidence_parts)[:18000]
            validator_prompt = task + "\n\nSOURCE MATERIAL:\n" + validator_evidence
            independent = gl.nondet.exec_prompt(
                validator_prompt,
                response_format="json"
            )

            if not isinstance(independent, dict):
                return False

            independent_verdict = independent.get("verdict", "")
            independent_confidence = independent.get("confidence", -1)

            if independent_verdict not in (
                "SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"
            ):
                return False
            if not isinstance(independent_confidence, int):
                return False

            # Core decision must match. Confidence has a tolerance.
            if verdict != independent_verdict:
                return False
            if abs(confidence - independent_confidence) > 20:
                return False

            return True

        result = gl.vm.run_nondet_unsafe(evaluate_sources, validate_result)

        if not isinstance(result, dict):
            raise gl.UserError("Consensus returned an invalid result")

        verdict = result.get("verdict", "INCONCLUSIVE")
        confidence = result.get("confidence", 0)
        summary = result.get("summary", "")
        used_sources = result.get("sources", [])

        self.statuses[claim_id] = "VERIFIED"
        self.verdicts[claim_id] = verdict
        self.confidence_scores[claim_id] = u32(confidence)
        self.evidence_summaries[claim_id] = summary
        self.verification_results[claim_id] = json.dumps(
            {
                "verdict": verdict,
                "confidence": confidence,
                "summary": summary,
                "sources": used_sources,
            },
            sort_keys=True,
        )

        return self.verification_results[claim_id]

    @gl.public.view
    def get_claim(self, claim_id: u32) -> dict:
        if claim_id >= u32(len(self.claims)):
            raise gl.UserError("Invalid claim ID")

        return {
            "claim_id": claim_id,
            "claim": self.claims[claim_id],
            "sources": self.source_urls[claim_id],
            "status": self.statuses[claim_id],
            "verdict": self.verdicts[claim_id],
            "confidence": self.confidence_scores[claim_id],
            "summary": self.evidence_summaries[claim_id],
            "verification_result": self.verification_results[claim_id],
            "submitter": self.submitters[claim_id].as_hex,
        }

    @gl.public.view
    def get_claim_count(self) -> u32:
        return u32(len(self.claims))

    @gl.public.view
    def get_verification_status(self, claim_id: u32) -> str:
        if claim_id >= u32(len(self.claims)):
            raise gl.UserError("Invalid claim ID")
        return self.statuses[claim_id]
