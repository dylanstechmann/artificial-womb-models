# Maternal-interface state and embryo progression

AI-assisted evidence curation and design inference, 2026-10-09. Human scientific
review pending. This document supplies offline observation requirements, without
biological procedures, device assembly or operating settings. Healthy continuous
human embryo-to-birth support remains unestablished.

The [machine concept](SYSTEM_DESIGN.md) now needs an explicit maternal-interface
state alongside embryo state. A remodelable physical boundary may be important,
but it cannot alone substitute for maternal receptivity, tissue responses and
usable exchange. Retaining those responses also cannot alone establish embryo
progression. These are joint requirements, with different observables.

## A living maternal-tissue comparator

[Hiraoka et al., Nature Communications (2025)](https://doi.org/10.1038/s41467-025-60610-x)
reports an ex-vivo mouse embryo/endometrial-tissue system. The
[source inventory](config/source_inventories/hiraoka_maternal_interface_2025.json)
pins the public XML, publisher HTML, two PDFs and a native Figure 5 workbook.
Selected results and captions were inspected; Supplementary Figures 4/5 and
the reporting-summary study-design page were rendered and visually checked.
Source procedures remain external. Original source bytes are unchanged;
source-specific reuse rights and human scientific review remain pending.

The source starts at mouse E3.75. It labels 24, 48 and 96 source hours with
E4.5, E5.25 and E5.5 in-vivo correspondence. These are resemblance labels,
not an assertion of chronological equivalence. The endpoint is early development.

| Distinct source branch | Bounded finding | Required interpretation |
| --- | --- | --- |
| Supplementary Fig. 5, 24h attachment | 343/362; printed 94.2% | Attachment is not embryonic functional progression. The printed percentage differs from the pooled count ratio; aggregation convention unqualified |
| 48h retention | 235/279 | Different loaded denominator; no subtraction from the 24h cohort into presumed losses |
| 96h retention | 55/96 | Presence on maternal tissue is a distinct endpoint from later organism health |
| 48h immunostained compartments | EPI-like 10/24; ExE-like 24/24 | Assessed morphology/marker subset, separate from all loaded embryos |
| 96h immunostained compartments | EPI-like 4/22; ExE-like 14/22 | Favorable extraembryonic findings must retain the limited embryonic-compartment result |
| Maternal tissue observations | Glandular/immune/decidual features, receptive tissue-state markers and vascular pattern | Architecture and expression do not establish every maternal function or a perfused exchange interface |
| Figure 5 signaling comparison | Attachment, later shedding/retention and assessed invasion change | Bounded functional involvement; complete mediator and all maternal/embryo effects remain unresolved |
| Separate persistent-fixation branch | Source describes loss of embryo morphology and apparent death by 72h | Preserve adverse findings. Coupled space/supply changes prevent a unique mechanical diagnosis |

Supplementary Fig. 5 is physical PDF page 8; the adverse branch is Results
Sec4 and Supplementary Fig. 4, page 7. Maternal findings are Results Sec5-Sec7,
Figures 3-5. No source rate is converted into a readiness or safety percentage.

The 24h printed 94.2% and count ratio 343/362 are retained separately. Direct
division rounds to 94.8%. This could involve an aggregation distinction; the
inspection does not diagnose a source error or replace the printed result.

## What the native cohort tables resolve

Figure 5F/G/I separates attachment/loaded, shedding/attached and retained/loaded.
The workbook supplies underlying count pairs and direct-division formulas. A
read-only check of original XML values, shared formulas and cached fractions
matches 31/31 calculations at absolute fraction tolerance 1e-14. This is
arithmetic qualification, without a biological effect estimate or workbook edit.

Notes at `5G!G9` and `5I!G9` explain that some attached embryos were used for
other assays. Their later shedding/retention could not be assessed, so later
denominators exclude them. This is informative disposition metadata: assay
withdrawal is different from assessed shedding. It does not provide individual
identities or a complete starting-to-ending roster.

The Figure 5 caption also distinguishes recipient-level ratio points in F/G/I
from embryo-level invasion values in K. `Exp` and `Embryo` labels alone do not
authenticate recipient/litter identities or cross-panel membership. Plot labels
and raw count rows have different offsets; follow each formula's references
rather than assigning the adjacent raw row's apparent label.

For the comparison-group `Exp3` label, formula-linked source cells contain
retained=3 (`5I!I5`), shed=3 (`5G!I5`) and attached=5 (`5G!J5`). These would
give a +1 closure residual **if** the labels refer to one assessed cohort with
exhaustive, mutually exclusive later outcomes. Eight other label candidates
close arithmetically. Neither outcome authenticates shared biological identity.
Retain the discrepancy for source reconciliation; do not repair a count, invent
an embryo or classify a biological loss.

The reporting summary says no collected data were excluded. This global
statement does not mean every initially loaded embryo was assessed at every
later endpoint. The workbook explains assay-specific withdrawals; the scope of
both statements must remain visible. Its global replication wording also does
not replace panel-specific unit definitions or validate a source-key join.

## Refine the design hypothesis

**Design inference:** Machine A needs a maternal surrogate whose state can
change appropriately as the embryo attaches, invades and grows. A physical
interface, a tissue with recognizable cell types, and a signaling response each
answer only part of that question. The source provides a living maternal-tissue
reference; it does not establish that retaining donor uterine tissue is a
necessary or sufficient solution for a human machine.

Keep three architecture comparators open: a physical niche with qualified
external support, a reconstructed living maternal interface, and a retained
maternal-tissue reference. The latter can inform function requirements, while
its own viability, growth, resource supply and durable compatibility remain
separate burdens. No material, signaling intervention or physical setting is
selected by this curation.

Machine B needs separate observations of maternal receptivity/remodeling,
attachment and invasion, actual recipient support, embryonic progression and
adverse tissue findings. Maternal vascular appearance is not a measurement of
directional exchange. Predicted transcriptional interactions are distinct from
observed responses and recipient function. A localized maternal response also
needs a non-embryo-associated artifact comparator, as the source discusses
weaker induction away from embryo attachment.

The next discriminator is whether maternal-interface state adds information
about subsequent progression **after accounting for earlier embryo state and
actual support**. Require source-established joint embryo/recipient identities,
the observation cutoff, original clocks, a disposition roster and all assessed
outcomes. Cross-sectional staining generally cannot provide a later outcome
for that same sacrificed unit; destructive-assay and longitudinal branches must
remain distinct. Shared recipient tissues also prevent treating every embryo
as an independent replicate.

The [boundary reanalysis contract](BOUNDARY_REANALYSIS_CONTRACT.md) still governs
earlier-movement prediction. This source does not repair the Bondarenko movement
map or establish that loss of coordination caused another source's arrest.
Its sharper disposition definitions are reusable observation requirements.

Resolve four source questions before a joint outcome analysis:

- Do the matching `Exp3` labels in 5G and 5I identify the same recipient and
  assessed cohort, and how should the three referenced counts be reconciled?
- Which units were withdrawn, when, for which assays, and were their later
  outcomes structurally unavailable or otherwise missing?
- Does the printed 24h percentage summarize recipient rates or the pooled
  count, and which experiment grouping supplies that quantity?
- How do the Supplementary Fig. 5 assessed subsets map to initial embryos,
  recipient tissue and the separate 24/48/96h endpoints?

The source declares GSE279808/GSE279809 scRNA-seq and GSE279268 bulk RNA-seq.
Their sample/file inventories and phenotype links remain unqualified. Expression
accessions do not supply these unit maps merely by sharing an article.

## Candidate intake

The [candidate dataset](config/observations/hiraoka_2025_maternal_interface_candidate.json)
contains eleven source summaries and one missing linked exchange/follow-up.
IDs remain null, source review remains candidate and continuity is
`not_reported`. The adverse configuration, selected subsets, source-count
ambiguities and maternal-versus-embryonic readouts remain separate.

```powershell
python -m wombmodels validate-observations --dataset config/observations/hiraoka_2025_maternal_interface_candidate.json --source-root . --out artifacts/maternal-interface-intake-NEW
python -m wombmodels verify-bundle --bundle artifacts/maternal-interface-intake-NEW --strict
```

Use the installed package or put `src` on the import path. The output directory
must be new. Local source hashes verify submitted bytes when available; they
do not authenticate source interpretations, unit identity or human review.
