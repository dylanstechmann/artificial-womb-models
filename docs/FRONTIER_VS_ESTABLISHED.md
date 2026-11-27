# Frontier versus established

**Date:** 2026-11-27

This boundary separates reproduced software behavior from biological evidence and the long-term research ambition. It records local, AI-assisted software validation; it is not an independent scientific review.

## Established: reproduced software behavior only

As of 2026-11-27, the following software behavior was reproduced locally:

- All **812 tests** passed on **Python 3.10.22** and **Python 3.13.18**. The same 812-test suite also passed on Python 3.12.16.
- On each of Python 3.10.22 and 3.13.18, that interpreter freshly generated both supported dimensionless bundle kinds: `synthetic_exchange_software_fixture` and `synthetic_exchange_observability_diagnostic`.
- Same-interpreter fresh and relocated reruns returned `reproduced_exact`. Simulation ancestry was `no_parent_declared`; identifiability ancestry was `resolved`. Complete fresh and relocated reproduction-report directories matched byte-for-byte.
- Strict verification rejected a one-byte mutation in each supported source bundle kind with exit status 1. Rerun preflight rejected each mutated source with exit status 2 and did not publish an output.
- Clean-checkout validation ran all 812 tests with **207 expected local-evidence skips** and **605 non-skipped tests**, with no failures. This checks the tracked-file view without requiring untracked local evidence.

These results establish bounded software determinism, receipt/file integrity, declared ancestry handling, and mutation detection for the tested implementation and inputs. They do not establish numerical or scientific validity beyond those explicit software checks. Command records and receipt hashes are retained in ignored local evidence under `artifacts/m5-interpreter-compatibility-2026-11-27/`; CI execution remains separately unestablished by these local runs.

## Frontier and open work

- Biological evidence mapping remains open research work: source coverage, transcription, comparability, developmental continuity, species boundaries, review status, and evidence gaps must remain distinct.
- Complete human ectogenesis, including development from IVF through birth outside a human uterus, remains the long-term ambition rather than an established capability.
- Synthetic dimensionless fixtures are not biological assays. Evidence-ledger entries, source audits, model outputs, and passing tests must not be concatenated into a claim of complete gestation or clinical benefit.
- **No biological validation, physiological calibration, clinical readiness, or human gestation prediction is established.**

## Update when evidence changes

Update this document when evidence changes, and change the date with each substantive revision. Link the new evidence or exact software validation record, identify who reviewed it, and keep synthetic software results separate from biological observations. Re-run the relevant tracked-file and compatibility checks when the software boundary changes. Move a frontier item only when the new evidence directly supports that specific claim; additional tests or bundle hashes alone cannot establish biological validation or clinical readiness.
