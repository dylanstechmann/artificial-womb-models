# Preserve usable material transfer, not just availability

AI-assisted research curation and design inference, 2026-10-09. Human scientific
review pending. This is an observation/data requirement, not an experimental
protocol, tissue manipulation, device specification or operating recommendation.
Complete human embryo-to-birth support remains unestablished.

The [terminal-boundary question](MIDGESTATION_BOUNDARY.md) distinguishes delivery
failure from tissue-use failure. Add an intermediate possibility: **support
tissue receives material but fails to pass it onward or release its own products**.
Increasing external availability alone would not establish that this step works.
This is a design inference; it does not diagnose the terminal mouse preprint.

## A primary-source counterexample

[Koike et al. (2023), Biology Open](https://doi.org/10.1242/bio.060081) reports
mouse yolk-sac visceral-endoderm findings in an Enpp2-deficient comparison:

| Observed comparison | Locator in pinned Europe PMC XML | What the comparison leaves open |
| --- | --- | --- |
| Similar yolk-sac IgG signal with lower downstream coelomic-fluid IgG | `s2a`, paragraph 3; Fig. 1D | Tissue abundance is not proof of onward passage or embryonic-organ receipt. |
| Similar cellular AFP with lower release from isolated tissue | `s2d`, paragraph 1; Fig. 3B | Protein presence is not proof of secretion. |
| VEGF fluid comparison does not reach significance, while isolated-tissue release is lower | `s2e`, paragraph 1; Fig. 4B,D; `s3`, paragraph 2 | A nonsignificant fluid difference is not equivalence; different assessment contexts cannot establish paired flux. |
| Lower TGF-beta1 in fluid and isolated-tissue output; cellular protein not established | `s2e`, paragraph 1; Fig. 4A,C | Unchanged RNA does not establish protein production. |
| Increased EGFR protein with unchanged receptor RNA | `s2c`, paragraph 1; Fig. 2 | The authors' turnover interpretation concerns a receptor, not measured nutrient digestion. |
| Different dextran and transferrin uptake findings | `s2a`, paragraphs 2–3; Fig. 1A,C | One tracer does not certify every uptake route. |

The source's secretion/clearance explanation for fluid-versus-isolated-tissue
differences is an interpretation. It is not a measured decomposition. Multiple
processes change together; no unique mechanism or correction follows.

Preserve the source branches: E8.5 assays, an E7.5-start tracer comparison, and a
separate E9.5 tissue-origin/development assessment. These do not establish one
continuous ex-utero developmental interval. The latter reports 44 collected
embryos and 13 mixed-endoderm cases. One had the selected embryo-identity
condition and appeared nearly normal; the other 12 had a different embryo origin
and stopped normal development. The authors explicitly consider the single
case insufficient. No treatment success rate or durable rescue is inferred.

Selected text and captions were inspected. Underlying images, supplementary
figures, raw assays, calibration, specimen/dam/litter hierarchy and cross-panel
pairing remain unqualified. Rat-origin IgG is a tracer in a **mouse** study; it
does not change the organism species or establish nutritional sufficiency.

## Refine the observation contract

The optional `assay.functional_context` retains six exact fields:

- `compartment`: where the readout was obtained.
- `material`: the observed tracer, molecule, receptor or developmental endpoint.
- `process`: the source-linked process category; it is not a validated mechanism.
- `quantity_basis`: signal, concentration, activity or other reported basis.
- `assessment_context`: in-utero, whole-embryo ex-utero, isolated-tissue or other branch.
- `source_locator`: the passage/panel supporting that declaration.

The validator requires all six when the object is supplied, rejects unknown or
unbounded metadata, and exports `functional_contexts.csv`. Existing records may
omit it; no compartment or mechanism is inferred from endpoint prose. Exact
grouping includes the full assay context, preserving otherwise identical
readouts from different compartments. Unit-overlap checks remain conservative:
adding a context does not create new independent biological units.

The [candidate intake](config/observations/koike_2023_material_handoff_candidate.json)
contains 13 qualitative source findings and one missing linked organ-use/later-
function requirement. Comparator IDs label source panel groups, not common
control specimens. Unknown biological identities remain null; both continuity
edges remain `not_reported`. The missing record is not an adverse outcome.

The [source inventory](config/source_inventories/material_handoff_2026.json)
pins a 121,044-byte XML retrieval by SHA-256. Pinning bytes does not authenticate
publisher revision, scientific transcription or human review. Source files stay
outside generated bundles.

```powershell
python -m wombmodels validate-observations --dataset config/observations/koike_2023_material_handoff_candidate.json --source-root . --out artifacts/material-handoff-intake-NEW
python -m wombmodels verify-bundle --bundle artifacts/material-handoff-intake-NEW --strict
```

Run with this project installed or `src` on the import path. The optional local
source check needs the XML at the inventory's path with matching bytes. The
validator does not retrieve sources or run assays. Use a new output directory.

## What a discriminating source dataset would need

| Competing explanation | Required linked quantities/context | Ambiguity if absent |
| --- | --- | --- |
| Reduced entry into support tissue | Input identity and tissue receipt, reported exposure/time, retained failed/excluded units | Tissue signal can reflect retention, degradation or assay behavior as well as entry. |
| Failed onward passage or release | Tissue and downstream material state, quantity basis, compartment volume if interpreting concentration, source-unit links | High tissue content can coexist with poor downstream receipt. |
| Altered removal or fluid state | Downstream accumulation/clearance and compartment inventory over comparable times | Equal concentration can conceal different throughput or volume. |
| Failed recipient use or developmental signaling | Actual embryonic-organ receipt, processing/function and developmental outcome | Tracer in surrounding fluid does not establish usable organ delivery or preserved development. |

These are data-qualification requirements, not proposed assay procedures. A
compartment concentration reflects inventory relative to volume. Inventory
change contains entry, exit, local production and degradation. One endpoint
cannot uniquely assign those contributions. Different molecules, sampled units
or assessment branches cannot be combined into a measured material balance.

## Consequences for the machine hypothesis

Machine A needs a functioning **uptake → processing/passage → release →
recipient-use chain**, with developmental signaling assessed separately from
nutritional delivery. Preserving endogenous support tissue remains a candidate
route; replacing selected functions must account for where usable products are
needed and which tissue interactions accompany them. Presence of support
tissue, vessels or source material does not establish the chain's sufficiency.

Machine B needs compartment/material/context evidence alongside supply, growth
and injury timing. Selective preservation of one readout must not obscure
failure of another. Cross-context source discordance motivates a question; it
does not by itself identify the failure in a growing support unit.

The [Jin et al. accepted mouse yolk-sac article (2026)](https://doi.org/10.1038/s42003-026-10656-4)
now has [selected-text and source-workbook qualification](SUPPORT_DEVELOPMENT_DISCORDANCE.md).
Reported component function persists alongside embryo-proper arrest. Direct
assays, molecular proxies and expression annotations remain distinct. Source
timing, units, starting rosters and paired recipient outcomes require further
qualification; no continuous-gestation edge is established.

The next useful analysis remains a source-qualified, unit-linked comparison of
receipt and recipient function across a developmental boundary, with losses and
sampling branches retained. These mouse observations sharpen that contract;
they do not establish a human implementation or a fix for terminal injury.
