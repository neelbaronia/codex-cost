// Append-only Standard API pricing ledger, USD per million tokens.
// A new price is a NEW row for the exact model ID, never an edit to an old row.
// effectiveFrom is inclusive UTC; the next row's effectiveFrom is exclusive.
// A date-only announcement is represented by midnight UTC, not a claimed exact
// rollout instant. checkedAt records verification, NOT when a price changed.
// See ../../PRICING-HISTORY.md before changing this ledger.
var PRICING_CHECKED_AT = "2026-09-22";
var PRICING_SOURCE_URL = "https://developers.openai.com/api/docs/pricing";
var LONG_CONTEXT_THRESHOLD = 272e3;
function pricing(model, inputPerMillion, cachedInputPerMillion, outputPerMillion, extras = {}) {
  return Object.freeze({
    model,
    // The original bundle recorded an observation date, not an effective date.
    // Preserve it as a baseline; earlier usage is explicitly provisional.
    effectiveFrom: "2026-09-08T00:00:00.000Z",
    effectiveDateBasis: "observed",
    allowEarlierEstimate: true,
    inputPerMillion,
    cachedInputPerMillion,
    outputPerMillion,
    source: PRICING_SOURCE_URL,
    checkedAt: "2026-09-22",
    ...extras
  });
}
var longContext = (inputPerMillion, cachedInputPerMillion, outputPerMillion, cacheWritePerMillion) => Object.freeze({
  thresholdInputTokens: LONG_CONTEXT_THRESHOLD,
  inputPerMillion,
  cachedInputPerMillion,
  outputPerMillion,
  ...cacheWritePerMillion === void 0 ? {} : { cacheWritePerMillion }
});
var MODEL_PRICING = Object.freeze([
  pricing("gpt-6-astra", 10, 1, 50, {
    cacheWritePerMillion: 12.5,
    longContext: longContext(20, 2, 75, 25)
  }),
  // September 22 release: exact public model IDs and Standard API rates.
  // Above 272K input tokens, the long-context rates apply to the full request.
  pricing("gpt-6-sol", 2, 0.2, 10, {
    effectiveFrom: "2026-09-22T00:00:00.000Z",
    effectiveDateBasis: "published-date",
    effectiveDateSource: "https://developers.openai.com/api/docs/changelog#september-2026",
    allowEarlierEstimate: false,
    cacheWritePerMillion: 2.5,
    longContext: longContext(4, 0.4, 15, 5)
  }),
  pricing("gpt-6-luna", 0.1, 0.01, 0.5, {
    effectiveFrom: "2026-09-22T00:00:00.000Z",
    effectiveDateBasis: "published-date",
    effectiveDateSource: "https://developers.openai.com/api/docs/changelog#september-2026",
    allowEarlierEstimate: false,
    cacheWritePerMillion: 0.125,
    longContext: longContext(0.2, 0.02, 0.75, 0.25)
  }),
  pricing("gpt-5.6-sol", 4, 0.4, 20, {
    cacheWritePerMillion: 5,
    longContext: longContext(8, 0.8, 30, 10),
    note: "Promotional API pricing is available at least through November 21, 2026. Recheck before relying on later estimates."
  }),
  pricing("gpt-5.6-terra", 2, 0.2, 12, {
    cacheWritePerMillion: 2.5,
    longContext: longContext(4, 0.4, 18, 5)
  }),
  pricing("gpt-5.6-luna", 0.2, 0.02, 1.2, {
    cacheWritePerMillion: 0.25,
    longContext: longContext(0.4, 0.04, 1.8, 0.5)
  }),
  pricing("gpt-5.5", 5, 0.5, 30, {
    longContext: longContext(10, 1, 45)
  }),
  pricing("gpt-5.4", 2.5, 0.25, 15, {
    longContext: longContext(5, 0.5, 22.5)
  }),
  pricing("gpt-5.4-mini", 0.75, 0.075, 4.5),
  pricing("gpt-5.4-nano", 0.2, 0.02, 1.25),
  pricing("gpt-5.3-codex", 1.75, 0.175, 14),
  pricing("gpt-5.2-codex", 1.75, 0.175, 14, {
    source: "https://developers.openai.com/api/docs/models/gpt-5.2-codex"
  }),
  pricing("gpt-5.1-codex", 1.25, 0.125, 10, {
    source: "https://developers.openai.com/api/docs/models/gpt-5.1-codex"
  }),
  pricing("gpt-5.2", 1.75, 0.175, 14),
  pricing("gpt-5.1", 1.25, 0.125, 10),
  pricing("gpt-5", 1.25, 0.125, 10),
  pricing("gpt-5-mini", 0.25, 0.025, 2),
  pricing("gpt-5-nano", 0.05, 5e-3, 0.4)
]);

function canonicalTimestamp(value) {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value) &&
    Number.isFinite(Date.parse(value)) && new Date(value).toISOString() === value;
}
function validateRates(rates) {
  for (const key of ["inputPerMillion", "cachedInputPerMillion", "outputPerMillion"]) {
    if (!Number.isFinite(rates[key]) || rates[key] < 0) throw new Error("Invalid pricing rate: " + key);
  }
  if (rates.cacheWritePerMillion !== undefined && (!Number.isFinite(rates.cacheWritePerMillion) || rates.cacheWritePerMillion < 0)) throw new Error("Invalid cache-write price.");
}
// Only models already in the September 8 bundle may retain the legacy fallback.
// A newly added model must supply its own verified release/price date.
const legacyBaselineModels = new Set([
  "gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
  "gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano",
  "gpt-5.3-codex", "gpt-5.2-codex", "gpt-5.1-codex",
  "gpt-5.2", "gpt-5.1", "gpt-5", "gpt-5-mini", "gpt-5-nano"
]);
const pricingByModel = new Map();
for (const row of MODEL_PRICING) {
  if (!row.model || !canonicalTimestamp(row.effectiveFrom) || !/^\d{4}-\d{2}-\d{2}$/.test(row.checkedAt) || !canonicalTimestamp(row.checkedAt + "T00:00:00.000Z") || !row.source?.startsWith("https://")) throw new Error("Invalid pricing history metadata.");
  validateRates(row);
  if (row.longContext) {
    validateRates(row.longContext);
    if (!Number.isSafeInteger(row.longContext.thresholdInputTokens) || row.longContext.thresholdInputTokens < 0) throw new Error("Invalid long-context threshold.");
  }
  const history = pricingByModel.get(row.model) ?? [];
  if (history.length && row.effectiveFrom <= history.at(-1).effectiveFrom) throw new Error("Pricing history must be strictly chronological per model: " + row.model);
  if (row.effectiveDateBasis === "observed") {
    if (history.length || !row.allowEarlierEstimate || !legacyBaselineModels.has(row.model) || row.effectiveFrom !== "2026-09-08T00:00:00.000Z") throw new Error("Only the original pricing baseline may use an unverified effective date.");
  } else if (!["published-date", "published-timestamp"].includes(row.effectiveDateBasis) || !row.effectiveDateSource?.startsWith("https://") || row.allowEarlierEstimate) {
    throw new Error("New pricing versions require an official effective-date source.");
  }
  history.push(row);
  pricingByModel.set(row.model, history);
}
function getModelPricing(model, at) {
  // Missing/invalid event times must not silently become today's price.
  if (!canonicalTimestamp(at)) return undefined;
  const history = pricingByModel.get(model);
  return history?.findLast((row) => row.effectiveFrom <= at) ??
    (history?.[0]?.allowEarlierEstimate ? history[0] : undefined);
}
function provisionalPricing(row, at) {
  return !!row && row.allowEarlierEstimate && at < row.effectiveFrom;
}
function pricingPeriod(row) {
  const history = pricingByModel.get(row.model);
  return { ...row, effectiveTo: history[history.indexOf(row) + 1]?.effectiveFrom ?? null };
}
export { MODEL_PRICING, PRICING_CHECKED_AT, getModelPricing, provisionalPricing, pricingPeriod };
