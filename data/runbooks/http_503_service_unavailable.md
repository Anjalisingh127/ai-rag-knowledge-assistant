---
document_id: RB-HTTP-503-001
title: HTTP 503 Service Unavailable Runbook
document_type: runbook
service: shared
severity: SEV-2
environment: production-simulated
owner: application-support
last_reviewed: 2026-09-18
tags: http-503, availability, database-timeout, dependency-failure
---

# HTTP 503 Service Unavailable Runbook

## Purpose

Use this runbook when an application or API returns HTTP 503 responses. All
services, incidents and operational records in this project are synthetic.

## Common causes

- An application instance is unhealthy or restarting.
- The database connection pool is exhausted.
- A downstream dependency is unavailable.
- A deployment introduced an invalid configuration.
- CPU, memory or request traffic exceeded safe capacity.
- The load balancer has no healthy backend instances.

## Initial triage

1. Record the affected service, environment and detection time.
2. Determine whether one endpoint or the complete service is affected.
3. Review five-minute error counts and response-time trends.
4. Check recent deployments and configuration changes.
5. Correlate logs using the request ID.
6. Verify database and downstream dependency health.
7. Assign the appropriate incident severity.

## Application health check

Request:

GET /health

Expected response:

{
  "status": "healthy"
}

If the health check fails, inspect application startup and dependency logs.

## Database checks

Search for:

- DATABASE_TIMEOUT
- CONNECTION_POOL_EXHAUSTED
- CONNECTION_REFUSED

Identify slow or abandoned connections before increasing connection-pool
capacity.

## Deployment checks

Compare the incident start time with the latest deployment. Review:

- environment-variable changes;
- missing secrets;
- database migrations;
- dependency-version changes;
- health-check configuration.

## Remediation

Apply remediation only after confirming the likely cause:

- Restart only unhealthy instances.
- Roll back a faulty deployment using the approved procedure.
- Restore unavailable dependencies.
- Correct invalid configuration values.
- Terminate abandoned database sessions after approval.
- Scale healthy instances when application capacity is insufficient.
- Use bounded retries with exponential backoff for transient failures.

Do not repeatedly restart services without identifying the underlying cause.

## Validation

1. Confirm that the health endpoint is healthy.
2. Run a controlled test request.
3. Verify that the HTTP 503 rate is below the alert threshold.
4. Confirm that response latency has stabilized.
5. Monitor the service for at least 15 minutes.
6. Record the resolution and supporting evidence.

## Escalation

Escalate when:

- a SEV-1 cause is not identified within 15 minutes;
- database recovery or infrastructure changes are required;
- a rollback fails;
- multiple critical services are affected;
- data integrity may be at risk.

## Required evidence

- Incident ID
- Affected service and environment
- Start and recovery timestamps
- Representative request IDs
- Error count and latency
- Relevant log extracts
- Confirmed root cause
- Remediation performed
- Post-remediation validation
- Follow-up actions
