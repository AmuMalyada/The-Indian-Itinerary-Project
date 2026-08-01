# Paper Trail Deployment and Runtime Status

## Scope

This document captures the current deployment state of the Paper Trail n8n
automation in this repository and the release steps for GitHub delivery.

## Project Overview

Paper Trail is a modular workflow automation for ingesting research papers,
extracting and validating structured signals, storing them in PostgreSQL,
detecting contradictions, generating consensus summaries, and sending
notifications.

The implementation follows a strict orchestration rule:
- Only the master workflow orchestrates child workflows.
- Child workflows do not orchestrate other child workflows.

## Architecture

### Orchestration Pattern

- Master workflow: `Paper Trail - Master Pipeline`
- Child workflows are invoked via Execute Workflow nodes.
- PostgreSQL is used for persistent storage and analytics tables.
- OpenAI model calls are used in extraction/analysis stages.
- External data retrieval is handled through HTTP Request nodes.

### Workflow Descriptions

1. `Paper Trail - Master Pipeline`
- Orchestrates end-to-end execution order.
- Triggers setup, ingestion, extraction, validation, storage,
  contradiction detection, consensus, and notifications.

2. `Paper Trail - Database Setup`
- Ensures required database structures/columns are available before run.

3. `Paper Trail - Ingestion`
- Pulls source records and performs dedup checks before downstream stages.

4. `Paper Trail - Extraction`
- Extracts structured fields from raw paper inputs with model assistance.

5. `Paper Trail - Validation`
- Applies validation logic for required fields and data readiness.

6. `Paper Trail - Storage`
- Writes validated records into PostgreSQL tables.

7. `Paper Trail - Contradiction Detection`
- Reads stored paper records and inserts contradiction events/findings.

8. `Paper Trail - Consensus Engine`
- Produces consensus outputs and upserts summary-level insights.

9. `Paper Trail - Notifications`
- Sends status notifications through a configured webhook endpoint.

## Technologies Used

- n8n Cloud (workflow orchestration)
- PostgreSQL (Neon)
- OpenAI API (LLM-backed extraction/analysis)
- HTTP-based source integrations (e.g., Semantic Scholar)
- GitHub (versioning and deployment tracking)

## Setup Instructions

1. Import all workflow JSON files from `workflows/` into n8n Cloud.
2. Verify each workflow imports with expected node names and links intact.
3. Configure credentials and environment variables listed below.
4. Publish child workflows first, then publish master workflow.
5. Execute only the master workflow for end-to-end testing.

## Environment Variables Required

- `PAPER_TRAIL_NOTIFICATION_WEBHOOK_URL`
  - Purpose: destination for notification payloads.
  - Example (non-secret): `https://webhook.site/<id>`

## Database Setup

PostgreSQL backend should be configured through a dedicated n8n credential.

Expected connection shape:
- Host: Neon PostgreSQL host
- Port: `5432`
- Database: project database name
- Username: project DB user
- SSL mode: `Require`

The database setup workflow must run successfully before ingestion/storage
stages to ensure required schema components exist.

## Credentials Required (Do Not Commit Secrets)

1. PostgreSQL credential in n8n
- Suggested name: `Paper Trail PostgreSQL`
- Contains host/user/password/database/ssl settings.

2. OpenAI credential in n8n
- Used by extraction/analysis nodes.

3. Optional webhook/integration credentials
- Only if your notification endpoint requires authenticated delivery.

## Deployment Process

1. Verify repository and branch context.
2. Confirm git identity for release authoring.
3. Review changed files and ensure no secrets are staged.
4. Stage only project-related files.
5. Commit with release-specific message.
6. Push to existing remote and current branch.

## Major Bugs Encountered

1. Missing Postgres credentials in workflow nodes
- Symptom: publish warnings and configuration issues on Postgres nodes.
- Fix: bind `Paper Trail PostgreSQL` on all Postgres nodes and republish.

2. Contradiction workflow publish block (`Store Contradictions`)
- Symptom: publish error reporting missing required `postgres` credential.
- Fix: reopen node, rebind credential, save node/workflow, republish.

3. Master runtime error at `Call Database Setup`
- Symptom: `Cannot convert undefined or null to object`.
- Cause: stale Execute Workflow input mapping (`defineBelow` + null mapping).
- Fix applied: reselect child workflow target in node configuration to
  refresh mapping metadata.

## Master Pipeline Milestone

- Milestone achieved: modular master-driven architecture was fully wired,
  child orchestration boundaries were enforced, and core workflows were
  published with required credentials and environment variable configuration.
- Master pipeline execution completed successfully after workflow input mapping
  refresh on `Call Database Setup` and credential rebinding across child flows.

## Remaining Work

1. Add post-run evidence (run IDs, screenshots, and logs) to release notes.
2. Add automated health checks for workflow credential presence.
3. Add retry/error-routing hardening for intermittent n8n Cloud UI/runtime
   interruptions.
4. Optionally add local Docker-based n8n dev environment runbook.
