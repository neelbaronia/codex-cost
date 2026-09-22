# Codex Cost

An animated ASCII dashboard for your local Codex usage: tokens, models, API-equivalent cost, and cost by repository.

This repository contains a ready-to-install Codex plugin and its standalone skill. The dashboard runtime is bundled, so no npm install, build step, API key, or separate account sign-in is required.

## Install the plugin

[Install Codex Cost from the official plugin directory](https://chatgpt.com/plugins/plugins_6aa57d893fbc8191b415a4321d9ce63c). Version **0.1.2** was published on **2026-09-12**.

You can also install from GitHub by running these commands in your shell:

```sh
codex plugin marketplace add neelbaronia/codex-cost --ref main
codex plugin add codex-cost@codex-cost
```

The first command registers this repository's marketplace; the second installs the plugin. Open a new Codex chat after installation, then ask:

```text
Use Codex Cost to open my animated usage dashboard.
```

You can also select the bundled skill from `/skills` or by typing `$` in Codex. The plugin contains the same skill and dashboard as the standalone installation below, so either installation method is sufficient.

Download the plugin ZIP from [GitHub releases](https://github.com/neelbaronia/codex-cost/releases). The [submission packet](SUBMISSION.md) includes listing copy and reviewer setup; [synthetic test cases](review/TEST-CASES.md) let reviewers inspect usage reports without personal history.

## Install only the skill

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

The six dashboard pages are **Activity**, **Cumulative cost**, **Models**, **Token mix**, **GPT-3 era**, and **Cost by repo**. Every page summarizes the full selected range. Press `t` to cycle through all time, 90 days, 30 days, 1 week, and 1 day.

| Key | Action |
| --- | --- |
| Left / Right | Switch chart pages |
| `1`–`6` | Jump to a chart |
| Up / Down | Scroll the current page |
| `m` | Switch Activity between tokens and API-equivalent dollars |
| `t` | Cycle the selected range: all time, 90d, 30d, 1w, 1d |
| `a` | Toggle ASCII and Unicode/Braille |
| `c` | Toggle color |
| Space | Pause or resume animation |
| `r` | Replay the entrance animation |
| `q` | Quit the dashboard and restore its terminal |

## Data and estimates

The skill reads the recipient's local Codex history and stores a local cache of usage/session metadata. It does not upload history or modify session logs. No usage history is included in this repository.

Dollar amounts are **API-equivalent estimates**, not Codex subscription charges or invoices. Unpriced models stay in token totals and are excluded from dollar estimates. Reasoning is already included in output; cached input is already included in logged input. Reporting periods use UTC. Deleted records, other devices, and server-only usage may be absent.

The GPT-3 era comparison is a pricing thought experiment, not a comparison of equivalent model capabilities.

Costs now use **dated price history**: each usage event uses the applicable rate
before totals are combined into charts. Future price updates append versions and
do not overwrite old prices. Identical token usage before and after a price change
can therefore have different costs. JSON exposes the preserved ledger and applied
period subtotals for auditing.

Older usage predating the original pricing snapshot keeps its previous estimate,
but is clearly marked **provisional** because its historical rate was not verified.
Missing timestamps or unavailable rates remain unpriced. See
[pricing history and update rules](skills/codex-cost/PRICING-HISTORY.md) for exact
boundaries, source provenance, cache behavior, and limitations.

Pricing checked September 22, 2026 includes GPT-6 Sol (`gpt-6-sol`) and GPT-6
Luna (`gpt-6-luna`). Standard rates per million tokens are $2 / $0.20 / $10 for
Sol and $0.10 / $0.01 / $0.50 for Luna (input / cached input / output).
Recorded cache writes and prompts above 272,000 input tokens use their published
rates from [OpenAI API pricing](https://developers.openai.com/api/docs/pricing).
Both models appear in the token and dollar charts with distinct colors. Run
`python3 review/check-model-pricing.py` to verify the bundled rates and accounting
using synthetic history.

Run `python3 review/check-pricing-history.py` for price-change boundary tests,
including warm caches, future versions, long-context thresholds, and preservation
of old rates. Both checks accept `--runner /absolute/path/to/scripts/run.sh`.

## Package contents

The plugin lives at the repository root. [`plugin.json`](plugin.json) declares the portable plugin identity, [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) supplies Codex presentation metadata and compatibility, and [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) makes the plugin installable from this GitHub repository.

The standalone installable folder remains [`skills/codex-cost`](skills/codex-cost). Keep the whole folder together, including `scripts/chunks/`: the main script imports those bundled modules. [`SKILL.md`](skills/codex-cost/SKILL.md) contains the workflow instructions and supported options; `agents/openai.yaml` supplies the skill display metadata.

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
