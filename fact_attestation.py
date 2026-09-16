from genlayer import *


class FactAttestationRegistry(gl.Contract):
    attestations: dict
    next_id: int

    def __init__(self):
        self.attestations = {}
        self.next_id = 1

    @gl.public.view
    def get_attestation(self, attestation_id: int):
        return self.attestations.get(str(attestation_id))

    @gl.public.view
    def get_count(self) -> int:
        return self.next_id - 1

    @gl.public.write
    def attest(
        self,
        claim: str,
        source_urls: list[str],
    ) -> int:

        if not claim or len(claim.strip()) < 10:
            raise Exception("Claim is too short")

        if len(source_urls) < 2:
            raise Exception("At least two sources are required")

        if len(source_urls) > 5:
            raise Exception("Maximum five sources")

        for url in source_urls:
            if not (
                url.startswith("https://")
                or url.startswith("http://")
            ):
                raise Exception("Invalid source URL")

        def evaluate():
            evidence = []

            for url in source_urls:
                page = gl.nondet.web.get(url)
                content = page.body.decode("utf-8")[:12000]

                evidence.append({
                    "url": url,
                    "content": content,
                })

            prompt = f"""
You are an evidence verification agent.

Claim:
{claim}

Evaluate the supplied web sources.

Return ONLY valid JSON:

{{
  "verdict": "SUPPORTED" | "REFUTED" | "INCONCLUSIVE",
  "confidence": 0-100,
  "reason": "short explanation",
  "source_assessments": [
    {{
      "url": "source URL",
      "supports": true | false | null
    }}
  ]
}}

Use only the supplied evidence.
Do not use prior knowledge.
Do not invent information.
If evidence is insufficient or conflicting, return INCONCLUSIVE.

Sources:
{evidence}
"""

            result = gl.nondet.exec_prompt(prompt)

            return result

        def validator(leader_result):
            if not isinstance(leader_result, gl.vm.Return):
                return False

            try:
                leader = leader_result.calldata

                if leader["verdict"] not in [
                    "SUPPORTED",
                    "REFUTED",
                    "INCONCLUSIVE",
                ]:
                    return False

                confidence = int(leader["confidence"])

                if confidence < 0 or confidence > 100:
                    return False

                independent = evaluate()

                if independent["verdict"] != leader["verdict"]:
                    return False

                return True

            except Exception:
                return False

        result = gl.vm.run_nondet_unsafe(
            evaluate,
            validator,
        )

        if not isinstance(result, gl.vm.Return):
            raise Exception("Consensus failed")

        result_data = result.calldata

        attestation_id = self.next_id

        self.attestations[str(attestation_id)] = {
            "id": attestation_id,
            "claim": claim,
            "sources": source_urls,
            "result": result_data,
        }

        self.next_id += 1

        return attestation_id
