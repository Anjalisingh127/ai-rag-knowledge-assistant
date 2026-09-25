---
document_id: RB-NETWORK-001
title: Network Connectivity Runbook
document_type: runbook
category: network
service: shared
environment: simulated
tags: dns, tcp, connection-refused, timeout, connectivity
---

# Network Connectivity Runbook

## Triage
1. Confirm the exact source and destination service.
2. Resolve the configured hostname.
3. Verify the destination port and protocol.
4. Test TCP connectivity from the affected environment.
5. Distinguish DNS failure, connection refusal, and timeout.

## Common causes
- Incorrect hostname or port.
- DNS resolution failure.
- Destination service not listening.
- Network policy or firewall rule blocking traffic.
- Dependency outage.

## Remediation
Correct invalid endpoint configuration, restore the destination service, or escalate policy changes through the appropriate infrastructure process. Do not disable security controls as a troubleshooting shortcut.

## Validation
Repeat DNS and TCP checks, run the dependency health request, and confirm the application no longer reports connectivity errors.
