# Fact Attestation Registry

A reusable GenLayer Intelligent Contract for source-grounded verification of real-world factual claims.

## Purpose

A user submits a claim and one or more public source URLs. When `verify_claim` is called, GenLayer nodes independently fetch the sources, extract evidence, and evaluate the claim. Consensus accepts the result only when the leader and validator agree on the core verdict and their confidence scores are within a defined tolerance.

The contract stores the claim, sources, verdict, confidence, evidence summary, verification result, and submitter.

## Why this is useful

The primitive can support:
- research and document verification;
- source-grounded AI agent workflows;
- DAO proposal evidence;
- content provenance;
- event and announcement attestation;
- reputation and information registries.

## Consensus design

The contract uses `gl.vm.run_nondet_unsafe` with:
- `evaluate_sources` as the leader function;
- `validate_result` as the validator function.

The validator independently fetches the same submitted sources and reruns the structured evaluation. It rejects the leader result unless:
1. the verdict is one of `SUPPORTED`, `CONTRADICTED`, or `INCONCLUSIVE`;
2. confidence is an integer from 0 to 100;
3. the summary is non-empty and bounded;
4. the independent verdict matches the leader verdict;
5. confidence differs by no more than 20 points.

Raw webpage text is never compared directly. Only the structured decision fields are compared, which is more appropriate for changing web pages and LLM outputs.

## Contract methods

| Method | Type | Purpose |
|---|---|---|
| `submit_claim(claim, sources)` | write | Create a pending claim |
| `verify_claim(claim_id)` | write | Fetch sources and reach consensus |
| `get_claim(claim_id)` | view | Read the complete record |
| `get_claim_count()` | view | Count submitted claims |
| `get_verification_status(claim_id)` | view | Read pending/verified status |

## Example

Claim:
`The Earth revolves around the Sun.`

Sources:
`https://en.wikipedia.org/wiki/Earth`

## Deployment

1. Copy `fact_attestation.py` into GenLayer Studio.
2. Confirm the contract schema loads.
3. Deploy without constructor arguments.
4. Call `submit_claim` with a claim and comma-separated URLs.
5. Call `verify_claim` using the returned claim ID.
6. Read the result with `get_claim`.

## Limitations

- Web pages can be unavailable, dynamic, or changed after verification.
- Source quality is evaluated by the model and should not be treated as an absolute guarantee.
- The contract records a consensus attestation at verification time, not permanent truth.
- Keep submitted URLs public and reasonably stable.
