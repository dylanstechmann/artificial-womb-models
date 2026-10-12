# Bukkems 2022 doravirine perfusion source screen — 2026-10-10

## Purpose and result

Screen whether Bukkems et al.'s article and supplements expose individual ex vivo perfusion records linking concentration trajectories to numeric volume/removal histories and per-run recovery. The source adds aggregate concentration and mass-balance evidence, including an explicit statement that sampling loss was corrected. It does not publish the individual rows required for a source-exact, run-level accounting join, so no observation table or dimensional fit is added.

## Sources inspected

- Bukkems et al., *Prediction of maternal and fetal doravirine exposure by integrating physiologically based pharmacokinetic modeling and human placenta perfusion experiments*, [PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9349081/) ([publisher article](https://link.springer.com/article/10.1007/s40262-022-01127-0); DOI 10.1007/s40262-022-01127-0).
- Publisher [ESM1 PDF](https://static-content.springer.com/esm/art%3A10.1007%2Fs40262-022-01127-0/MediaObjects/40262_2022_1127_MOESM1_ESM.pdf), pinned locally as `artifacts/perfusion-intake-2026-10-10/bukkems_2022_doravirine_ESM1.pdf`, SHA-256 `b44e63c7a43fe476ce5841a2452ab867f0b78718e514362641ea7745f8fe8b12`.
- Publisher [ESM2 PDF](https://static-content.springer.com/esm/art%3A10.1007%2Fs40262-022-01127-0/MediaObjects/40262_2022_1127_MOESM2_ESM.pdf), pinned locally as `artifacts/perfusion-intake-2026-10-10/bukkems_2022_doravirine_ESM2.pdf`, SHA-256 `8684a03dc0f6dd2dfcdcabf9464af743c8af611218f41113806b6e84b5580ae5`.

## Findings

The article reports human term-cotyledon closed–closed perfusions in both transfer directions (four perfusions per direction), with samples over 180 minutes. Its main concentration figure is reported as mean ± SD. The paper reports overall doravirine recovery of 46% for maternal-to-fetal perfusion and 53% for fetal-to-maternal perfusion, not individual run totals.

ESM1 Online Resource 6 says its mass-balance calculations use measured maternal and fetal buffer concentrations at each timepoint and correct for perfusion-medium volume lost to sampling. The figure is a summary graphic; neither it nor the other inspected supplement pages publish the underlying per-run concentration rows, numeric time-resolved reservoir volumes, sample-removal amounts, or individual recovery totals. ESM1 Online Resource 5 is an end-point tissue summary for eight placentas (mean ± SD). ESM2 Online Resource 15 shows closed–open perfusion summaries for six placentas (three per direction; mean ± SD), not a run-level table.

The article says the data are stored at Radboud University Medical Center and may be available upon request. No author was contacted. The paper concerns term placental drug transfer and model predictions; it does not assess embryo development, continuous gestation, birth, or later health.

## Intake decision

Retain the article as an aggregate accounting-method comparator. Do not digitize figures into pseudo-individual rows or treat aggregate recovery as per-run mass balance. A useful next public-source addition must include linked individual concentrations, numeric compartment volumes and sample removals, and per-run recovery or enough source values to reproduce them.
