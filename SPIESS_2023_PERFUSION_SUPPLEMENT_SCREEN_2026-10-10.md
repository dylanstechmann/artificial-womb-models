# Spiess et al. 2023 placental-perfusion supplement screen

**Disposition:** useful field-availability comparator; no observation rows imported. No author was contacted.

The [primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9868778/) reports ex vivo term-human placental perfusions for protopine and comparison compounds. Its methods define recovery from maternal, fetal and sampled fractions and an empty-system adherence measurement. The results present concentration profiles as mean ± SD, and Table 1S reports group-level recovery components. The article reports that sampling accounted for a nontrivial share of recovered material, but the table does not provide a run-by-time sample-removal ledger. It also cautions that calculated recovery may be low because fetal-circuit adsorption was not measured.

The official PMC article page is readable and exposes a named 2 MB supporting-information PDF, with a description covering absolute concentration profiles, recovery, placenta characteristics, individual-perfusion details and bioanalytical methods. The linked attachment HEAD request returned HTTP 200 but served an 1,817-byte HTML challenge page rather than PDF content; the legacy PMC OA package endpoint returned 404. The supplement remains uninspected. See the [Cycle 231 receipt](artifacts/perfusion-comparability-2026-10-11/spiess-pmc-supplement-route-cycle231.json). A [University of Basel repository record](https://edoc.unibas.ch/entities/publication/bc8556f6-d477-49cd-baa9-d6c6fed4d831) is currently marked “request a copy”; its indexed dissertation PDF text nevertheless exposes the structure of Table 3S. That table is organized by compound and experiment number and reports placenta/cotyledon characteristics, total maternal and fetal volume loss at the end, and preparation/pre-phase/perfusion timing. This is per-perfusion context, not a concentration time series. The article’s figure captions and indexed Table 3S material did not expose a row-linked sequence of concentrations and sampled volumes for each perfusion.

This changes the earlier screen in one specific way: endpoint volume-loss and timing fields are visible in an indexed companion excerpt, so those fields should not be described as wholly absent from the public record. The observed volume field is total loss at the end, however; it does not supply timepoint-specific remaining volume or sample-removal amounts. Group-level recovery summaries cannot be joined to the per-perfusion Table 3S rows from the inspected evidence. Experiment numbering is compound-specific in the table layout, and no shared donor key was located, so equal numbers do not establish same-placenta reuse or independent donors.

### Additional Europe PMC and publisher-route check (Cycle 241)

Europe PMC's official full-text XML endpoint returned article XML and exposed
the same supplement filename as relative metadata, but its separate article
file-serving path returned HTTP 403. The exact Thieme article-PDF route returned
HTTP 404 over both HTTP and HTTPS; it is not the supplement file. No alternate
PDF bytes were retrieved, and the supplement remains uninspected. See the
[Cycle 241 route receipt](artifacts/perfusion-comparability-2026-10-11/spiess-europepmc-publisher-route-cycle241.json).

The primary article is distributed under CC BY-NC-ND. This screen records the field map and availability boundary without reproducing the table or constructing a derivative observation dataset. The study is a term-placenta xenobiotic-transfer comparator; it has no embryo-development, continuous-gestation, birth, neonatal-transition or later-health outcome. It does not close the Mathiesen 2020 volume/recovery gap or qualify a dimensional transport fit.

## Screen outcome

- **Present at group level:** mean concentration profiles; recovery fractions for maternal, fetal, sampled and system-adherence components.
- **Present in the indexed Table 3S excerpt at per-perfusion level:** placenta/cotyledon context, total compartment volume loss at the end, and phase/perfusion timing.
- **Not exposed in the inspected materials:** per-perfusion concentration trajectories, time-resolved sample-removal/reservoir-volume history, and an explicit cross-compound placenta/donor key.
- **Use:** comparator for observation-contract fields and for distinguishing endpoint volume summaries from time-resolved accounting. Do not merge or pool its values with Mathiesen 2020.

The structured candidate entry and retrieval boundary are retained in the [perfusion availability crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json). The [primary article](https://doi.org/10.1055/a-1829-9546) and repository excerpt are supporting records; the actual supplementary PDF and dissertation bytes were not retrieved into the workspace. The official PMC route check is recorded in [Cycle 231](artifacts/perfusion-comparability-2026-10-11/spiess-pmc-supplement-route-cycle231.json).
