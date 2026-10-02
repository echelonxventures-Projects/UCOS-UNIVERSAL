# UCOS Ω∞ — Universal Capability Operating System

A platform factory: platforms (commerce, marketplaces, mobility, media, fintech, ERP, CRM, healthcare, government and future types) are **composed from certified capabilities, context, policies and metadata**, not hand-coded.

| Start here | What it is |
|---|---|
| [`UCOS-MASTER-ARCHITECTURE.md`](UCOS-MASTER-ARCHITECTURE.md) | The constitution: architecture, laws, meta-model, composition, runtime, trust, experience, operations, roadmap (v1.1+) |
| [`constitutions/`](constitutions/README.md) | One specification per universe (status table, amendments register), plus the Coverage Register, Temporal Binding Matrix and Industry/Product/Domain catalogue |
| [`engineering/`](engineering/) | Kernel design and Phase 1 readiness |
| [`docs/adr/`](docs/adr/README.md) | Architecture Decision Records (ADR-001…020) |
| [`docs/threat-models/`](docs/threat-models/README.md) | STRIDE threat models for Phase 0–1 surfaces |
| [`spec/`](spec/README.md) | Machine-readable schemas, capability manifests, object-type schemas, gate catalogue, error registry, rule facts, policies, decisions, reference platform definitions |
| [`tools/`](tools/) | `ucos_check.py` consistency checker (CI gate) · `gen_manifests.py` manifest source · `gen_registries.py` error registry and object-type schemas |
| `Chat.txt` | Original source material that the master document consolidates |

```bash
pip install pyyaml jsonschema
python3 tools/ucos_check.py          # must exit 0
```
