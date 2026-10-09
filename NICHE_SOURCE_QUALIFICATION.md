# Niche mechanics and developmental outcomes: source qualification

AI-assisted source audit, 2026-10-09. Candidate transcription; human source,
scientific and reuse review pending. No mechanical calibration, causal effect,
embryo procedure or human gestation result is produced.

The [feasibility strategy](FEASIBILITY_STRATEGY.md) proposes a remodelable
maternal niche and a growing living interface. This audit makes its next
empirical question more concrete: **what do existing mechanical and
developmental observations discriminate, given their actual source hierarchy?**

## Source and exact inspected scope

[Guo et al., Nature Communications (2026)](https://www.nature.com/articles/s41467-025-68039-y)
links a [Source Data workbook](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-025-68039-y/MediaObjects/41467_2025_68039_MOESM18_ESM.xlsx).
The downloaded file has 55 worksheets; the executable audit reads five selected
Figure 4 panels and one supplemental profile sheet. Other sheets were inventoried,
not fully qualified. The source remains unchanged in ignored local artifacts.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `guo-source-data.xlsx` | 137,918 | `c84b1faf2ebe02c812af7ec73d94a10c6640a11fba677ac85947999b9dc33e8e` |

| Selected sheet | Observed scalar structure | Current interpretation |
| --- | --- | --- |
| `Fig4A` | Two labeled columns with 9 and 10 values | Source relaxation half-time comparison; physical units and hierarchy unqualified in this audit. |
| `Fig4C` | Three labeled columns with 10 values each | Source Young-modulus comparison; not proof of equivalent stiffness. |
| `Fig4D` | Three labeled columns with 5 values each | Source relaxation half-time comparison; not paired with modulus rows. |
| `Fig4E`, `Fig4F` | Each has 7, 4 and 5 percentages across its three conditions | Caption-reported two-cavity and egg-cylinder outcomes at IVC days 3 and 4, respectively; experiment/embryo identity and denominators unresolved. |
| `Sup 10 I` | One X column and three response columns, each with 200 values | A source profile inventory, not 200 independent replicates. Units, loading/holding history, normalization and individual-versus-summary profile status remain unqualified. |

The audit retains 96 endpoint-cell locators and 800 supplemental profile-cell
locators with original numeric lexemes. Only the 32 developmental percentages
enter `input_dataset.json`; mechanically unqualified values remain in a separate
inventory. Source condition titles are retained exactly, without expanding them
into a preparation recipe. Blank trailing cells are not turned into zero or
classified as excluded embryos.

## What the data permit now

Source tracing is executable: selected headers, finite values, exact populated
cell sets, original lexemes and the pinned workbook hash are checked. The
candidate observation dataset retains mouse species, actual elapsed culture
days, null unit IDs, unreported replicate roles and no continuity edges.
Elapsed culture time is not added to the embryo's source starting age.

The source panels motivate distinct mechanical and developmental observations,
but lack explicit links between them. A repeated condition title permits a
descriptive source partition; it does not authenticate a material batch or
embryo experiment. Equal row positions cannot establish repeated outcomes,
matched specimens or a material-to-development correlation.

The paper's nonsignificant Young-modulus comparisons cannot establish
equivalence. A future equivalence question needs a reviewed margin appropriate
to the mechanical estimand, independent runs, uncertainty and measurement
comparability. This audit supplies no margin and computes no equivalence test.

Outcome percentages also need their original numerator, starting denominator,
experiment identity and exclusions. Recovering a likely integer denominator
from a rounded percentage would invent source metadata. Later morphology or
cardiac activity cannot substitute for the missing starting roster.

## Frozen candidate questions and missing observations

| Question | Candidate comparison | Required qualification |
| --- | --- | --- |
| Does the mechanical profile require time-dependent response? | Constant response under a reviewed held-deformation contract versus a relaxing response with a possible residual plateau | Exact assay mode, loading/holding history, time origin/units, normalization, geometry and independent profile mapping. |
| Are material groups mechanically comparable beyond stiffness? | A reviewed equivalence question for modulus, separately from relaxation/architecture | Independent material/run IDs, comparable measurement mode, uncertainty and a prespecified margin. |
| Does mechanical behavior explain developmental outcomes? | Stiffness-only explanation versus time-dependent response, retaining chemistry, adhesion, architecture and transport as possible confounds | Material-to-embryo/run links, outcome numerators/denominators, exclusions and prespecified contrasts. |

The current Kelvin–Voigt fixture represents creep/recovery under imposed
stress. Its time constant cannot be substituted for source relaxation half-time
or calibrated from these inventories. No profile fit, cross-panel regression,
held-out claim or causal estimate is performed here.

## Reproduce the audit and candidate intake

Provide the exact workbook and new output destinations:

```powershell
wombmodels audit-guo-source --workbook artifacts/feasibility-strategy-2026-10-09/guo-source-data.xlsx --out artifacts/guo-niche-audit
wombmodels validate-observations --dataset artifacts/guo-niche-audit/input_dataset.json --source-root artifacts/feasibility-strategy-2026-10-09 --out artifacts/guo-niche-intake
wombmodels verify-bundle --bundle artifacts/guo-niche-audit --strict
wombmodels verify-bundle --bundle artifacts/guo-niche-intake --strict
```

The standard-library reader evaluates no formulas or workbook programs and
rejects changed headers, populated-cell inventories, hashes and nonfinite
values. Publication is exclusive and receipt-last. Source hashing and bundle
integrity do not establish scientific transcription or review.

The article declares CC BY-NC-ND 4.0; workbook-specific reuse remains
unqualified. Original source bytes are external and untouched; local outputs
are reformatted candidate scalar inventories. No publisher data is committed,
no public redistribution is performed and no author inquiry has been sent.

The result advances data access for a niche-function comparison. The missing
material/experiment hierarchy, loading definitions, outcome denominators and
review contract remain prerequisites for an eligible analysis. It supplies no
human niche setting, sustained placenta replacement or embryo-to-birth path.
