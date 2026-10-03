# ADR-034: Architecture Board composition

| Field | Value |
|---|---|
| Status | Accepted (structure); members named by the founders before P0 genesis |
| Deciders | Architecture Board (U01 root authority) |
| References | U01 Authority; open decision U01 |

## Context
The root authority approves level-3 decisions and constitutional amendments. Its membership must exist before the P0 genesis ceremony.

## Decision
The Architecture Board has **at least three members**: the CTO (chair), the chief architect and the CISO. The head of product is a member without a vote on security waivers. Quorum is two of three, including the chair or the CISO for security matters. Each member holds a hardware key used to sign DecisionRecords. Named members are recorded as a U01 DecisionRecord at genesis.

## Alternatives considered
- A single founder as root authority: a single point of failure and no separation of duties.

## Consequences
**Positive**
- Separation of duties from day one.

**Negative / costs**
- Decisions need two people; break-glass covers emergencies.

## Enforcement
`ARCH-AUTH-01`; genesis checklist.
