# Roelofsen ex-vivo Papp: surface-area assumption lineage

Source review, 2026-10-10. This is a provenance and uncertainty note, not a
biological observation dataset or a placental operating specification. No
authors were contacted.

## What the 11.8 m² / 35-cotyledon scaling represents

Roelofsen et al. state that the critical assumption in scaling ex-vivo
cotyledon apparent permeability (`Papp`) is cotyledon surface area. They use a
reported average whole-placenta villous surface area of 11.8 m² and divide by
an average of 35 cotyledons per term placenta. The authors explicitly warn that this
average can over- or underestimate the cotyledons used in their experiments.
They say surface-area uncertainty could be handled with uncertainty analysis
or worst-case scenarios. No microscopic surface-area measurement is reported
for each perfused cotyledon.

## Apparent 100-fold area-unit discrepancy

The publisher's Methods state that the assumed area in the ex-vivo `Papp`
equation is `3371 dm²` per perfused cotyledon. In the Discussion, the same
paper says the term-placenta value is `11.8 m²`, divided by an average of 35
cotyledons. That calculation gives approximately `0.337 m²`, or `33.7 dm²`,
or `3371 cm²` per cotyledon. Thus the Methods' printed `3371 dm²` is 100 times
the area implied by the stated division; the value is consistent with cm².
The article's Table 1 reports the resulting ex-vivo `Papp` in cm/s.

This is an apparent internal unit mismatch, not enough evidence to correct the
published values. The supplement gives detail for the BeWo calculation, while
the article says ex-vivo `Papp` is calculated similarly; the inspected files do
not expose a calculation workbook or per-run inputs that identify the physical
area actually used. Because `Papp = (ΔQ/Δt)/(A C₀)`, it scales inversely with
area when the other terms are fixed. If `3371 dm²` rather than the implied
`3371 cm²` was actually used as the physical area, the area term would be 100
times larger and `Papp` 100 times smaller. It remains unknown whether the
printed unit is a typo or the calculation used the larger physical area. No
published `Papp` has been corrected, rescaled, or reclassified here. Quantitative
use requires reconciliation of the unit and the area value used in the
calculation.

## What the 100× sensitivity does and does not establish

This factor is a deterministic unit conversion: for the same numeric area,
`1 dm² = 100 cm²`, so `3371 dm²` is exactly 100 times `3371 cm²`. Under the
first interpretation, the Methods' unit is a typographic error and the
Discussion-implied area was used; the published `Papp` and ratio cells stay as
reported (scale factor 1). Under the second, the printed `3371 dm²` was used
and the Discussion-implied area is the intended value; replacing it would
multiply ex-vivo `Papp` and its ex-vivo/BeWo ratios by 100. The source record
does not identify which branch occurred. These are conditional bookkeeping
cases, not probabilities, a confidence interval, or an empirical range for
cotyledon area. No per-perfusion area or definition-matched area distribution
is available to bound the biological quantity more broadly.

This ambiguity is material to the paper's cross-model result. Table 1 reports
two ex-vivo/BeWo `Papp` ratio rows: about 0.34–0.54 for BeWo compounds tested
in a mixture and 0.31–0.75 for those tested separately. If the larger physical
area was used and the intended area is 100 times smaller, the ex-vivo values
and ratios would conditionally scale by 100, giving 34–54 and 31–75,
respectively. This would reverse the quantitative comparison between the
systems. It is a conditional sensitivity calculation from published ratios,
not evidence that the area was misapplied or that the published values should
be changed.

The exact source-reported ratio rows, in Table 1 compound-column order
(antipyrine, amoxicillin, thalidomide uncorrected, thalidomide corrected,
valproic acid), are `0.35, 0.54, 0.47, 0.34, 0.50` for the mixture comparison
and `0.34, 0.55, 0.45, 0.31, 0.75` for the separate-compound comparison. Their
100× conditional counterparts are recorded cell-by-cell in the [ratio source-cell
inventory](config/source_inventories/roelofsen_table1_papp_ratio_source_cells.csv).
The inventory preserves the table's ratios as printed instead of recomputing
them from rounded mean cells; hypothetical scaling remains separate from the
published values. For audit, it separately stores the arithmetic ratios of the
displayed rounded means and their differences from the printed ratio cells.
These are not identical for every compound (for example, the mixture
amoxicillin values give 0.54 as printed versus about 0.524 from displayed
means). The source does not provide unrounded means, run-level values or the
fold-difference calculation details, so this is retained as a rounding/method
qualification rather than a claim of error. Conditional sensitivity uses the
source-reported ratio cells only.

| Intake claim | Source or calculation | Evidence status |
| --- | --- | --- |
| The Methods state `A = 3371 dm²`. | [Publisher Methods, ex-vivo `Papp` equation](https://doi.org/10.1007/s00204-026-04418-8) | Source-reported wording; preserve as printed. |
| The Discussion derives per-cotyledon area from `11.8 m² / 35`. | [Publisher Discussion, area-scaling paragraph](https://doi.org/10.1007/s00204-026-04418-8) | Source-reported scaling assumption; not per-perfusion morphometry. |
| The stated division is about `0.337 m² = 33.7 dm² = 3371 cm²`. | Arithmetic conversion of the two Discussion inputs | Derived audit value; not a new biological observation. |
| `Papp` is inversely proportional to area in the published equation. | `P = (ΔQ/Δt)/(A C₀)` | Algebraic consequence, holding the other terms fixed. |
| Table 1 reports two ex-vivo/BeWo ratio rows, `0.34–0.54` and `0.31–0.75`. | [Publisher Table 1](https://doi.org/10.1007/s00204-026-04418-8) | Source-reported rounded comparison values. |
| Which physical area entered each reported ex-vivo calculation? | No calculation file or run-linked source inputs located | Unresolved; do not correct or rescale the published `Papp`. |
| The larger area was used and should be replaced with the smaller one. | Conditional 100× scenario applied to the Table 1 ratios | Unverified scenario only; not an observation or correction. |

The [aggregate `Papp` source-cell inventory](config/source_inventories/roelofsen_table1_papp_aggregate_source_cells.csv)
preserves the fifteen mean±SD cells, and the [ratio inventory](config/source_inventories/roelofsen_table1_papp_ratio_source_cells.csv)
preserves the ten printed fold-difference cells. Both are generated from the
pinned full-text XML by the [offline extractor](artifacts/transport-collection-2026-10-09/extract_roelofsen_table1_papp.py).

## Public-record check

A bounded publisher/PubMed title- and DOI-search and targeted institutional-
repository/data-record searches on 2026-10-10 did not surface a correction
notice or a separate ex-vivo `Papp` calculation dataset. The publisher lists
the inspected supplementary DOCX, which describes methods and supplies
processed figures/native tables, but it does not identify the physical area
used for each reported ex-vivo value. This is a search boundary, not proof that
no private or later record exists. No author was contacted.

## Repository intake boundary

The current [Roelofsen candidate intake](src/wombmodels/roelofsen_intake.py)
emits source-linked S9/S10 percentage-of-initial-dose cells, not the Table 1
`Papp` summaries. The abstract [transport identifiability diagnostic](src/wombmodels/transport_identifiability.py)
also states that no published `Papp` value is used as a model parameter. A
repository search found no Roelofsen `Papp` records in the observation or model
configuration paths. The unit discrepancy is therefore not currently feeding
the executable model; any later `Papp` intake must carry this unresolved area
qualification before parameter use.

For traceability, a separate [Table 1 aggregate source-cell inventory](config/source_inventories/roelofsen_table1_papp_aggregate_source_cells.csv)
now preserves all 15 published `Papp` mean±SD cells across the ex-vivo and
BeWo rows. Its [offline extractor](artifacts/transport-collection-2026-10-09/extract_roelofsen_table1_papp.py)
reads the pinned [Europe PMC full-text XML](artifacts/transport-collection-2026-10-09/roelofsen-fulltext-xml.xml)
and records the exact cell text, parsed mean and SD, source locator, assay time,
mixture/separate condition, and the Table 1 caption's assay-family `N`. The
caption does not specify a compound-cell denominator or provide run identities,
so the repeated `N` is retained as caption-level context only. Ex-vivo rows
carry the unresolved area qualification; no value or ratio is corrected or
rescaled. This descriptive inventory stays outside the developmental
observation dataset and executable model inputs.

The same extractor creates a separate [ten-cell comparison-ratio inventory](config/source_inventories/roelofsen_table1_papp_ratio_source_cells.csv).
It retains the two printed ratio rows verbatim and stores their conditional
100× values in a distinct field. These source ratios are not recalculated from
the displayed rounded Papp means; the conditional values are not source
observations.

A post-intake code-reference audit found no reference to either new CSV or a
generic loader for `config/source_inventories` in `src/wombmodels`. The model
entry points read explicitly supplied JSON configurations. Thus adding these
source inventories did not create an automatic route into simulations; this
is a repository wiring check, not a scientific validation of the summaries.

The source lineage is:

1. [Dallmann et al. (2017)](https://doi.org/10.1007/s40262-017-0539-z)
   provide the whole-placenta villous-area basis. Their publisher supplement,
   Table 1 and Figure 25, describes a gestation-dependent mean and standard
   deviation fitted by weighted least squares to published villous-area
   measurements. The listed studies are literature observations, not
   histometry on the Roelofsen perfusions. The supplement says `x` denotes
   fertilization age but omits a numerical unit. A later PBPK methods paper by
   Dallmann and colleagues describes the model's maximum fertilization age as
   38 weeks ([Dallmann et al. 2018](https://doi.org/10.1002/psp4.12300)). This
   supports interpreting `x` in weeks, although it does not amend the omitted
   label in the 2017 supplement. Evaluating the published fits at `x = 38`
   gives a model mean of about 11.81 m² and fitted SD of about 2.16 m², which
   rounds to the 11.8 m² value used by Roelofsen. This is a consistency check
   on the model lineage, not a new observation or an area distribution for
   perfused cotyledons.
2. [Mian et al. (2021)](https://doi.org/10.3389/fped.2021.733520) state that
   the total fetal-villus area in a term placenta is approximately
   1178 dm² (citing Dallmann) and divide it by an average of about 35
   cotyledons at term (citing Polin et al., *Fetal and Neonatal Physiology*,
   2011). This is a model-scaling step, not a measurement of an individual
   cotyledon in the Roelofsen study. The 1178 dm² numerator is consistent by
   unit conversion with the rounded 11.8 m² value, so Mian is not an
   independent validation of that numerator.
3. Roelofsen et al. apply the average area to their ex-vivo `Papp` calculation
   and acknowledge the possible individual-cotyledon mismatch.
4. [Barker et al. (2013)](https://doi.org/10.1016/j.placenta.2013.04.019)
   counted visible maternal-surface cotyledons from photographs of formalin-
   stored placentas in one hospital cohort and reported a range of 3–37. This
   is a gross anatomical count, not a microscopic villous-area measurement or
   a count linked to the Roelofsen perfusions. It shows that cotyledon count is
   variable and definition-sensitive; it cannot be substituted as a numerical
   prior for the model's average of 35 without a matched counting definition
   and population.

The Dallmann supplement's villous-area functions are:

```text
mean area μ(x) = 20.3 exp(-8.03 exp(-0.0710 x)) - 0.00659 m²
SD area σ(x)   = 2.24 / (1 + 64.9 exp(-0.210 x)) - 0.0339 m²
```

The mean fit can be evaluated on a week-based fertilization-age axis for a
bounded whole-placenta area sensitivity analysis, subject to applicability
review. The fitted SD summarizes the literature-data model; it is not an area
distribution measured on the cotyledons in these perfusions. The cotyledon-count assumption has its
own uncertainty and must not be treated as known exactly merely because 35 is
used as an average. Barker et al.'s visible-count cohort is evidence of
variation, but it does not quantify the distribution appropriate to the
perfused cotyledons.

## Implication for intake and qualification

Keep the reported `Papp` as an assumption-dependent aggregate result. Do not
promote it to donor-specific conductance or whole-placenta capacity. The area
uncertainty can be tested separately from the unavailable per-run concentration,
volume/removal, and donor-linkage information; it cannot repair those missing
records. A later sensitivity analysis should identify the age convention,
distribution represented by the fitted SD, cotyledon-count uncertainty, and
the surface definition used by the perfusion calculation before using the
literature fit.

The row in the [mass-balance field matrix](config/source_inventories/roelofsen_mass_balance_field_matrix.csv)
and the [qualification card](ROELOFSEN_DATA_REQUIREMENTS.md) preserve this
distinction. No area values or calculations have been added to biological
observations. This note's unit conversion audits the published assumption; it
is not a replacement area observation or corrected `Papp` value.

## Source links

- [Roelofsen et al. (2026), primary study and supplementary material](https://doi.org/10.1007/s00204-026-04418-8)
- [Roelofsen et al. (2026), PubMed record](https://pubmed.ncbi.nlm.nih.gov/42050187/)
- [Dallmann et al. (2017), article](https://doi.org/10.1007/s40262-017-0539-z)
- [Dallmann et al. (2017), publisher supplementary PDF](https://media.springernature.com/original/springer-static/esm/art%3A10.1007%2Fs40262-017-0539-z/MediaObjects/40262_2017_539_MOESM1_ESM.pdf)
- [Mian et al. (2021), full text](https://doi.org/10.3389/fped.2021.733520)
- [Barker et al. (2013), cotyledon-count cohort](https://doi.org/10.1016/j.placenta.2013.04.019)
