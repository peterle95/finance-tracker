---
type: operations guide
title: Automation and release operations
description: Scheduled OpenWiki updates, CI permissions and credentials, Electron build/package commands, artifacts, and recovery boundaries.
tags: [operations, ci, release]
---

# Automation and release operations

`.github/workflows/openwiki-update.yml` runs manually or daily at `0 8 * * *`. It checks out full history with pinned `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5` (v4), installs Node 22 via pinned `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020` (v4), and installs `openwiki@0.3.3`, `mermaid@11.16.0`, and `jsdom@29.1.1`. It runs `openwiki code --update --print` with provider `openai-chatgpt` and model `gpt-5.6-luna`, then uses pinned `peter-evans/create-pull-request@22a9089034f40e5a961c8808d113e2c98fb63676` (v7) on branch `openwiki/update`, targeting the workflow's default repository base branch. Full history is required so OpenWiki can compare against the last documented commit. It requires `contents: write` and `pull-requests: write`; `OPENWIKI_LANGSMITH_API_KEY` is required for the configured connector and `LANGSMITH_API_KEY` is optional tracing. Treat these as secrets and do not reproduce their values.

The PR action is allowed to modify `openwiki`, `AGENTS.md`, `CLAUDE.md`, and `.github/workflows/openwiki-update.yml`; generated documentation should be reviewed as a normal PR, and missing credentials, shallow history, provider failure, or permission errors require checking secrets/permissions and rerunning manually.

The modern desktop package scripts provide `typecheck`, Vitest, Playwright E2E, `build`, and `package:win`. Electron Builder emits a Windows NSIS installer under `modern-desktop/release/`; build output is `out/`. The narrow validation order is `npm run typecheck`, `npm test`, `npm run build`, then `npm run test:e2e`; package only for release artifacts. CI documentation changes arrive as a PR and can be repaired by rerunning the workflow with full history.
