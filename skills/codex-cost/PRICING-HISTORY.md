# Dated API-equivalent pricing

The ledger in `scripts/chunks/pricing-history.mjs` is append-only. Each exact
model ID can have multiple complete price versions. A usage event selects the
last version whose `effectiveFrom` is no later than its normalized UTC timestamp.
The next version ends the preceding interval, exclusively. Price requests before
aggregating them into dates, models, sessions, repositories, or cumulative charts.

## Updating a price

1. Fetch official OpenAI pricing and an official announcement of the effective
   date. Record source links. The date a check runs (`checkedAt`) is not the date
   a price changed (`effectiveFrom`). Do not infer a price change from a promotion
   guaranteed to last *at least* until a date.
2. Append a `pricing(...)` row for the exact model ID, in chronological order for
   that model. Preserve every old row and its metadata. Include `effectiveFrom`
   as canonical UTC (`YYYY-MM-DDTHH:mm:ss.sssZ`), `effectiveDateBasis` as
   `published-timestamp` or `published-date`, `effectiveDateSource`, the new
   `checkedAt`, and `allowEarlierEstimate: false`. A date-only announcement uses
   midnight UTC and explicitly does not claim an exact rollout instant.
3. Supply the complete input, cached input, cache-write, output, and long-context
   rates. Long-context thresholds belong to each version. For a new threshold,
   supply an explicit `longContext` object; never change the shared historical
   helper or its 272,000-token constant to update older rows. Do not omit a
   required cache-write price or invent aliases. Zero is a valid *verified* rate.
4. Advance `PRICING_CHECKED_AT` for the ledger check without changing earlier
   rows' `checkedAt` fields. If the effective date is not verified, report the
   gap instead of inserting a guessed boundary. The legacy observed baseline
   is the only exception, not a template for future changes.
5. Run both `review/check-model-pricing.py` and `review/check-pricing-history.py`
   from the repository. Extend independently calculated expected costs for the
   changed model and append new versions to the regression snapshot without
   editing existing versions. Check the installed copy with `--runner` too.

## Historical coverage and uncertainty

The original bundle only retained rates observed on September 8, 2026, not their
historical effective dates. Those baseline rates remain available for older usage
as explicitly **provisional** estimates. This preserves existing estimates
without claiming that the old prices have been reconstructed. The September 22
GPT-6 Sol/Luna release has a published effective date and no pre-release fallback.

`provisionalPricingTokens` and `provisionalApiCost` identify the provisional subset
of the estimated totals. Dashboard headers and reports warn when that subset is
present. Missing event timestamps, unknown models, and dates with no applicable
version remain unpriced, never silently charged at today's rate. Unpriced zero
costs are sentinels, not free usage. `pricingKnown` is false for a model with any
unpriced usage in the selected range; it does not certify the provisional subset.

JSON includes `pricingMethod: "usage-time"`, the entire `pricingHistory`, and
`pricingPeriods` with the actual applied rates, boundaries, sources, usage dates,
and subtotals. Provisional usage is a separate period subtotal. These totals feed
every chart and reporting range, including full all-time history.

Exact request input counts and timestamps are retained in the numerical cache.
The first run after upgrading automatically rebuilds older cache metadata; session
logs are never changed. Subsequent price updates reuse numerical metadata and
select the appropriate dated version. Missing request context uses short rates;
cumulative-only usage is attributed to its event time. If a cumulative delta spans
a rate change, its exact split cannot be reconstructed without request timestamps.

This remains a Standard API-equivalent estimate, not a Codex invoice. Other
processing tiers, regional premiums, tools, media, taxes, and negotiated rates
are outside the estimate. Historical baseline corrections require explicit
evidence and review, not an automatic overwrite.
