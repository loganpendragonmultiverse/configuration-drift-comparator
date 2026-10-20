# Changelog

## 1.2.1 - 2026-10-20

- Reject malformed sources, non-finite values, duplicate JSON keys and ambiguous legacy dotted paths.
- Distinguish literal missing-marker strings from absent keys in legacy drift counts.
- Create reports exclusively to preserve existing files during destination races.
- Document and test source safety, typed input and installed distribution acceptance.

## 1.2.0 - 2026-10-15

- Add opt-in recursive JSON Pointer comparison with escaped keys, atomic arrays, explicit missing-source evidence and object/scalar boundary comparisons.
- Preserve legacy dotted-key reports and both peer and designated-baseline comparisons.

## 1.1.0 - 2026-07-27

- Added optional baseline-source comparisons and per-key drift classifications.
- Added missing-key totals by source and consistent/changed/missing summaries.

## 1.0.0 - 2026-07-26

- Released the first complete Configuration Drift Comparator command-line workflow.
- Added deterministic reporting, representative examples, cross-platform tests, and explicit limitations.
