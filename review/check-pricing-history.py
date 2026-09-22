#!/usr/bin/env python3
"""Verify dated pricing through the shipped launcher, using only temporary data."""

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--runner", type=Path, default=ROOT / "skills/codex-cost/scripts/run.sh")
args = parser.parse_args()
MODEL = "synthetic-dated-model"

# These rates and dates are intentionally fictional. Never install this ledger.
OLD = '''
  pricing("synthetic-dated-model", 10, 1, 20, {
    effectiveFrom: "2026-08-01T00:00:00.000Z",
    effectiveDateBasis: "published-timestamp",
    effectiveDateSource: "https://example.invalid/synthetic-old-rate",
    allowEarlierEstimate: false,
    cacheWritePerMillion: 12.5,
    longContext: { thresholdInputTokens: 100, inputPerMillion: 20, cachedInputPerMillion: 2, cacheWritePerMillion: 25, outputPerMillion: 30 }
  })'''
NEW = '''
  pricing("synthetic-dated-model", 2, 0.2, 10, {
    effectiveFrom: "2026-09-21T12:00:00.000Z",
    effectiveDateBasis: "published-timestamp",
    effectiveDateSource: "https://example.invalid/synthetic-new-rate",
    allowEarlierEstimate: false,
    cacheWritePerMillion: 2.5,
    longContext: { thresholdInputTokens: 200, inputPerMillion: 4, cachedInputPerMillion: 0.4, cacheWritePerMillion: 5, outputPerMillion: 15 }
  })'''
FUTURE = NEW.replace("2026-09-21T12:00:00.000Z", "2030-01-01T00:00:00.000Z").replace(
    '"synthetic-dated-model", 2, 0.2, 10', '"synthetic-dated-model", 1, 0.1, 5')


def close(actual, expected):
    assert math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12), (actual, expected)


def event(kind, at, payload):
    return {"timestamp": at, "type": kind, "payload": payload}


def raw(input_tokens, cached=0, writes=0, output=0):
    return dict(input_tokens=input_tokens, cached_input_tokens=cached,
                cache_write_input_tokens=writes, output_tokens=output)


with tempfile.TemporaryDirectory(prefix="codex-cost-history-") as tmp:
    root = Path(tmp)
    # Mutate only an isolated copy; never expose test prices in the live skill.
    scripts = root / "scripts"
    shutil.copytree(args.runner.resolve().parent, scripts)
    ledger = scripts / "chunks/pricing-history.mjs"
    original = ledger.read_text()
    marker = "]);\n\nfunction canonicalTimestamp"
    assert original.count(marker) == 1

    def versions(*rows):
        ledger.write_text(original.replace(marker, ",\n" + ",\n".join(rows) + "\n" + marker))

    fixture = root / "history"
    (fixture / "sessions").mkdir(parents=True)
    (fixture / "archived_sessions").mkdir()
    cache = root / "cache"
    records = [event("session_meta", "2026-08-22T12:00:00Z", {
        "id": "dated", "timestamp": "2026-08-22T12:00:00Z", "cwd": "/synthetic/dated-project"}),
        event("turn_context", "2026-08-22T12:00:00Z", {"model": MODEL})]
    # Identical ten-token requests must keep different costs around the boundary.
    requests = [
        ("2026-08-22T12:00:00Z", raw(10)),
        ("2026-09-21T11:59:59.999Z", raw(10)),
        ("2026-09-21T12:00:00Z", raw(10)),
        ("2026-09-21T04:00:00-08:00", raw(10)),
        ("2026-09-21T11:59:59.998Z", raw(150, 20, 30, 10)),
        ("2026-09-21T12:01:00Z", raw(150, 20, 30, 10)),
        ("2026-09-21T12:02:00Z", raw(201, 20, 30, 10)),
        (None, raw(10)),
        ("2026-07-31T23:59:59Z", raw(10)),
    ]
    for i, (at, usage) in enumerate(requests):
        records.append(event("token_usage_record", at, {
            "thread_id": "dated", "response_id": f"r{i}", "usage": usage}))
    records.append(records[4])  # Duplicate response at the new-price boundary.
    (fixture / "sessions/dated.jsonl").write_text("\n".join(map(json.dumps, records)) + "\n")
    legacy = [event("session_meta", "2026-09-20T12:00:00Z", {
        "id": "legacy", "timestamp": "2026-09-20T12:00:00Z", "cwd": "/synthetic/dated-project"}),
        event("turn_context", "2026-09-20T12:00:00Z", {"model": MODEL})]
    for count, at in [(10, "2026-09-20T12:00:00Z"), (20, "2026-09-21T12:00:00Z")]:
        legacy.append(event("event_msg", at, {"type": "token_count", "info": {
            "total_token_usage": raw(count), "last_token_usage": raw(10)}}))
    (fixture / "archived_sessions/legacy.jsonl").write_text("\n".join(map(json.dumps, legacy)) + "\n")

    def report(*extra, success=True):
        result = subprocess.run(
            ["/bin/sh", str(scripts / "run.sh"), "--json", "--range", "all",
             "--data-dir", str(fixture), *extra], capture_output=True, text=True,
            env={**os.environ, "CODEX_COST_CACHE_DIR": str(cache)})
        if not success:
            assert result.returncode != 0 and not result.stdout, result
            assert "pricing" in result.stderr.lower() or "price" in result.stderr.lower(), result.stderr
            return
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def day(data, date):
        return next(d for d in data["daily"] if d["date"] == date)

    def verify(data):
        assert data["pricingMethod"] == "usage-time"
        assert data["totalTokens"] == 611
        assert data["pricedTokens"] == 591
        assert data["unpricedTokens"] == 20
        assert data["provisionalPricingTokens"] == 0
        close(data["estimatedApiCost"], 0.004741)
        close(day(data, "2026-08-22")["estimatedApiCost"], 0.0001)
        close(day(data, "2026-09-20")["estimatedApiCost"], 0.0001)
        close(day(data, "2026-09-21")["estimatedApiCost"], 0.004541)
        periods = sorted(data["pricingPeriods"], key=lambda p: p["effectiveFrom"])
        assert len(periods) == 2
        close(periods[0]["estimatedApiCost"], 0.00339)
        close(periods[1]["estimatedApiCost"], 0.001351)
        assert periods[0]["effectiveTo"] == periods[1]["effectiveFrom"]
        assert periods[0]["usageTo"] == "2026-09-21T11:59:59.999Z"
        assert periods[1]["usageFrom"] == "2026-09-21T12:00:00.000Z"
        assert data["models"][0]["pricingKnown"] is False  # Partial date coverage.
        assert any("lack a valid usage timestamp" in w for w in data["diagnostics"]["warnings"])
        for key in ["daily", "models", "projects", "sessionDetails", "pricingPeriods"]:
            close(sum(item["estimatedApiCost"] for item in data[key]), data["estimatedApiCost"])
            assert sum(item["totalTokens"] for item in data[key]) == (591 if key == "pricingPeriods" else 611)

    versions(OLD)
    before = report()
    versions(OLD, NEW)
    after = report()
    verify(after)
    assert after["diagnostics"]["cachedFiles"] == 2
    # Adding a new price must never change earlier usage, even with a warm cache.
    for date in ["2026-08-22", "2026-09-20"]:
        close(day(before, date)["estimatedApiCost"], day(after, date)["estimatedApiCost"])
    verify(report("--rescan"))
    versions(OLD, NEW, FUTURE)
    future = report()
    verify(future)
    close(future["estimatedApiCost"], after["estimatedApiCost"])
    assert len([p for p in future["pricingHistory"] if p["model"] == MODEL]) == 3

    # A previous cache schema must rebuild automatically, without manual cleanup.
    with sqlite3.connect(cache / "usage.sqlite") as db:
        db.execute("UPDATE files SET version = 3")
    migrated = report()
    verify(migrated)
    assert migrated["diagnostics"]["cachedFiles"] == 0

    # Reject invalid ledgers instead of guessing at a price.
    for rows in [(OLD, NEW, NEW), (NEW, OLD), ('pricing("new-undated-model", 1, 0.1, 2)',),
                 (OLD, NEW.replace("2026-09-21T12:00:00.000Z", "2026-02-30T12:00:00.000Z")),
                 (OLD, NEW.replace('"synthetic-dated-model", 2, 0.2, 10', '"synthetic-dated-model", -2, 0.2, 10')),
                 (OLD, NEW.replace('effectiveDateBasis: "published-timestamp"', 'effectiveDateBasis: "observed"'))]:
        versions(*rows)
        report(success=False)

    # Exercise all six real chart renderers and all T-key reporting ranges,
    # without opening a window or sending keystrokes to the user's Terminal.
    versions(OLD, NEW)
    inspector = scripts / "chunks/chunk-6A4INWEF.mjs"
    inspector.write_text(inspector.read_text() + "\nexport { createInspectorData, renderInspector };\n")
    (scripts / "codex-cost.mjs").write_text(r'''
import assert from "node:assert/strict";
import { getAnalytics } from "./chunks/service-SIMU6ROX.mjs";
import { createInspectorData, renderInspector } from "./chunks/chunk-6A4INWEF.mjs";
let frames = 0;
for (const days of [undefined, 90, 30, 7, 1]) {
  const analytics = await getAnalytics({ days });
  const data = createInspectorData(analytics);
  if (days) assert.equal(data.days.length, days);
  if (!days && process.env.EXPECT_OLD_HISTORY) assert.ok(data.days.length > 90);
  for (const width of [40, 80, 160]) for (const page of [0, 1, 2, 3, 4, 5]) for (const color of [false, true]) {
    const frame = renderInspector(data, { width, height: 40, page, color, ascii: true, metric: "cost", motion: false });
    const lines = [...frame.header, ...frame.body];
    const text = lines.join("\n");
    assert.ok(text.includes("DATED PRICING"));
    assert.ok(!text.includes("NaN") && !text.includes("undefined"));
    if (analytics.totals.provisionalPricingTokens) assert.ok(text.includes("provisional"));
    for (const line of frame.header) assert.ok(line.replace(/\x1b\[[0-9;]*m/g, "").length <= width);
    const cumulative = data.cumulative.at(-1)?.estimatedApiCost ?? 0;
    assert.ok(Math.abs(cumulative - analytics.totals.estimatedApiCost) < 1e-10);
    frames++;
  }
}
console.log(JSON.stringify({ frames }));
''')
    for fixture_name in ["main", "gpt6"]:
        result = subprocess.run(
            ["/bin/sh", str(scripts / "run.sh")], capture_output=True, text=True,
            env={**os.environ, "CODEX_COST_CACHE_DIR": str(cache),
                 "CODEX_COST_DATA_DIR": str(ROOT / "review/fixtures" / fixture_name),
                 "EXPECT_OLD_HISTORY": "1" if fixture_name == "main" else ""})
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["frames"] == 180

print("PASS: historical rates, ten-token examples, exact/offset/mid-day boundaries, dated long-context thresholds, cached/write/output prices, legacy records, missing timestamps, all aggregates, future prices, warm-cache updates, schema migration, invalid ledgers, 360 chart frames and all time ranges.")
