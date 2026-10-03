# ADR-037: Primary cloud provider for the first cells

| Field | Value |
|---|---|
| Status | **Proposed (decision needed before the first cell is provisioned, by 2026-12-15)** |
| Deciders | Architecture Board (U01 root authority), with the founders for the commercial terms |
| References | ADR-002 (cells), ADR-024 (OpenTofu + Crossplane), ADR-028 (multi-region tenants), U73; business/COST-MODEL.md §2 |

## Context
Phase 0 ends with a running cell, and the Phase 1 reference platform needs cells in **India** and the **UAE** (data residency, ADR-028). Everything above the cloud is portable by design: Kubernetes, Postgres, a Kafka-API bus, Keycloak, Temporal, and S3-compatible object storage, all behind ports (gate `ARCH-INF-01`). The cell's infrastructure code (OpenTofu modules wrapped by Crossplane) is the one part that must be written for a specific provider. Today `deploy/` holds only the provider-neutral layers: the Kubernetes baseline, the Argo CD ApplicationSet and the local development stack.

## Options
| Criterion | AWS | Azure | Google Cloud |
|---|---|---|---|
| India region(s) | Mumbai (ap-south-1), Hyderabad (ap-south-2) | Central India (Pune), South India, West India | Mumbai (asia-south1), Delhi (asia-south2) |
| UAE region | UAE (me-central-1) | UAE North (Dubai), UAE Central | Doha (me-central1) and Dammam (me-central2) are nearby; no UAE region at the time of writing; verify before relying on it |
| Managed Kubernetes | EKS | AKS | GKE |
| Managed Postgres 16+ | RDS / Aurora | Azure Database for PostgreSQL | Cloud SQL / AlloyDB |
| Kafka API | MSK | Event Hubs (Kafka API) | Managed Kafka |
| KMS / HSM for genesis keys | KMS, CloudHSM | Key Vault (Managed HSM) | Cloud KMS, Cloud HSM |
| gVisor (ADR-025) | self-managed node pool | self-managed node pool | GKE Sandbox (built in) |

Prices and region lists must be checked against each provider's current documentation before deciding; this table is a starting point, not a quotation.

## Decision criteria
1. In-country regions for both India and the UAE (residency is a hard requirement).
2. Startup credits and committed-use pricing for the cost model's baseline (cost model §2).
3. Team familiarity, so the first SRE hires can operate the platform.
4. Maturity of the Crossplane provider and OpenTofu modules for the chosen services.

## Consequences
Until this ADR is decided, CI validates the provider-neutral layers only, and the first cell cannot be provisioned. After the decision, `deploy/opentofu/` gains the cell module for the chosen provider, validated in CI with a pinned `tofu validate`, and the ApplicationSet lists the real cells.
