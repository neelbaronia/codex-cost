#!/usr/bin/env python3
"""Check cumulative Activity geometry without opening a user's Terminal."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--runner", type=Path, default=ROOT / "skills/codex-cost/scripts/run.sh")
args = parser.parse_args()

with tempfile.TemporaryDirectory(prefix="codex-cost-cumulative-") as tmp:
    scripts = Path(tmp) / "scripts"
    shutil.copytree(args.runner.resolve().parent, scripts)
    inspector = scripts / "chunks/chunk-6A4INWEF.mjs"
    inspector.write_text(inspector.read_text() + "\nexport { createActivityCurves, activityCurves, createInspectorData, renderInspector, plot, geometryCache };\n")
    (scripts / "codex-cost.mjs").write_text(r'''
import assert from "node:assert/strict";
import { getAnalytics } from "./chunks/service-SIMU6ROX.mjs";
import { createActivityCurves, activityCurves, createInspectorData, renderInspector, plot, geometryCache } from "./chunks/chunk-6A4INWEF.mjs";
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-10, `${a} != ${b}`);
const model = (model, totalTokens, estimatedApiCost) => ({ model, totalTokens, estimatedApiCost });
const daily = [
  [model("a", 10, 1), model("c", 2, 0.2), model("unknown", 5, 0)],
  [model("b", 20, 2), model("unknown", 3, 0)],
  [],
  [model("a", 7, 0.7), model("c", 1, 0.1)],
  [model("d", 6, 0.6), model("e", 4, 0.4), model("f", 3, 0.3), model("g", 1, 0.1)]
].map((models, i) => ({ date: `2026-01-0${i + 1}`, models }));
const original = JSON.stringify(daily);
const tokenCurves = createActivityCurves(daily, "tokens");
const sums = (curves) => daily.map((_, i) => curves.series.reduce((sum, curve) => sum + curve.values[i], 0));
assert.deepEqual(sums(tokenCurves), [17, 40, 40, 48, 62]);
assert.deepEqual(tokenCurves.series.find(s => s.model === "a").values, [10, 10, 10, 17, 17]);
assert.deepEqual(tokenCurves.series.find(s => s.model === "b").values, [0, 20, 20, 20, 20]);
// A shared scale uses the largest individual curve, not the sum of all curves.
assert.equal(tokenCurves.maximum, 20);
assert.equal(tokenCurves.total, 62);
// Narrowed periods must start fresh, not inherit the all-time running total.
const narrowed = createActivityCurves(daily.slice(3), "tokens");
assert.equal(narrowed.total, 22);
assert.deepEqual(narrowed.series.find(s => s.model === "a").values, [7, 7]);
assert.equal(tokenCurves.series.length, 6);
assert.equal(tokenCurves.series.at(-1).count, 3);
assert.equal(tokenCurves.series.at(-1).total, 7);
assert.notEqual(tokenCurves.series[0].values, tokenCurves.series[1].values);
const costCurves = createActivityCurves(daily, "cost");
sums(costCurves).forEach((value, i) => close(value, [1.2, 3.2, 3.2, 4, 5.4][i]));
assert.ok(!costCurves.series.some(s => s.model === "unknown"));
assert.equal(createActivityCurves([], "tokens").maximum, 0);
assert.deepEqual(createActivityCurves([daily[2]], "tokens").series, []);
assert.equal(JSON.stringify(daily), original);

function verifyCurves(days, metric) {
  const field = metric === "cost" ? "estimatedApiCost" : "totalTokens";
  const curves = createActivityCurves(days, metric);
  const final = days.reduce((sum, day) => sum + day.models.reduce((n, m) => n + m[field], 0), 0);
  close(curves.total, final);
  close(curves.maximum, Math.max(0, ...curves.series.map(s => s.total)));
  for (const [i, date] of days.entries()) {
    const included = days.slice(0, i + 1);
    for (const series of curves.series) {
      const expected = included.reduce((sum, day) => sum + day.models.filter(m => series.model ? m.model === series.model : !curves.series.some(s => s.model === m.model)).reduce((n, m) => n + m[field], 0), 0);
      close(series.values[i], expected);
      if (i) assert.ok(series.values[i] >= series.values[i - 1]);
    }
  }
  curves.series.forEach(series => close(series.values.at(-1), series.total));
}
for (const metric of ["tokens", "cost"]) verifyCurves(daily, metric);

const strip = s => s.replace(/\x1b\[[0-9;]*m/g, "");
const synthetic = { days: daily, curves: costCurves.series, modelColors: new Map() };
for (const ascii of [true, false]) {
  const options = { ascii, color: false, metric: "tokens", motion: { elapsedMs: 1000, reveal: 1 } };
  const rendered = plot(synthetic, options, 80, 12, tokenCurves);
  assert.ok(rendered[0].trimStart().startsWith("20"));
  assert.ok(rendered.some(line => line.includes("A 20")));
  assert.ok(rendered.some(line => line.includes("B 17")));
  assert.ok(!rendered.join("\n").includes("$"));
  const { grid, paths } = geometryCache(synthetic).activityPlot.geometry;
  const columns = grid[0].length;
  // Model A is b: it starts at zero and ends at its own 20-token ceiling.
  assert.equal(Math.floor(paths[0][0] / columns), 11);
  assert.equal(Math.floor(paths[0].at(-1) / columns), 0);
  // Model B starts at 10, halfway up the same scale, not on top of model A.
  assert.ok([5, 6].includes(Math.floor(paths[1][0] / columns)));
  assert.ok(grid.flat().filter(cell => cell.bits || cell.char !== " ").length < grid.flat().length / 2);
  const costPlot = plot(synthetic, { ...options, metric: "cost" }, 80, 12, costCurves).join("\n");
  assert.ok(costPlot.includes("$2"));
  // The cost page and the two Activity metrics cannot share stale geometry.
  const before = plot(synthetic, options, 80, 12).join("\n");
  plot(synthetic, options, 80, 12, tokenCurves);
  assert.equal(plot(synthetic, options, 80, 12).join("\n"), before);
  assert.equal(plot(synthetic, options, 80, 12, tokenCurves).join("\n"), rendered.join("\n"));
  for (const days of [[], [daily[2]], [daily[0]]]) {
    const single = createActivityCurves(days, "tokens");
    const output = plot({ ...synthetic, days }, { ...options, motion: false }, 40, 4, single).join("\n");
    assert.ok(!output.includes("NaN") && !output.includes("undefined"));
    if (days[0]?.models.length) assert.ok(output.includes("A 10"));
  }
}
let frames = 0;
for (const days of [undefined, 90, 30, 7, 1]) {
  const analytics = await getAnalytics({ days });
  const data = createInspectorData(analytics);
  const originalDaily = JSON.stringify(analytics.daily);
  if (days) assert.equal(data.days.length, days);
  else assert.ok(data.days.length > 90);
  for (const metric of ["tokens", "cost"]) for (const width of [40, 80, 160]) {
    verifyCurves(data.days, metric);
    const expected = metric === "cost" ? analytics.totals.estimatedApiCost : analytics.totals.totalTokens;
    // Exercise the geometry cache while toggling metrics and motion.
    for (const motion of [false, { elapsedMs: 1000, reveal: 1 }]) for (const ascii of [true, false]) for (const color of [true, false]) {
      const curves = activityCurves(data, { metric, motion });
      close(curves.total, expected);
      close(curves.maximum, Math.max(0, ...curves.series.map(s => s.total)));
      const frame = renderInspector(data, { width, height: 40, page: 0, metric, motion, ascii, color });
      const output = [...frame.header, ...frame.body].join("\n");
      assert.ok([...frame.header, ...frame.body].every(line => strip(line).length <= width));
      assert.ok(output.includes("Cumulative"));
      assert.ok(!output.includes("NaN") && !output.includes("undefined"));
      assert.ok(!output.includes("MODEL BANDS") && !output.includes("top edge"));
      if (metric === "cost" && analytics.totals.unpricedTokens) assert.ok(output.includes("partial estimate"));
      frames++;
    }
    if (metric === "cost") close(data.cumulative.at(-1)?.estimatedApiCost ?? 0, expected);
  }
  assert.equal(JSON.stringify(analytics.daily), originalDaily);
}
console.log(JSON.stringify({ frames }));
''')
    result = subprocess.run(
        ["/bin/sh", str(scripts / "run.sh")], capture_output=True, text=True,
        env={**os.environ, "CODEX_COST_CACHE_DIR": str(Path(tmp) / "cache"),
             "CODEX_COST_DATA_DIR": str(ROOT / "review/fixtures/main")})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["frames"] == 240

print("PASS: unstacked cumulative model curves, shared zero baseline, individual scales/endpoints, token/cost labels, Other models, unknown prices, empty/single-day history, all ranges, 240 frames, separate motion caches and unchanged daily data.")
