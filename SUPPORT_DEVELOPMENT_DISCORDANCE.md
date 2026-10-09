# Require support function and embryonic progression together

AI-assisted source audit and design inference, 2026-10-09. Human scientific
review pending. This contains offline source qualification and functional
requirements. It supplies no embryo procedure, tissue manipulation, culture
condition, physiological setting, device assembly or clinical recommendation.
Complete human embryo-to-birth support remains unestablished.

The [material handoff requirements](MATERIAL_HANDOFF_REQUIREMENTS.md) qualify
usable transfer within support tissue. A second requirement is **developmental
coordination between support tissue and the embryo proper**. A successful
component assay cannot close that requirement.

## Source scope and what changes the design question

[Jin et al., Communications Biology (2026)](https://doi.org/10.1038/s42003-026-10656-4)
is a peer-reviewed accepted, unedited article in press. Selected Results,
Discussion, captions, selection metadata and data availability were inspected
through a [rendered primary manuscript copy](https://www.researchgate.net/publication/409415402_Ex_utero_3D_culture_system_illuminates_post-implantation_development_and_functions_of_the_mouse_yolk_sac).
The DOI/title/acceptance banner match; original full-manuscript bytes and copy
revision integrity remain unqualified. Publisher landing HTML and source data
were retrieved separately. The landing-page hash does not pin the full text.

The source reports mouse E3.5 entry, delayed early development, abnormal
gastrulation and embryo-proper arrest. Yolk-sac development and selected
functional readouts persist. D10 yolk-sac resemblance to an E8.5 reference is not
an E13.5 embryo endpoint. Expanded tissue was selected and pooled for profiles;
starting-cohort representation and individual assay pairing remain unqualified.
Relevant locators are Results' platform/scRNA-seq sections, Discussion's divergent
development paragraph, and the sampling-selection note.

| Readout category | Inspected evidence | Requirement still open |
| --- | --- | --- |
| Direct component assays | Tracer uptake; medium proteins; colony-forming potential | Recipient-organ receipt, useful flux and durable function |
| Compartment/identity proxies | Lysosomal staining/localization | Actual substrate-to-product processing |
| Expression-based function labels | Coagulation/barrier transcripts; predicted interactions | Selective exclusion, clotting competence and specific causal signaling |
| Embryonic progression | Adverse morphology and arrest narrative | Incidence, onset and linked support measurements |

These source findings motivate the design inference that component function and
embryo progression must be qualified jointly. They do not demonstrate that every
necessary support function was adequate, that the same embryos had both assay
results, or that patterning was the sole cause of arrest. The authors' missing-
spatial-constraint explanation remains a hypothesis.

## Read-only source-data audit

The [pinned source inventory](config/source_inventories/jin_yolk_sac_2026.json)
records a publisher workbook with four sheets: Figure 2, Figure 4, Figure 5 and
Figure 6. The selected sheets contain no Figure 1 starting roster or selected
uptake/colony quantitative panels. That workbook audit alone does not establish
that such data are absent elsewhere. The selected PDF follow-up below qualifies
additional aggregate cohort and replication metadata.

`audit-yolk-sac-source` retains **310 numeric source cells across 31 Figure 5
time rows**, including source scalar columns, reported means and SDs. It checks
124 mean/sample-SD calculations using the three scalar columns for each source
group/time row. All checks match within the stated arithmetic tolerance. This
is arithmetic consistency, not validated biological n or assay validity.

The audit preserves unresolved source issues:

- No physical concentration units in the selected table; units are not guessed.
- `NC`/`WEC` are original group labels; the NC definition and background handling
  remain unqualified. No subtraction is performed.
- Source table/caption `APOA` and Results `APOA1` need analyte-specificity review.
- Three scalar columns do not establish independent units or repeated measures
  of the same specimens over time.
- VEGFA text names D2/D6. Strict adjacent interior maxima of the unmodified WEC
  reported mean column occur at D1/D5: `Figure 5!A35/J35` and `A39/J39`.
  Both representations are retained; no labels are repaired. Concentration
  maxima are not independently identified secretion events.

Without quantity units, calibration, volume/renewal accounting, source-unit
hierarchy and recipient measurements, these cells cannot support an absolute
material balance or transport fit. The command exports an audit rather than a
numeric observation dataset. It never executes source formulas or edits the
workbook.

```powershell
python -m wombmodels audit-yolk-sac-source --workbook artifacts/jin-yolk-sac-2026-10-09/supplementary-data-5.xlsx --out artifacts/jin-yolk-sac-audit-NEW
python -m wombmodels verify-bundle --bundle artifacts/jin-yolk-sac-audit-NEW --strict
```

Run with the package installed or `src` on the import path and a new output
directory. The pinned external workbook is required for a rerun, not copied
into the bundle. Its original bytes remain unchanged. The receipt pins source
transcription/outputs; byte integrity and scientific review are separate.

The [candidate observation intake](config/observations/jin_2026_yolk_sac_candidate.json)
has 12 qualitative source findings and one missing paired recipient/later-function
requirement. Molecular proxies stay `molecular_identity`; embryo defects stay
`adverse_effect`. Biological identities remain null, scalar concentrations are
excluded, and continuity stays `not_reported`.

```powershell
python -m wombmodels validate-observations --dataset config/observations/jin_2026_yolk_sac_candidate.json --source-root . --out artifacts/jin-yolk-sac-intake-NEW
```

The intake's local source check can verify workbook bytes, while rendered
manuscript bytes remain unpinned. Reported source percentages of yolk-sac
formation are not used as embryo-progression success rates.

## Freeze the narrower feasibility question

**Question:** in a source-qualified starting cohort, does a unit retain the
specified support function while embryonic patterning/progression fails?

| Candidate explanation | Discriminating source observations | What would leave it unresolved |
| --- | --- | --- |
| Support capacity or onward delivery is insufficient | Same-unit support inventory/output and actual recipient receipt around failure onset | Favorable component assays in selected, different or destructive samples |
| Patterning/tissue coordination fails despite specified support function | Same-unit structure, spatial relationships and progression, with receipt/function retained | Marker presence or a suggested missing constraint without a qualified comparative outcome |
| Apparent discordance reflects selection or stage mismatch | Starting roster, exclusions, failed units, actual stage/time and sample branches | Comparing selected D10 tissue profiles with an unlinked whole-cohort arrest narrative |

These are observation/data requirements, not proposed procedures. Multiple
explanations can coexist. At present the sources provide **descriptive
discordance**, not an estimated frequency or identified cause.

The acceptance condition for a narrow empirical analysis is a source-reviewed
unit map spanning the relevant observations, including failures and missing
outcomes. If only unlinked summaries or unknown column identities are available,
retain a descriptive source-discrepancy result and do not fit a favored model.

Machine A's research requirement is now joint: preserve usable exchange **and**
developmentally appropriate tissue coordination. Neither requirement substitutes
for the other. Machine B must preserve their separate trajectories, sampling
branches and adverse endpoints, rather than reporting support-component function
as organism-level success. No specific external input, physical constraint or
control action follows from this source audit.

The [moving-boundary qualification](DYNAMIC_BOUNDARY_REQUIREMENTS.md) now recovers
aggregate screen counts from Supplementary Table 1, post-QC cell totals from
Table 2, and the Reporting Summary's definition of a biological replicate as
a new blastocyst-batch experiment. These selected publisher PDFs are hashed and
visually inspected. The global definition does not authenticate Figure 5 scalar
columns or cross-assay pairing. The selected table gives aggregate endpoints,
without individual identities or a link to the main eight-experiment summary.
The inventory preserves this narrower qualification; the 13-record intake now
declares both pinned supplements as supporting artifacts.

Next qualification: reconcile Figure 5 timing/units and recover individual
starting/outcome records plus cross-assay specimen hierarchy. CRA024449 retrieval
failed; its file/sample inventory remains unqualified. A separate mouse
implantation study adds comparative boundary/growth evidence, without diagnosing
arrest here. Even fully resolving these source issues would not establish human
continuous gestation or healthy lifelong outcomes.
