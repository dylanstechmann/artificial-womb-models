# Usuda terminal source-audit reproduction — Cycle 347

## Decision question

Do the source-pinned terminal group summaries that motivate keeping organ and bone development separate from body mass reproduce exactly from the checked-in extractor, and does the parser reject a malformed published-summary cell? This is a narrow data-pipeline check; it cannot choose a support architecture.

## Result

The Cycle 346 command was rerun into a fresh, exclusive output directory using the pinned [Europe PMC JATS source](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10484719/fullTextXML). The source SHA-256 was `553bb25875e95db787249c60bab779dc05aebb32f341dce27b3f1c7405430e0a`. The extractor implementation SHA-256 was `4ec359b18bcc5caa433d715ce6ae61652adb595834943474349fd78b11c33b16` in both receipts.

Both the original and replay bundles passed strict receipt verification. All six source-derived outputs were byte-for-byte identical:

| Output | Bytes | SHA-256 |
| --- | ---: | --- |
| `REPORT.md` | 3,335 | `b8217ee073033fd68528ac0e61754fc2eb19611b3ba14bac35ac4715961f6ef1` |
| `endpoint_cells.csv` | 8,895 | `46af0f56e766eb862214040c7cc5e4ad47b50b6478e8a8555999f1dcf040ac49` |
| `input_dataset.json` | 240,546 | `dc17e4094cf312ceaa2c6e5f0a0f34444ae81431125dc3680cd5e072f7b28049` |
| `input_source_manifest.json` | 328 | `6f2626f17513a6c91c3b54c2a525f589efe6bd1fa8cd6792adb1969d5778aeec` |
| `qualification.json` | 1,684 | `d13e42ec1583e569351d2e894829ddc4e98e95a6fcceb4cbe2f27bc017e876c1` |
| `reported_mean_comparisons.csv` | 2,265 | `adc60e413442fc752f6d23951cd0fb629346762513151640b6f88333a787aa9f` |

The reproduction plan and enclosing receipt differ as expected: the original bundle records Python 3.11.2 and the replay records Python 3.11.15. The source-derived tables and report are unchanged. A malformed summary literal, `NaN ± 1`, was rejected with `Unsupported published summary syntax`.

The replay output is at `artifacts/usuda-terminal-development-cycle346/rerun-cycle347/`; its receipt SHA-256 is `ad117a405d52ae852e360589c0f6de871f9eba1b5b7ac41b5672d38b82d0daf2`. The original receipt SHA-256 is `cb12de0ed8dc9c52e5c309b3d946f7f37ba0cbc6600c1cd80afe7937c404a0dd`.

## Decision consequence and limits

The currently used extraction and arithmetic for the nine published terminal morphology means are reproducible from the pinned article bytes under the recorded implementation. This supports retaining the reported organ/bone endpoints alongside body mass as distinct descriptive observations. It does not establish individual-level effects, developmental causality, external-support efficacy, or an architecture choice. The source still has zero reported individual IDs and no measurement pairs or transitions; its control-count discrepancy, different necropsy ages, edema qualification, and source-review status remain unchanged. No scientific review was performed and no author was contacted. No biological gate moves.

Strict bundle verification establishes receipt/file integrity, while this separate CLI rerun establishes output reproducibility for this source and software version. Neither establishes source transcription correctness or biological validity.
