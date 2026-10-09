# Native placental-perfusion data: question and qualification card

AI-assisted source inspection, 2026-10-09. Candidate transcription, no human
review or biological fit. This is a data-analysis requirement, not an assay or
device operating procedure.

The [primary study](https://link.springer.com/article/10.1007/s00204-026-04418-8)
and its pinned DOCX supplement provide processed circulation/time and tissue
percentage tables. The [recovery dossier](COLLECTION_ACCOUNTING.md) records the
source hash, embedded-object identities and reproducible extraction.

## What is available now

The offline audit emits 448 source-linked Y observations: circulation tables
with explicitly referenced `Time (min)` metadata, and tissue endpoints with
caption-reported elapsed time. The cell export preserves numeric lexemes and
one-based CSV locations. Native set GUIDs identify source data sets; they do
not identify biological specimens. Neither aligned slot positions nor labels
`Placenta 1`–`Placenta 4` authenticate cross-table donor pairing.

The candidate intake records human ex vivo placental tissue, processed `% of
initial dose`, unqualified exact donor gestational ages and no developmental
continuity. Each independent-unit ID is null and each replicate role remains
`not_reported`. No value is relabeled as an original instrument observation.

## Selection affects the target population

Supplement `word/document.xml`, paragraph 17 in document order, defines
successful perfusions using an antipyrine compartment-ratio criterion. Figure
S10's caption specifies results per successful experiment. The inspected
tables do not provide the starting-attempt denominator or failure/exclusion
roster. The exact criterion remains in the external source; it is not supplied
as an operating recommendation here.

This limits the target to the included source experiments. Using a transport
readout in selection may condition subsequent transport comparisons; this is
an analysis concern, not evidence that a particular bias direction or magnitude
has been demonstrated. A source caption's four biological replicates does not
establish the overall assay success fraction. Unsuccessful, technically
unavailable and deliberately excluded attempts need separate records.

The supplement also describes multiple tissue subsamples, while the native
tissue table has six Y slots per compound within each labeled row. Their
relationship is unqualified. Neither averaging all slots as independent donors
nor assuming they are paired analytical duplicates is justified by layout.

## Separate questions and current decisions

| Question | Current decision | What would change the decision |
| --- | --- | --- |
| Can source values and time definitions be traced? | Executable candidate transcription available; human review pending | Confirm cell mapping, caption mapping, exact quantities and source-specific reuse terms. |
| Do paired maternal/foetal trajectories constrain transport alternatives? | Not qualified | Authenticate specimen/run/slot links and the original observations, corrections and uncertainty. Freeze a simpler alternative and analysis contract before fitting. |
| Can tissue endpoints resolve storage versus conversion/unrecovered analyte? | Not qualified | Authenticate tissue/run linkage and subsample hierarchy, denominator definitions, and collection-corrected amounts. A tissue endpoint alone leaves other sink ambiguity. |
| What fraction of starting attempts succeeds? | Unknown denominator and exclusions | Obtain a complete attempt roster with included/failed/excluded/unavailable status and actual criteria. |
| Does this support continuous human development? | Not assessed by these assays | Requires separate same-unit developmental/transition/outcome evidence; term-tissue transfer does not supply it. |

No dynamic rate, permeability, pooled biological n, uncertainty interval or
survival probability is estimated from this candidate intake. Its numerical
time values are assay observations, not simulation settings or gestation time.

## Minimal information needed for review

- A coded donor/run mapping for all circulation columns and tissue rows, with
  relationships across compounds and compartments explicitly stated. Retain
  source identities without introducing direct personal information.
- The starting-attempt roster, each inclusion/exclusion/failure status, and
  links from included runs to their recorded results.
- Original concentration/instrument and calibration records; initial-dose
  denominator definitions; volume/collection histories; and which records
  received stability, hydrolysis, sampling or other corrections.
- A mapping of native tissue slots to tissue subsamples, repeated analytical
  measurements and their source runs, with uncertainty/missingness definitions.
- Confirmation of the exact source version, relevant units and reuse terms.

## Draft inquiry — unsent

We are developing a personal, AI-assisted research software project for
source-linked transport observation intake. We recovered the native Prism
tables embedded in the updated supplementary DOCX for your 2026 comparison
study, preserving CSV values and metadata without running saved analyses.

For Supplementary Figures S9 and S10, could you clarify the coded mapping
between the maternal/foetal column slots, compounds and labeled placental
tissue rows, and the hierarchy represented by the six tissue subcolumns?
We would also appreciate the complete attempt/inclusion roster, original
concentration and correction ancestry, normalization and collection metadata,
and confirmation of source-data reuse terms. These details would determine
whether a bounded transport-model comparison is supportable. We have not fitted
biological parameters or treated source slots as verified independent donors.

This draft has not been sent. No author contact is authorized by its presence.
