# Codex Cost

An animated ASCII dashboard for your local Codex usage: tokens, models, API-equivalent cost, and cost by repository.

This repository contains the complete, ready-to-install Codex skill. Its runtime is bundled, so no npm install, build step, API key, or separate account sign-in is required.

## Install in Codex

Paste this into Codex:

```text
$skill-installer install https://github.com/neelbaronia/codex-cost/tree/main/skills/codex-cost
```

Then invoke:

```text
$codex-cost
```

Codex detects newly installed skills automatically. If the skill does not appear, restart Codex.

## Requirements

- **macOS with Terminal.app** for the skill's automatic dashboard launcher. The animation opens in a new Terminal window.
- **Node.js 22.13 or newer.** The launcher checks Node on PATH and common Homebrew installation paths.
- **Local Codex history** on the machine running the skill.

The launcher may need permission to control Terminal.app. If Codex reports that its sandbox blocks the launch, approve the specific launcher command when prompted.

The bundled reporting engine can also be run directly in a compatible local environment with Node.js 22.13+. Automatic window opening uses macOS-specific scripts.

## Ask for a view

```text
Use $codex-cost to open my animated usage dashboard.
Use $codex-cost to open my last 30 days of usage.
Use $codex-cost to show my last 7 days as static ASCII charts in this conversation.
Use $codex-cost to show my usage as JSON.
```

The six dashboard pages are **Activity**, **Cumulative cost**, **Models**, **Token mix**, **GPT-3 era**, and **Cost by repo**. Every page summarizes the full selected range. Supported ranges are all history, 7 days, 30 days, and 90 days.

| Key | Action |
| --- | --- |
| Left / Right | Switch chart pages |
| `1`–`6` | Jump to a chart |
| Up / Down | Scroll the current page |
| `m` | Switch Activity between tokens and API-equivalent dollars |
| `a` | Toggle ASCII and Unicode/Braille |
| `c` | Toggle color |
| Space | Pause or resume animation |
| `r` | Replay the entrance animation |
| `q` | Quit the dashboard and restore its terminal |

## Data and estimates

The skill reads the recipient's local Codex history and stores a local cache of usage/session metadata. It does not upload history or modify session logs. No usage history is included in this repository.

Dollar amounts are **API-equivalent estimates**, not Codex subscription charges or invoices. Unpriced models stay in token totals and are excluded from dollar estimates. Reasoning is already included in output; cached input is already included in logged input. Reporting periods use UTC. Deleted records, other devices, and server-only usage may be absent.

The GPT-3 era comparison is a pricing thought experiment, not a comparison of equivalent model capabilities.

## Package contents

The installable folder is [`skills/codex-cost`](skills/codex-cost). Keep the whole folder together, including `scripts/chunks/`: the main script imports those bundled modules. [`SKILL.md`](skills/codex-cost/SKILL.md) contains the workflow instructions and supported options; `agents/openai.yaml` supplies the display metadata.

For direct use from a clone of this repository:

```sh
# Open the animated dashboard in a new macOS Terminal window.
/bin/sh skills/codex-cost/scripts/open.sh

# Print a report and exit.
/bin/sh skills/codex-cost/scripts/run.sh --terminal --ascii --no-color --width 80

# Show command-line options without reading usage history.
/bin/sh skills/codex-cost/scripts/run.sh --help
```

## License

[MIT](LICENSE).
