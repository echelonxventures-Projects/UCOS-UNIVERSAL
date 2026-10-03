# ADR-022: Composer Datalog: embedded Go evaluator with the Python checker as oracle

| Field | Value |
|---|---|
| Status | Accepted (provisional; confirmed by spike S-01 by 2027-01-15) |
| Deciders | Architecture Board (U01 root authority) |
| References | U58 Composition; KERNEL-DESIGN §9; PHASE1-READINESS S-01; ADR-006, ADR-018 |

## Context
The composer evaluates `spec/rules/core/closure.dl` over registry and tenant facts. It must be deterministic, give per-fact provenance (the "because" on every gap), re-evaluate incrementally when one fact changes, and run inside the Go control plane.

## Decision
Implement a **stratified, semi-naive Datalog evaluator in Go** inside the composer, with provenance recording, and incremental maintenance for single-fact changes. The rule language is the subset used by `closure.dl` (no arithmetic beyond comparisons; stratified negation). `tools/ucos_check.py` is the oracle: CI runs both on the golden platform definitions and requires byte-identical blueprints.

## Alternatives considered
- Soufflé: very fast batch evaluation, but it is a C++ code generator, awkward to embed, and its provenance mode is not incremental.
- Embedded Rust engine (Ascent/Crepe class) over FFI or gRPC: fast, but adds a second language to the control plane. Kept as the fallback if S-01 performance fails.

## Consequences
**Positive**
- One language in the control plane; provenance is first-class; deterministic by construction.
- The oracle comparison makes engine bugs visible in CI.

**Negative / costs**
- The team writes and maintains an evaluator; scope is kept small by the rule subset.

## Enforcement
S-01 (identical blueprints, < 10 s cold on 1M facts, < 1 s incremental); CI oracle comparison.
