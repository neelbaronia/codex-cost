#!/usr/bin/env python3
"""Exercise the shipped launcher against synthetic logs, without personal history."""

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--runner", type=Path, default=ROOT / "skills/codex-cost/scripts/run.sh")
args = parser.parse_args()


def close(actual, expected):
    assert math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12), (actual, expected)


def report(fixture, cache, *extra):
    result = subprocess.run(
        ["/bin/sh", str(args.runner), "--json", "--range", "all", "--data-dir",
         str(ROOT / "review/fixtures" / fixture), *extra],
        env={**os.environ, "CODEX_COST_CACHE_DIR": str(cache)},
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def verify_release(data):
    assert data["pricingCheckedAt"] == "2026-09-22"
    assert data["pricingMethod"] == "usage-time"
    assert data["provisionalPricingTokens"] == 0
    close(data["provisionalApiCost"], 0)
    # Existing ledger entries are immutable; future versions may only add rows.
    preserved = json.loads((ROOT / "review/fixtures/pricing-history-baseline.json").read_text())
    history = [{k: v for k, v in row.items() if k != "effectiveTo"} for row in data["pricingHistory"]]
    for row in preserved:
        assert row in history, f"Historical pricing version was changed or removed: {row['model']} {row['effectiveFrom']}"
    assert data["sessions"] == 7
    assert data["totalTokens"] == 1412202
    assert data["pricedTokens"] == 1130202
    assert data["unpricedTokens"] == 282000
    close(data["estimatedApiCost"], 1.6328802)
    models = {entry["model"]: entry for entry in data["models"]}
    # Requests at 272,000 use short rates; 272,001 uses long rates for every
    # token, including cache writes. Legacy counts add one small short request.
    for model, expected in [("gpt-6-sol", 1.555124), ("gpt-6-luna", 0.0777562)]:
        item = models[model]
        assert item["pricingKnown"] is True
        assert item["inputTokens"] == 400401
        assert item["cachedInputTokens"] == 144600
        assert item["outputTokens"] == 20100
        assert item["totalTokens"] == 565101
        assert item["unpricedTokens"] == 0
        assert item["sessions"] == 3
        close(item["estimatedApiCost"], expected)
    # An undocumented suffix must not inherit a published model's price.
    unknown = models["gpt-6-sol-unverified"]
    assert unknown["pricingKnown"] is False
    assert unknown["unpricedTokens"] == 282000
    assert unknown["estimatedApiCost"] == 0
    assert data["diagnostics"]["warnings"] == []


with tempfile.TemporaryDirectory(prefix="codex-cost-pricing-") as tmp:
    cache = Path(tmp) / "cache"
    # Cover cold parsing, cached numerical metadata, and explicit rescanning.
    for extra, cached in [((), 0), ((), 7), (("--rescan",), 0)]:
        data = report("gpt6", cache, *extra)
        verify_release(data)
        assert data["diagnostics"]["cachedFiles"] == cached

    # The previous fixture must retain its original prices and partial coverage.
    old = report("main", cache)
    assert old["sessions"] == 3
    assert old["totalTokens"] == 2420
    assert old["pricedTokens"] == 2200
    assert old["unpricedTokens"] == 220
    close(old["estimatedApiCost"], 0.0058625)
    assert old["provisionalPricingTokens"] == 2200
    close(old["provisionalApiCost"], 0.0058625)
    assert any("provisional pre-baseline" in note for note in old["diagnostics"]["warnings"])
    assert old["daily"][0]["date"] == "2026-01-05"
    assert len(old["daily"]) > 90

    # Presentation must disclose provisional history without losing any charts.
    for bucket in ["day", "week", "month"]:
        rendered = subprocess.run(
            ["/bin/sh", str(args.runner), "--terminal", "--ascii", "--no-color",
             "--width", "80", "--range", "all", "--bucket", bucket, "--data-dir",
             str(ROOT / "review/fixtures/main")],
            env={**os.environ, "CODEX_COST_CACHE_DIR": str(cache)},
            capture_output=True, text=True, check=True,
        ).stdout
        assert "provisional pre-baseline prices" in rendered
        assert "2026-01-05" in rendered
        assert "NaN" not in rendered

print("PASS: GPT-6 Sol/Luna standard, long-context, cache-write, legacy and deduplication accounting; cache reuse; unknown IDs; existing prices and all-time history.")
