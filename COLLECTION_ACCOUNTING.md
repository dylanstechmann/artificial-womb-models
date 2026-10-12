# Transport collection accounting and native source recovery

AI-assisted exploration, 2026-10-09; human source and scientific review pending.
This advances evidence intake for a narrow interface question. It does not
qualify a biological transport fit or close a human gestation gate.

The concrete advance is access to native numerical tables embedded inside a
publisher's DOCX supplement. Concentration, fluid inventory, collected analyte,
tissue inventory and conversion remain distinct observables. The new
dimensionless diagnostic explains why these distinctions matter before fitting
the recovered values.

## Primary evidence inspected

[Roelofsen et al., Archives of Toxicology (2026)](https://link.springer.com/article/10.1007/s00204-026-04418-8)
compares ex vivo human placental perfusion with BeWo b30 transfer assays. The
article discusses sampling removal and analyte degradation corrections, which
affect interpretation of disappearance and recovery. The publisher records a
supplementary update on 3 July 2026. These assays do not observe embryonic
development, neonatal transition or a complete gestation.

The current article text gives a cumulative-mass equation that corrects for
analyte removed in earlier samples. This confirms that raw concentration at a
later time is not the corrected transferred amount. The recovered Prism tables
remain percent-of-initial-dose summaries; the inspected files do not link those
percentages to original concentration/volume records or identify which
correction steps produced each plotted row. The equation is therefore a
source-declared method, not a reproducible correction for the recovered values.

[Fournier et al., Advanced Sensor Research (2026)](https://advanced.onlinelibrary.wiley.com/doi/10.1002/adsr.202500166)
provides another collection/transport analysis candidate. Its data statement
offers data on reasonable request. Its supporting attachment could not be
retrieved in this inspection; its contents remain unqualified. No author inquiry
has been sent.

## Recover actual tables, then qualify their meaning

The [Roelofsen supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1007%2Fs00204-026-04418-8/MediaObjects/204_2026_4418_MOESM1_ESM.docx)
contains six native Prism OLE objects. The original percent-of-dose recovery
selects objects 5 and 6 rather than digitizing plotted images. A later bounded
audit of the stability-control objects 2 and 3 is recorded below. Its pinned
input is:

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `roelofsen-supplement-1.docx`, downloaded 2026-10-09 | 779,093 | `ccab1bae3d666024b35e256cf9fb421217fcbba226ea5a294182002ab0a8e108` |

DOCX relationships and adjoining captions identify the objects as
Supplementary Figures S9 and S10. S9 reports circulation percentages over three
hours; S10 reports tissue percentages after 180 minutes per successful
experiment. Both captions declare four biological replicates. This is a source
declaration; native slot-to-donor mapping remains unverified.

| Selected object | Recovered structure | Interpretation retained |
| --- | --- | --- |
| `word/embeddings/oleObject5.bin`, S9 | Four XY tables, each 11 rows and 9 columns: one X column and two sets of four Y slots; 352 Y values | Author-processed percentages of initial dose, with maternal/foetal set titles. Original concentrations and normalization ancestry are not recovered here. |
| `word/embeddings/oleObject6.bin`, S10 | One grouped table, four labeled rows and 25 columns: row label and four sets of six Y slots; 96 Y values | Source labels `Placenta 1`–`Placenta 4` retained. The six slots within each compound do not establish six additional biological donors. |

## Public supplementary object audit — 2026-10-10

The current publisher DOCX was retrieved again on 2026-10-10. It is byte-for-byte
identical to the version pinned above (779,093 bytes; SHA-256
`ccab1bae3d666024b35e256cf9fb421217fcbba226ea5a294182002ab0a8e108`), despite
the article page's updated marker. The additional source worksheets are not a
new revision or an external raw-data repository.

A bounded, read-only extraction of native objects 2 and 3, mapped to
Supplementary Figures S4 and S5, found twelve embedded worksheets. The
[machine-readable inventory](config/source_inventories/roelofsen_auxiliary_table_inventory.csv)
retains worksheet/table IDs, figure and paragraph locators, set labels, shape,
numeric-cell counts, axis titles, unit qualifications and exact CSV hashes.
Exact native CSV bytes are held in the ignored local artifact directory
`artifacts/roelofsen-auxiliary-stability-2026-10-10/`; its `SOURCE.json` pins
the parent DOCX, OLE objects and extracted tables.

Object 2 (S4) contains two 11-row, four-compound series with three source slots
per compound and sheet titles ending in `% of ID`; the x-axis is only titled
`Time`, without a unit. It also contains two thalidomide series labeled
`stability perfusion system` and `degradation in glass vial`. One numeric table
is titled as input to a log transformation, but its y unit is not specified;
its companion worksheet contains transformed values, followed by Prism fit
lines and statistics. Object 3 (S5) contains a 16-row four-compound
`% of ID` transwell-stability series with a native `Time (min)` axis and a
separate log-transformed thalidomide series. Saved regression lines and fit
summaries remain derived outputs and are not observations.

These stability controls help characterize compound disappearance in test
systems, but they are not placenta-transfer concentration histories. The
unlabeled numeric thalidomide series is not assigned a concentration unit;
`% of ID` is not converted to mass. Replicate slots do not establish perfusion
donors or biological-unit linkage. The article does report a 3 mL subtraction
per ex-vivo timepoint, described as two 1.5 mL samples, and fixed BeWo
compartment/sample volumes. The inspected ex-vivo text does not resolve how
that aliquot total maps to each circuit. The files also lack run-linked
concentration histories, actual starting circuit volumes, calibration records
and donor mappings. The [field matrix](config/source_inventories/roelofsen_mass_balance_field_matrix.csv)
separates those method statements from per-run measurements. The separate
[area-source lineage note](ROELOFSEN_SURFACE_AREA_LINEAGE_2026-10-10.md)
traces the area/count inputs and the available literature-fit uncertainty. For the ex-vivo
Papp calculation, the discussion calls cotyledon surface area its critical
scaling assumption: it divides the reported average whole-placenta villous
area (11.8 m²) by an average 35 cotyledons, and warns this can over- or
underestimate the cotyledons tested. No cotyledon-specific microscopic area measurement is
linked to the perfusions, so the published Papp carries structural scaling
uncertainty beyond the missing per-run fluid and concentration histories. No
values from these twelve sheets were added to the observation dataset or fitted.

The Dallmann 2017 supplement labels its independent variable as fertilization
age but omits the numeric unit. A later Dallmann et al. methods paper describes
the model maximum as 38 weeks; evaluating the 2017 mean fit at `x = 38` gives
about 11.81 m² (fitted SD about 2.16 m²), consistent with Roelofsen's rounded
11.8 m². This is a source-lineage check on a whole-placenta literature fit,
not a measurement or uncertainty distribution for the cotyledons perfused.

The Methods print this assumed area as 3371 dm², while the Discussion's
11.8 m² / 35 calculation gives about 0.337 m² = 33.7 dm² = 3371 cm². The
printed unit is therefore 100 times the Discussion-implied area; the value
3371 is consistent with cm². Table 1 reports ex-vivo `Papp` in cm/s. The
supplement and available source tables do not establish which physical area
was used for the reported ex-vivo values. Since `Papp` is inversely
proportional to area, the ambiguity could produce a 100-fold scale difference
if the larger area was actually used. Treat this as an unresolved source
inconsistency: no values have been rescaled. See the [surface-area lineage
note](ROELOFSEN_SURFACE_AREA_LINEAGE_2026-10-10.md).

Source spelling, including `Antipryine`, is retained. Further native metadata
inspection resolved the trajectory unit: each XY table references an X data
set explicitly titled `Time (min)` with the X-axis attribute. Values are retained
in `min` without conversion. The tissue endpoint uses the caption's `180 minutes`
and is recorded separately in `minutes`; it has no native X column. These are
elapsed assay times, separate from donor tissue age and developmental intervals.
Tissue normalization and within-row subcolumn meanings require review.

The reader implements a bounded subset of the
[Microsoft CFB format](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-cfb/68530324-9d3d-4441-9ea9-66a2c8f79567):
regular-sector `CONTENTS` streams in the inspected layout. It checks FAT chains,
size prefixes and nested ZIP inventories, reads JSON metadata and copies CSV
bytes exactly. Changed hashes, unsupported layouts, malformed shapes and
nonfinite numeric tokens fail before publication. The
[Prism format documentation](https://www.graphpad.com/guides/prism/latest/user-guide/prism_file_format.htm)
describes native ZIP/CSV storage. No OLE program, embedded code or saved Prism
analysis is executed.

An independent `olefile` inspection produced exactly the same selected native
ZIP bytes as the standard-library implementation:

| Object | Native ZIP SHA-256 |
| --- | --- |
| 5 | `5deeb4192fd8b36b5322ff4b130c4da205cf651fe7d631e8591b989982b6d7d1` |
| 6 | `82b19348348dc62e9d5902db54177f95c9f7749e6c4bb33acf8f2bddc5c98874` |

The independent inspector is an ignored local helper; the runtime has no
third-party dependency. Recovery publishes selected CSVs, member/table locators,
hash ancestry, a candidate report and receipt. It now also emits a candidate
observation dataset, while establishing no analysis eligibility and executing
no fit. Downloads and recovered source tables remain in
ignored `artifacts/`; no publisher data is committed. The article declares CC BY
4.0; source-specific reuse review remains pending. Outputs attribute the source
and identify unchanged CSV bytes versus new metadata.

## IF-4: what does collection-corrected disappearance identify?

For one tracked analyte and one common window, fluid inventory is
`Q_fluid = C_d V_d + C_r V_r`. The artificial accounting question is:

```text
r = supplied - collected - change_in_fluid_inventory
r = change_in_tissue_inventory + conversion + unrecovered
```

A future biological analysis requires compatible amount units and source-linked
supplied/collected amounts. Concentration alone cannot supply an amount. The
artificial witness class restricts the right-hand terms to nonnegative net
amounts; it represents neither gross turnover nor route/rate.

`collection-accounting` publishes four invented, dimensionless counterexamples:

| Case | Exact observation implication in this fixture |
| --- | --- |
| Collection accounts for disappearance | Correct collection gives residual 0; omission gives 5. An apparent sink need not be tissue accumulation. |
| Concentration rises while volume falls | Receiver concentration doubles while its inventory stays equal. Relative concentration change is not a delivery fraction. |
| Positive residual without tissue observation | Residual 4 admits allocations `(4,0,0)`, `(0,4,0)` and `(0,0,4)` to tissue/conversion/unrecovered with identical aggregate observations. |
| Independent tissue observation added | Tissue change 1.5 leaves 2.5 assignable either to conversion or unrecovered analyte. Tissue information reduces ambiguity without resolving both terms. |

The first constraint has matrix `[1,1,1]` and nullspace directions `[1,-1,0]`
and `[1,0,-1]`. Adding independently observed tissue inventory gives a second row
`[1,0,0]` and leaves `[0,1,-1]` unobserved. This aggregate algebra does not
identify a dynamic model or guarantee practical identifiability for biological
measurements.

A negative remainder is retained as incompatible with this restricted class;
the tool does not diagnose injury, assay error or an omitted process. At a
nonnegative boundary, one feasible partition may remain without establishing
general structural identifiability or absence of gross turnover. Missing tissue
information differs from measured zero. A zero receiver baseline leaves relative
concentration change unavailable.

Products and balances use exact rational arithmetic for validated binary-float
inputs, preserving a small change against a large common inventory. Exported
decimals are rounded representations. Strict fields, input bounds and a 50-case
cap bound the diagnostic. No biological source value becomes calibration.

## Reproduce and check the outputs

With the package installed, provide the pinned input and new destinations:

```powershell
wombmodels audit-roelofsen-source --supplement artifacts/transport-collection-2026-10-09/roelofsen-supplement-1.docx --out artifacts/roelofsen-native-recovery
wombmodels validate-observations --dataset artifacts/roelofsen-native-recovery/input_dataset.json --source-root artifacts/transport-collection-2026-10-09 --out artifacts/roelofsen-native-intake
wombmodels collection-accounting --config examples/collection_accounting_fixture.json --out artifacts/collection-accounting
wombmodels verify-bundle --bundle artifacts/roelofsen-native-recovery --strict
wombmodels verify-bundle --bundle artifacts/roelofsen-native-intake --strict
wombmodels verify-bundle --bundle artifacts/collection-accounting --strict
```

The bundles include implementation/input/output hashes and reproduction plans;
receipts publish last. Verification checks bytes, not scientific eligibility or
source review. Existing destinations are rejected.

## Next qualification target

The [native-data qualification card](ROELOFSEN_DATA_REQUIREMENTS.md) distinguishes
source tracing from paired transport fitting and starting-cohort success
estimation. `native_cells.csv` preserves 448 Y-cell locators, exact numeric
lexemes, set IDs/titles, source row labels and slot positions. `input_dataset.json`
retains reported quantities/times, null biological-unit identities, unreported
replicate roles and no continuity edges. `qualification.json` explicitly retains
unknown starting/excluded attempts. Structural validation and source-byte
verification do not authenticate biological identity or human review.

Review table/caption mapping, exact quantities and correction ancestry.
Authenticate the donor/experiment/replicate mapping between maternal and foetal
trajectories, across compounds and to tissue endpoints; column order alone is
insufficient. Preserve unsuccessful experiments, exclusions and technical
subsamples separately from biological units.

Then determine whether original concentration, volume, collection, stability
and tissue records support a bounded model comparison with a simpler baseline
and uncertainty. Processed percentages may support a descriptive question while
leaving amount/rate fitting ineligible. Term placental transport, BeWo results,
early implantation and sustained development remain separate. All continuous
human embryo-to-birth gates remain open.
