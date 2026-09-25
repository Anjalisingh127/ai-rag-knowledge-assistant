---
document_id: RB-SLOW-API-001
title: Slow API Response Runbook
document_type: runbook
category: performance
service: shared
environment: simulated
tags: latency, slow-api, p95, cpu, database
---

# Slow API Response Runbook

## Triage
1. Establish the affected endpoint and latency percentile.
2. Check whether error rate increased with latency.
3. Compare application CPU, memory, worker saturation, and dependency latency.
4. Inspect slow database queries and recent code or configuration changes.
5. Reproduce with a controlled request when possible.

## Common causes
- Missing database indexes.
- Slow downstream dependencies.
- Worker or thread saturation.
- Excessive request concurrency.
- Expensive serialization or repeated external calls.

## Remediation
Fix the confirmed bottleneck rather than only increasing timeouts. Optimize queries, restore dependencies, adjust safe worker capacity, or roll back a performance regression.

## Validation
Repeat the same request or load profile and compare p50/p95 latency, error rate, and resource usage with the incident baseline.
