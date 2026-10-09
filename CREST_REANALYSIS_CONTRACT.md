# Early-interface functional reanalysis contract

Revision 2026-10-09. AI-assisted source/data audit for IF-2 and design gate G1.
Human scientific and source-specific reuse review remain pending. This is
a contract for existing observations, not a biological procedure or a
physiological model. No functional effect or gestation outcome is fitted.

## Recovered source hierarchy

[E-MTAB-13629](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-13629)
provides a [Sample and Data Relationship Format file](https://www.ebi.ac.uk/biostudies/files/E-MTAB-13629/E-MTAB-13629.sdrf.txt).
The selected metadata describes human embryo/endometrial scaffold samples
at the reported embryo day 14. The inspected 57,215-byte revision has SHA-256
`4394e7b377e10c7bd47fab7cb387ccccdd87f26b3f66e2db9453793663584391`.
Its 60 rows reduce to seven source-named preparations and six distinct
declared embryo-member sets. The 13 distinct embryo-label strings are
reported identifiers, not independently verified biological n.

| Preparation | Declared embryo labels | SDRF rows | Distinct assay labels |
| --- | --- | ---: | ---: |
| Sample 1 | Em38 + Em45 | 8 | 2 |
| Sample 2 | Em2 + Em12 | 12 | 3 |
| Sample 3 | Em16 + Em1 + Em11 | 8 | 2 |
| Sample 3B | Em16 + Em1 + Em11 | 8 | 2 |
| Sample 6 | Em33 + Em28 | 8 | 2 |
| Sample 7 | Em5 + Em8 | 8 | 2 |
| Sample 8 | Em52 + Em54 | 8 | 2 |

Sample 3 and Sample 3B list the same three members. Their different
preparation labels cannot establish disjoint embryo populations. Repeated
SDRF rows and assay names are not biological replicate counts. Maternal
contributors and membership completeness are unresolved.

The [publication code archive, v1.0](https://zenodo.org/records/17955321)
has SHA-256
`f7af5da0b98f050c98f037698b02297e79571592f4a936ff9368f3a47c0e96b9`.
Only its annotation CSV and selected label-assignment script were read.
The script assigns `D3B$ID3` to `C4`; `C4` has no rows in the supplied final
annotation CSV. That comparison does not establish why it is absent,
biological attrition or a physical-specimen mapping. The CSV's 15,673 cells,
15 class labels and six batch categories remain annotation counts. Author
code, genomic variant contents and large expression objects were not
executed or analyzed.

These inspected sources do not establish links to individual Figure 7G
area/length measurements in
[Molè et al., Cell (2026)](https://doi.org/10.1016/j.cell.2025.10.027).
Matching a reported specimen count to 13 label strings would not establish
such a link. Scientific transcription and source review remain unverified.

## Reproduce the audit and candidate intake

Download the two exact revisions manually, then use new output directories.
Commands remain offline and use only the Python standard library:

```powershell
wombmodels audit-crest-linkage --sdrf artifacts/early-interface-linkage-2026-10-09/E-MTAB-13629.sdrf.txt --archive artifacts/interface-frontier-2026-10-09/crest-code-v1.zip --out artifacts/crest-linkage-v1
wombmodels validate-observations --dataset artifacts/crest-linkage-v1/input_dataset.json --source-root artifacts/early-interface-linkage-2026-10-09 --out artifacts/crest-pool-intake-v1
wombmodels verify-bundle --bundle artifacts/crest-linkage-v1 --strict
wombmodels verify-bundle --bundle artifacts/crest-pool-intake-v1 --strict
```

The audit pins both hashes, preserves selected metadata locators and
compares literal code labels with CSV category presence. Changed source
bytes require a new audit. Original files remain external and untouched.
The generated intake contains seven metadata records, all
`author_reported_summary` with `summary_only` roles and no transition edges.
Their text values are reported pool labels, not molecular or functional
measurements. SDRF age is not a continuous support interval.

The source-audit manifest binds both input hashes; its report records
selected archive-member hashes. Intake byte verification applies to the
SDRF artifact declared in its dataset. Byte verification and metadata
containment establish neither scientific accuracy nor analysis eligibility.

## Explicit pool membership

The observation contract accepts `independent_unit.kind = sample_pool` and
optional `members`, each containing a source-reported kind, identifier and
optional parent identifier. At most 100 distinct members are allowed.
Nested pools, missing member IDs and malformed lists fail. Membership can
be attached only to a reported pool identifier.
Surrounding whitespace is normalized consistently for direct/member IDs;
the original submitted dataset bytes remain preserved.

The validator indexes direct units and declared members within the same
source artifact, species, stage, assay and endpoint scope. Records sharing
an identifier cannot carry an independent-replicate assertion. Repeated,
technical or summary records remain preserved; `unit_members.csv` retains
members and `shared_unit_membership.csv` retains shared identifiers. No
quadratic expansion into every record pair is performed.

Missing members do not prove disjointness. Parent and source namespaces are
retained; identities are not inferred across different artifacts or from
genomic data. Member and pool-name counts are not verified biological n.
Pool records cannot establish demonstrated individual developmental
continuity, even when a pool name recurs across stages.

## Separate two reanalysis routes

**Phenotype-only reproduction** can evaluate Figure 7G independently of the
transcriptomic data if original endpoints, specimen IDs, experiment/source
hierarchy, selection and measurement metadata are supplied and reviewed.
First show per-experiment/source distributions, missingness and exclusions.
The paper reports two experiments; a specimen total cannot substitute for
hierarchy or establish broad generalization. Qualify inputs and freeze the
estimand, summaries and uncertainty method before any planned evaluation.

**Paired identity/function analysis** additionally needs a source-established
specimen link, pool membership and preparation/selection information.
Without it, report identity and function separately. Do not attach one
pool's expression profile to every member as an independent predictor or
duplicate one phenotype across cell rows.

Both routes retain the actual early in-vitro model and ascertainment window.
They establish no complete gestation or neonatal health. Embryos/blastoids,
Figure 7/supplementary subsets and their exclusions remain separate.

| Field family | Required existing source information |
| --- | --- |
| Identity/hierarchy | Coded specimen ID, embryo versus blastoid, experiment and endometrial-source IDs |
| Assignment | Source-defined condition/comparator labels and assignment records |
| Endpoint | Original area and outgrowth-length values, exact units, nulls with reasons |
| Measurement | Original image-analysis definition/version, ascertainment, calibration and uncertainty |
| Selection | Starting/assessed populations, exclusions, missing specimens and endpoint-specific denominators |
| Linkage | Relationship to RNA samples/member labels, or confirmation that cohorts are unpaired |
| Provenance | Original files, version, stable locators, permissible reuse and hashes |

No kinetic or signaling-control parameter is estimated from identifiers,
annotation counts or summary graphics. Human review is separate from intake
validity; G1 and the continuous-human system gates remain open.

## Unsent source-data inquiry draft

This draft has not been sent. It requests coded existing observations, not
participant identities, genomic variants or an experimental procedure.

> We are preparing an AI-assisted research-software reproduction of Figure
> 7G in your 2026 Cell paper. Could you share original HLA-G area and
> outgrowth-length values with coded specimen, experiment and endometrial-
> source identifiers; selection/exclusion and measurement metadata; and
> permissible reuse terms? If these specimens link to E-MTAB-13629, could
> you provide or identify the mapping, including pooled preparations?
> Confirmation that the cohorts are separate would also help scope the
> analysis. We will retain different model/endpoint populations separately
> and make no continuous-gestation claim.
