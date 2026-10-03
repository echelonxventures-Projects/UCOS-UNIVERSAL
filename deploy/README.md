# Deployment

| Path | What it is | Checked in CI by |
|---|---|---|
| `local/` | Development stack (Postgres with the kernel schema, Redpanda, Keycloak with a dev realm, Temporal and its UI), images pinned by digest. `make -C deploy/local up` | `docker compose config`; the **devstack** job starts it and runs `tools/devstack_smoke.sh` |
| `k8s/base`, `k8s/overlays/{dev,staging,prod}` | Cell baseline: restricted Pod Security, default-deny networking, gVisor runtime class for third-party packs (ADR-025), tier priority classes, quotas | `kubectl kustomize` + kubeconform (strict, Kubernetes 1.33) |
| `k8s/argocd` | ApplicationSet that deploys each cell from this repository (ADR-024) | kubeconform |
| `../kernel/Dockerfile` | `ucos` image: static, non-root, from scratch | **container** job builds and smoke-tests it; tagged releases push it to GHCR, keyless-signed with cosign, with an SPDX SBOM and SLSA provenance attestation |

**Not here yet:** cloud infrastructure for a cell (OpenTofu modules wrapped by Crossplane, ADR-024). It depends on the cloud provider, which is an open decision: see [ADR-037](../docs/adr/ADR-037-primary-cloud-provider-for-the-first-cells.md).
