GenLayer Fact Attestation Registry

A reusable Intelligent Contract primitive for creating consensus-backed attestations from real-world web evidence.

What it does

A user submits:

- A factual claim
- Between 2 and 5 source URLs

GenLayer validators independently retrieve and evaluate the supplied evidence.

The contract produces one of three outcomes:

- "SUPPORTED"
- "REFUTED"
- "INCONCLUSIVE"

The consensus result is then stored on-chain and can be queried by other applications.

Why GenLayer?

Web information and language-model reasoning are nondeterministic. Different validators can interpret the same evidence differently.

This contract uses GenLayer consensus to require independent validators to agree on the substantive decision.

Validators check:

1. The verdict
2. The confidence score within a tolerance
3. The validity of the returned decision

The contract only commits the accepted consensus result to persistent state.

Architecture

User
 |
 | claim + source URLs
 v
Intelligent Contract
 |
 v
Leader
 |
 | retrieves sources
 | evaluates evidence
 v
Structured result
 |
 v
Independent Validators
 |
 | independently repeat evaluation
 v
Consensus
 |
 v
Stored Attestation

Example

A user could submit:

Claim:
"The organization published its annual report in 2026."

Sources:
- https://example.com/report
- https://example.org/announcement

Validators independently inspect the supplied sources.

The resulting attestation could contain:

{
  "verdict": "SUPPORTED",
  "confidence": 91,
  "reason": "Both supplied sources provide evidence supporting the claim."
}

If the evidence is insufficient or materially conflicting, the contract can instead return:

INCONCLUSIVE

Reusable Use Cases

The primitive can support:

- DAO governance research
- RWA information verification
- Research-source verification
- Grant and bounty verification
- Reputation systems
- Due-diligence workflows
- Evidence-backed application logic
- Web-information attestations

Design Principles

Evidence-first

The model is instructed to use the supplied sources rather than relying on prior knowledge.

Independent validation

Validators independently repeat the evidence-evaluation process rather than only checking output formatting.

Explicit uncertainty

The contract supports "INCONCLUSIVE" instead of forcing uncertain evidence into a binary answer.

Bounded nondeterminism

Only the evidence retrieval and language-model evaluation are nondeterministic. Persistent state updates occur after consensus.

Structured state

Each accepted attestation stores the claim, sources, verdict, confidence, and explanation.

Contract Interface

"attest(claim, source_urls)"

Creates a new consensus-backed attestation.

"get_attestation(attestation_id)"

Returns a stored attestation.

"get_count()"

Returns the number of stored attestations.

Limitations

This contract does not claim that a web source is inherently truthful.

The attestation represents validator consensus about the supplied evidence at execution time.

Source availability, source quality, and model interpretation can affect the result.

License

MIT
