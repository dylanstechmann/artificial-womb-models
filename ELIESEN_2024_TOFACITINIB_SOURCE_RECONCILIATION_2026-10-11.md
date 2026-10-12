# Eliesen et al. 2024 Table S3 source reconciliation

Cycle 243 adds a bounded, repeatable check of the candidate observation CSV against the pinned publisher DOCX. The audit selects the third of the three document tables by its Tofacitinib headers and reconciles every time/series cell to its CSV row, including the stated units, compartment, source locator, source lexeme, numeric value, and missingness status.

All 70 cells reconcile: 69 literal numeric values match and the no-placenta control's `N/A` at 1 minute remains `not_assessed` with no numeric value. Table S3 stores the values as literal DOCX text; there is no spreadsheet formula or cached-value layer to audit. The automated check does not complete human transcription/source review, and the candidate remains pending that review.

The check establishes transcription integrity only. The paper and supplement still do not provide numerical per-run reservoir-volume histories, sampling/removal records, or individual recovery totals, so the concentration rows remain ineligible for amount, mass-balance, net-flux, or dimensional transport fitting. They are term ex-vivo placental-transfer observations, not embryo-development or gestation outcomes. No author contact was made.

See the [audit receipt](artifacts/perfusion-intake-2026-10-10/eliesen-table-s3-source-reconciliation-cycle243.json), [candidate manifest](config/perfusion_observations/eliesen_2024_tofacitinib_dataset.json), and [validator](src/wombmodels/eliesen_source.py).
