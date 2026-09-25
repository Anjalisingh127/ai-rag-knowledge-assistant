---
document_id: FAQ-SUPPORT-001
title: Application Support FAQ
document_type: faq
service: shared
environment: simulated
tags: support, incidents, escalation, logs, validation
---

# Application Support FAQ

## What evidence should I collect before escalation?
Record the incident ID, affected service and environment, start time, representative request IDs, error messages, recent changes, remediation attempted, and validation results.

## Should I restart a service immediately after a 503?
No. First check health, dependencies, configuration, deployment timing, and logs. Restart only an unhealthy instance when evidence supports it.

## How should secrets appear in logs?
Do not log passwords, API keys, tokens, or complete credentials. Log safe identifiers and error categories instead.

## What makes a resolution complete?
The immediate symptom is gone, a controlled validation request succeeds, relevant health and latency indicators are normal, and the incident record contains the root cause and remediation evidence.

## When should an issue be escalated?
Escalate when recovery requires infrastructure or database changes outside the application team's authority, a high-severity incident has no identified cause within the defined response window, or data integrity may be at risk.
