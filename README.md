# UCOS Ω∞ — Universal Capability Operating System

A platform factory: platforms (commerce, marketplaces, mobility, media, fintech, ERP, CRM, healthcare, government and future types) are **composed from certified capabilities, context, policies and metadata**, not hand-coded.

| Start here | What it is |
|---|---|
| [`UCOS-MASTER-ARCHITECTURE.md`](UCOS-MASTER-ARCHITECTURE.md) | The constitution: architecture, laws, meta-model, composition, runtime, trust, experience, operations, roadmap (v1.1+) |
| [`constitutions/`](constitutions/README.md) | One specification per universe (status table, amendments register), plus the Coverage Register, Temporal Binding Matrix and Industry/Product/Domain catalogue |
| [`engineering/`](engineering/) | Kernel design and Phase 1 readiness |
| [`spec/`](spec/README.md) | Machine-readable schemas, capability manifests, rule facts, policies, decisions, reference platform definitions |
| [`tools/ucos_check.py`](tools/ucos_check.py) | Consistency checker (CI gate) |
| `Chat.txt` | Original source material that the master document consolidates |

```bash
pip install pyyaml jsonschema
python3 tools/ucos_check.py          # must exit 0
```
