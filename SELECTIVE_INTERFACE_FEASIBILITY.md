# Selective interface function: exploration and design refinement

AI-assisted primary-source inspection, 2026-10-09. Candidate evidence and
conceptual requirements; human scientific review is pending. The research
target remains an embryo-to-birth system with assessed follow-up outcomes.
This exploration narrows what its interface would need to demonstrate.

The strongest new direction is **selective, stage-appropriate function**:
nutrient delivery, unwanted passage, tissue injury and endocrine behavior
need separate observations. A single permeability or cell-identity endpoint
cannot establish that joint behavior. This is a design inference, not a
qualified biological model or a device specification.

## Two new primary candidates

| Source | Reported observations relevant here | What remains unresolved |
| --- | --- | --- |
| [Antich et al., Scientific Reports, published 28 July 2026](https://www.nature.com/articles/s41598-026-61708-y) | Stage-like human placental tissue models; Figure 6 distinguishes cellular uptake, directional nutrient-transfer readouts and transporter activity. Primary and immortalized cell sources remain separate. | Models use term-derived cells; an early-like model is not an actual early-gestation donor or an embryo undergoing gestation. Function/omics specimen linkage and eligible raw transport trajectories need qualification. |
| [Fattahi et al., Nature Biomedical Engineering, published 9 October 2026](https://www.nature.com/articles/s41551-026-01801-9) | Figure 2 separates electrical resistance, tracer permeability, injury, hormone and glucose-transfer readouts under source-defined exposure comparisons. The source defines glucose transfer using receiver concentration change. | Published endpoint rows do not establish linked donor/receiver trajectories or cross-assay specimen identities. Tissue readouts do not measure sustained embryo/fetal development. |

Neither source supplies a demonstrated continuous-human path. Their assays
motivate a narrower requirement; they cannot be joined to implantation or
ovine fetal-support reports as one gestation.

## Concrete source inputs inspected

The two article HTML snapshots, repository metadata and downloaded source
files remain ignored, read-only local artifacts under
`artifacts/interface-exploration-2026-10-09/`. No raw public data is added to
the software repository or rewritten. Dynamic HTML hashes identify the
observed local snapshot, not a universal publisher revision.

| File/scope | Bytes | SHA-256 |
| --- | ---: | --- |
| Fattahi Figure 1 workbook; sheet inventory and scalar cells inspected | 21,173 | `d49ca7a4d46b0d4d92391721540f56912ff8a204ceb425d1ebad70056989f36c` |
| Fattahi Figure 2 workbook; audit limited to `Figure 2h`, `Figure 2i`, `Figure 2k` | 19,315 | `c3bbcc7d226ffcd24f015570ff89e7894bdeb62e9143c60219883a0ec98024c0` |
| Fattahi Figshare v1 `Main Fig 2.zip`; archive names/sizes inventoried, images not analyzed | 17,243,800 | `04d2a6d28224e860807c9ff355c6833d41aae42df63cb0a421119721ce3c7d85` |

The [publisher Figure 2 workbook](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41551-026-01801-9/MediaObjects/41551_2026_1801_MOESM4_ESM.xlsx)
provides 92 scalar values across five selected readouts, with original
worksheet/cell locators and numeric lexemes retained by the audit. These
are source-value counts, not biological n. `Sample 1`–`Sample 4` repeat in
different tables and conditions; this alone establishes neither repeated
measurements nor independent physical specimens. Donor, experiment,
cross-assay linkage and complete starting populations remain unqualified.

Figure 1 also contains concentration/fluorescence-related and structural
endpoints, but no linked concentration-and-mass inventory was qualified
from that inspection. The inspected Figure 2 archive contains image files,
not an additional tabular transport trajectory; other Figshare archives
were not inspected. This does not establish that raw observations are
unavailable everywhere.

The [Figshare record](https://doi.org/10.6084/m9.figshare.32098060.v1)
declares CC BY 4.0 and a repository publication date of 25 April 2026.
That date is distinct from the journal's October publication. The journal
article declares CC BY-NC-ND 4.0; workbook-specific terms remain unqualified.
Do not transfer the archive's rights declaration to the publisher workbook.
Human source-specific reuse review remains separate from byte verification.

Antich's data availability points to
[GSE318016](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE318016) and
[PXD072837](https://www.ebi.ac.uk/pride/archive/projects/PXD072837) for
transcriptomics and proteomics. A metadata-only check of the GEO record found
12 RNA-seq samples and a raw-count matrix. The PRIDE file manifest lists 12
mass-spectrometry `.raw` files and one `ProteinQuant_summary.xlsx`; no large
raw omics files were downloaded. These records can qualify molecular datasets,
not nutrient-transfer trajectories.

**Bounded public-file closure, 2026-10-10:** the publisher lists 16
supplementary items. The 12 XLSX sheets previously inventoried have gene
expression, pathway/enrichment or RNA/protein-comparison headers; the sheet
named `Transport` is a gene-expression table. The four additional items were
checked as follows: Supplement 1 is a narrative note, Supplements 2 and 3 are
one-page narrative notes, and Supplement 16 is a figure package with embedded
images and no tables. Their hashes and scope are in the
[metadata inventory](config/source_inventories/antich_2026_workbooks.json).
The figure images were not digitized, and the spreadsheet cells were not
reanalyzed. No structured per-replicate functional-transfer table was found
in this bounded file set.

The article reports separate trophoblast uptake and receiver-side targeted
metabolite measurements for glucose, leucine and linoleic acid. Its methods
describe receiver-side collection over a 24-hour interval and three
biologically independent replicates; Figure 6 reports N=3. Supplementary
Note 3 describes the targeted-metabolite readout in peak-area terms. The
published files do not provide replicate-by-time numeric transfer rows or a
replicate-to-donor/source crosswalk. A peak-area signal is distinct from
calibrated concentration, amount, net flux or nutrient delivery fraction;
those require assay calibration and collection-volume, baseline and recovery
accounting. Thus this is a useful **descriptive
functional candidate**, not a fit-ready or independently validated transport
dataset. No expression fit, genotype inference or gene-to-transport-rate
assignment was made.

## Freeze IF-3: which distinct functions are actually observed?

**Question:** can a source-linked interface demonstrate directional
nutrient delivery and selective barrier function while retaining tissue
viability and the required endocrine behavior over its stated interval?

The first discriminator is a correctly identified observation vector,
with each quantity's units and ascertainment preserved:

| Quantity | What its observation can address | Inference it cannot supply alone |
| --- | --- | --- |
| Cellular nutrient uptake | Entry/accumulation in measured interface cells | Export to the receiver or embryo nutrition |
| Receiver concentration change | Analyte change in the sampled receiver under its collection definition | Mass flux, fraction of donor input recovered or oxygen support |
| Tracer permeability | Passage of that tracer through the tested barrier | Adequacy of selective nutrient transport |
| Electrical resistance | The electrical barrier endpoint under its calibration | Universal solute permeability or tissue health |
| Hormone concentration | The endocrine concentration endpoint under its collection process | A secretion rate without collection accounting, correct whole-system signaling or complete pregnancy maintenance |
| Injury/viability | The measured damage/viability endpoint | Developmental adequacy across organs and later stages |
| Linked development/follow-up | The actual assessed organismal outcome and window | Unassessed later health or embryo-to-birth success |

Treat the published functional comparisons as separate assays until the
source establishes pairing. Do not derive a within-specimen leak-versus-
nutrition relationship from matching worksheet row numbers. No weighted
health score, universal optimum or machine operating target follows from
this vector.

## Accounting needed before fitting transport

This is dimensional bookkeeping for a future reviewed observation contract,
not a new physiological equation or a prescription for a biological assay.
For the same tracked analyte, control-volume boundary and time window:

```text
total analyte input - total analyte output
    = change in fluid inventory + change in tissue inventory
      + analyte removed by conversion + other unrecovered analyte
```

All terms require compatible amount units. For measured flow systems,
input/output amounts would need calibrated concentration-and-volume or
concentration-and-flow records and collection corrections. Net receiver
recovery would also subtract analyte already supplied to the receiver.
Storage, conversion and unrecovered analyte must remain distinct unknowns;
an accounting residual cannot silently become a biochemical uptake rate.

The published glucose percentage does not provide these amounts. Its
denominator is not a measured donor input amount. Converting it to a
permeability coefficient, an exchange rate or a nutrient-delivery fraction
without the missing observation mapping would invent a quantity.

IF-1's identifiability counterexample still applies to its own exact model
class. Adding these endpoints or a more elaborate pathway diagram does
not resolve its rate ambiguity unless eligible observations and their
relationship to model states actually discriminate the competing models.

## Refine the machines' evidence requirements

For Machine A, retain distinct hypotheses for selective transfer, interface
storage/conversion and unintended passage. Their biological realization and
stage changes remain unresolved; the current equations acquire no biological
parameter values through this exploration.

For Machine B, observe delivered support, barrier state, tissue injury and
signaling separately. Hardware stability and a high transfer readout are
insufficient substitutes. Observations must retain delayed/unavailable
readings, uncertainty and actual source intervals.

For Machine C and follow-up, none of these tissue-model assays evaluates
neonatal transition or long-term development. Those requirements still need
source-linked organismal outcomes from their complete starting cohorts.

Three separate stage descriptors are necessary in a future qualified data
card: **donor tissue age**, **model phenotype/stage label**, and **elapsed
assay time**. A term-derived tissue with an early-like phenotype does not
establish an early developmental transition. No gestational interval is
inferred for the present endpoint intake.

## Reproduce the candidate audit

Provide the exact publisher workbook and new output directories:

```powershell
wombmodels audit-fattahi-source --workbook artifacts/interface-exploration-2026-10-09/fattahi-fig2.xlsx --out artifacts/fattahi-functional-audit
wombmodels validate-observations --dataset artifacts/fattahi-functional-audit/input_dataset.json --source-root artifacts/interface-exploration-2026-10-09 --out artifacts/fattahi-functional-intake
wombmodels verify-bundle --bundle artifacts/fattahi-functional-audit --strict
wombmodels verify-bundle --bundle artifacts/fattahi-functional-intake --strict
```

The offline command reads only the selected sheets, checks exact metric and
condition headers, rejects formulas/nonfinite values and changed source
bytes, and publishes source locators and a candidate observation dataset.
Unit IDs and model-age bounds remain null; no individual-phenotype
eligibility, pairing, effect estimate, biological fit or ledger promotion
is asserted. The glucose readout remains a percentage in its original
definition. Existing dimensionless fixtures stay uncalibrated.

The next data target is an existing, reviewed set of linked inlet/outlet,
interface-inventory and functional observations with actual specimen/source
hierarchy, exclusions, calibration and collection metadata. The early-
implantation Figure 7 data requirement also remains open. Both targets can
be pursued without treating separate assays, species or developmental
intervals as a continuous human gestation result.

[Collection accounting and native source recovery](COLLECTION_ACCOUNTING.md)
now adds a concrete placental-perfusion trajectory/tissue candidate recovered
from embedded Prism CSV tables. It tests collection and residual-partition
ambiguities in a separate dimensionless fixture. Donor linkage, correction
ancestry and model-fit eligibility remain open.
