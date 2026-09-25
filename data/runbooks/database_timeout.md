---
document_id: RB-DB-TIMEOUT-001
title: Database Timeout Troubleshooting Runbook
document_type: runbook
category: database
service: shared
environment: simulated
tags: database-timeout, connection-pool, slow-query, connectivity
---

# Database Timeout Troubleshooting Runbook

## When to use
Use this runbook for DATABASE_TIMEOUT, connection-pool wait failures, or database connection errors.

## Triage
1. Confirm the affected service and database dependency.
2. Compare timeout start time with deployments or configuration changes.
3. Check active connections, pool usage, wait time, and slow-query evidence.
4. Verify the host and port before changing pool size.
5. Identify whether the issue is saturation, a slow query, or connectivity.

## Common causes
- Long-running queries holding connections.
- Pool exhaustion caused by leaked or abandoned connections.
- Incorrect host, port, or credentials.
- Database restart or unavailable network path.
- Timeout settings that are shorter than normal query duration.

## Remediation
Cancel or optimize confirmed long-running queries, correct invalid configuration, restore connectivity, and restart only the affected application instance when necessary. Do not increase pool capacity without identifying why connections are unavailable.

## Validation
Confirm successful database connectivity, healthy application status, normal pool wait time, and successful controlled requests. Monitor for recurrence and record the supporting evidence.
