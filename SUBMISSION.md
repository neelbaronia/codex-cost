# Codex Cost — submission packet

## Package

- Submission type: **Skills only**
- Package ID: `codex-cost`
- Version: `0.1.1`
- Display name: **Codex Cost**
- Subtitle: **Codex usage and cost charts**
- Category: **Productivity**
- Website and source: https://github.com/neelbaronia/codex-cost
- Support: https://github.com/neelbaronia/codex-cost/issues
- License: MIT

The publisher in the submission must match the verified individual or organization used in the OpenAI Platform portal. The package currently identifies the GitHub maintainer, `neelbaronia`.

## Description

View token activity, model usage, API-equivalent cost, and cost by repository. The bundled skill reads local Codex history and opens an animated dashboard in a new macOS Terminal window. Requires Node.js 22.13 or newer.

## Starter prompts

1. Open my animated Codex usage dashboard.
2. Show my last 30 days of Codex usage as ASCII charts.
3. Show my Codex API-equivalent cost by repository.

## Reviewer setup

The automatic animation launcher requires macOS, Terminal.app, and Node.js 22.13 or newer. No API key, remote server, paid account, or npm install is needed. macOS may ask for permission to control Terminal.app.

Use the synthetic fixtures and reproduction steps in [review/TEST-CASES.md](review/TEST-CASES.md) to inspect reports without reading personal Codex history. The fixtures contain invented session identifiers, paths, and usage. They are outside the installed skill's automatic history discovery path.

The plugin reads local Codex session logs and stores a local usage cache. It does not upload history or modify session logs. Dollar figures are API-equivalent estimates, not subscription charges or invoices. Unknown models remain in token totals and are excluded from dollar estimates.

## Release notes

Version 0.1.1 adds a square logo and composer icon, a subtitle within directory limits, synthetic reviewer fixtures, and a packaged ZIP. The dashboard runtime and separate Terminal window workflow are unchanged from 0.1.0.

## Directory workflow

Create a **Skills only** plugin at [OpenAI Platform](https://platform.openai.com/plugins) and upload `codex-cost-0.1.1.zip`. Verify the displayed publisher, listing fields, and asset previews before submitting. The account needs Apps Management Write access and a verified publishing identity. Complete any required attestations in the portal, submit for review, then choose Publish after approval.

The ZIP and public GitHub repository do not themselves create a directory listing. OpenAI performs the platform's security scans and review after submission.

References: [Submission guide](https://developers.openai.com/plugins/deploy/submission), [Submission validation](https://developers.openai.com/plugins/deploy/submission-errors).
