# Architecture Decision Records

Each ADR records one significant decision: its context, the alternatives considered, the consequences and how it is enforced. ADRs are immutable once accepted. A change of direction is a new ADR that supersedes the old one, approved through U02 Governance with a U01 DecisionRecord (gate `ARCH-AUTH-01`).

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](ADR-001-interpret-metadata-at-runtime-generate-only-external-artifacts.md) | Interpret metadata at runtime; generate only external artifacts | Accepted (master v1.0) |
| [ADR-002](ADR-002-control-plane-data-plane-split-with-cells.md) | Control plane / data plane split with cells | Accepted (master v1.0) |
| [ADR-003](ADR-003-hybrid-physical-model-generated-tables-for-core-types-jsonb-fo.md) | Hybrid physical model: generated tables for core types, JSONB for tenant extensions | Accepted (master v1.0) |
| [ADR-004](ADR-004-temporal-is-a-foundation-universe-no-raw-start-end-dates-elsew.md) | Temporal is a foundation universe; no raw start/end dates elsewhere | Accepted (master v1.0; strengthened by A-46, A-63) |
| [ADR-005](ADR-005-single-pdp-cedar-for-rbac-abac-rebac-and-pbac.md) | Single PDP (Cedar) for RBAC, ABAC, ReBAC and PBAC | Accepted (master v1.0) |
| [ADR-006](ADR-006-composition-rules-in-datalog-over-the-knowledge-graph.md) | Composition rules in Datalog over the knowledge graph | Accepted (master v1.0) |
| [ADR-007](ADR-007-transactional-outbox-and-sagas-no-distributed-two-phase-commit.md) | Transactional outbox and sagas; no distributed two-phase commit | Accepted (master v1.0) |
| [ADR-008](ADR-008-global-product-master-separated-from-tenant-listings.md) | Global product master separated from tenant listings | Accepted (master v1.0) |
| [ADR-009](ADR-009-packs-as-signed-oci-artifacts-with-sbom-and-slsa-provenance-wa.md) | Packs as signed OCI artifacts with SBOM and SLSA provenance; WASM for in-process extensions | Accepted (master v1.0) |
| [ADR-010](ADR-010-ai-through-a-gateway-with-policy-based-routing-agents-are-iden.md) | AI through a gateway with policy-based routing; agents are identities with bounded authority | Accepted (master v1.0; detailed in U49–U51) |
| [ADR-011](ADR-011-bitemporal-canonical-objects.md) | Bitemporal canonical objects | Accepted (master v1.0) |
| [ADR-012](ADR-012-kafka-api-event-backbone-with-cloudevents-envelope.md) | Kafka-API event backbone with CloudEvents envelope | Accepted (master v1.0) |
| [ADR-013](ADR-013-cel-as-the-single-expression-language.md) | CEL as the single expression language | Accepted (A-22) |
| [ADR-014](ADR-014-frames-of-reference-u77-make-every-foundation-frame-aware.md) | Frames of reference (U77) make every foundation frame-aware | Accepted (A-23…A-28) |
| [ADR-015](ADR-015-communication-is-part-of-every-platform-s-base-set.md) | Communication is part of every platform's base set | Accepted (A-60, A-64, A-65) |
| [ADR-016](ADR-016-durable-workflow-engine-temporal-io-class-for-long-running-pro.md) | Durable workflow engine (Temporal.io class) for long-running processes | Accepted (master v1.0; U60) |
| [ADR-017](ADR-017-go-for-the-kernel-go-and-typescript-sdks-for-packs.md) | Go for the kernel; Go and TypeScript SDKs for packs | Accepted (KERNEL-DESIGN) |
| [ADR-018](ADR-018-a-reference-checker-precedes-the-production-composer.md) | A reference checker precedes the production composer | Accepted (A-66, A-69) |
| [ADR-019](ADR-019-derived-manifests-for-universes-beyond-phase-1.md) | Derived manifests for universes beyond Phase 1 | Accepted (A-69) |
| [ADR-020](ADR-020-postgres-row-level-security-as-the-tenancy-guard.md) | Postgres row-level security as the tenancy guard | Accepted (KERNEL-DESIGN §4) |

## Proposed (open decisions from the specs)
These stay *Proposed* until their spike or review completes (see `constitutions/README.md` → Open decisions):
- Reference identity provider, Keycloak or Ory (U09; P0 load spike).
- Datalog engine, Soufflé or an embeddable Rust engine (U58; P0 spike).
- Reservation counters at extreme peak, sharded Postgres or Redis (U13).
- Cell provisioning, Crossplane or plain OpenTofu (U73).
- gVisor sandbox for all third-party packs (U57; P2 spike).
- OpenFGA alongside Cedar for relationship-heavy cases (U03; P6).

Template: copy any ADR and keep the same headings.
