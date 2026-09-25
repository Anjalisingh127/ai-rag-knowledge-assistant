---
document_id: RB-AUTH-FAIL-001
title: Authentication Failure Runbook
document_type: runbook
category: authentication
service: shared
environment: simulated
tags: authentication, 401, credentials, token, secret-rotation
---

# Authentication Failure Runbook

## Triage
1. Determine whether the failure affects users, service accounts, or one service instance.
2. Check response codes and authentication error messages.
3. Review recent secret, certificate, or token configuration changes.
4. Compare working and failing instances.
5. Validate system time when token validity errors appear.

## Common causes
- Expired or incorrectly rotated credentials.
- Missing secret or environment variable.
- Token issuer, audience, or clock-skew mismatch.
- Incorrect service account permissions.

## Remediation
Reload the correct credential, correct token configuration, repair system time, or restore required permissions. Avoid logging full secrets or access tokens.

## Validation
Run a controlled authentication request, verify expected authorization behavior, and confirm errors stop across all affected instances.
