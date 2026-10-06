# Artificial womb models

An open research software project investigating **complete human ectogenesis: development from IVF through birth outside a human uterus**. A wall-powered artificial womb that could eventually remove the need for gestational surrogacy is the long-term ambition. The first release makes the evidence gaps inspectable and the software experiments reproducible.

The repository contains a reviewed stage/evidence map and an abstract exchange, backup-power and monitoring fixture. Its outputs measure software behavior. Complete human gestation, replacement of surrogacy and fewer congenital defects remain unassessed or undemonstrated in the evidence ledger reviewed on 2026-10-06.

## What you can run

Python 3.10+; the runtime has no third-party dependencies.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\wombmodels evidence-report --ledger config/evidence.json --out artifacts/evidence-v1
.venv\Scripts\wombmodels simulate --config examples/exchange_fixture.json --out artifacts/exchange-v1
.venv\Scripts\wombmodels desk-status --url http://127.0.0.1:8092
```

Each output destination must be new. Evidence reports include claims, a species-separated stage map, requirements, the original input and a receipt. Simulations include trajectories, balance residuals, synthetic sensor fault metrics, the original fixture configuration and a receipt. Artifact formats are CSV, JSON and Markdown.

The fixture has invented **dimensionless** stocks, rates, times and thresholds. It represents substrate conversion into waste, powered input and clearance, wall-power interruptions, finite backup reserve, and synthetic sensor bias/dropout. There is no conversion from its time coordinate into hours, gestational weeks or nine months. It computes no fetal physiology, development, probability of birth, machine-control action or biological safety rating.

## Developmental scope

| Research stage | First-release treatment |
| --- | --- |
| Preimplantation development | Explicit gap in this bounded source ledger |
| Implantation and placental interface formation | Unresolved stage and interface requirement |
| Postimplantation embryonic development | Mouse interval retained in mouse developmental notation |
| Partial support of an already-developed fetus | Ovine reports and intended human clinical scope kept separate |
| Transition into neonatal life | Separate from duration on support |
| Developmental and longer-term outcomes | Separate from physiological stability and survival |
| Continuous human IVF-to-birth gestation | Undemonstrated ambition in this ledger |

Different studies and species cannot be concatenated to claim a continuous gestation pathway. [EVIDENCE.md](EVIDENCE.md) describes source classes and the important adverse-growth finding; [METHODS.md](METHODS.md) gives the equations, boundaries and reproducibility contract.

```mermaid
flowchart LR
    A[Complete ectogenesis research ambition] --> B[Developmental stages and unresolved transitions]
    A --> C[Placental exchange and interface questions]
    A --> D[Endocrine, immune and developmental unknowns]
    A --> E[Monitoring and long-term outcome evidence]
    A --> F[Resources and power continuity questions]
    F --> G[Dimensionless software fixture]
    E --> H[Evidence ledger]
    B --> H
    C --> H
    D --> H
```

This diagram organizes research questions; its arrows do not describe a demonstrated biological system or an assembly plan.

## ResearchDesk bridge

RegenWorkbench's `ectogenesis` blueprint provides normal source searches, evidence campaigns and dossier exports. This repository remains independently installable. `desk-status` makes one read-only request to the usual local `/api/state` endpoint and prints only the ectogenesis title, starter IDs and evidence-axis IDs. It accepts a numeric loopback HTTP(S) origin, disables proxies, refuses redirects, caps response size, and submits no jobs. Other notes and campaigns are neither printed nor written to disk.

A local ResearchDesk server can be inspected with the command above. Without that server, the two offline artifact commands still work. The bridge is research organization and source discovery; it has no live control API. Synthetic exchange outputs are not registered as biological assays or `experiment.json` records.

## Development and verification

From the parent shared workspace:

```powershell
docker compose run --rm dev bash -lc 'cd /workspace/artificial-womb-models && PYTHONPATH=src python3 -W error::ResourceWarning -m unittest discover -s tests -v'
```

On a host with Python, after installing the package:

```powershell
python -W error::ResourceWarning -m unittest discover -s tests -v
```

Tests cover analytic limits, balance conservation, outage and backup event boundaries, seeded reproducibility, malformed inputs, protected evidence gaps, species/stage separation, exclusive artifact publication and read-only local discovery. [ROADMAP.md](ROADMAP.md) describes useful next contributions.

The code is MIT licensed. Source papers retain their original rights; the ledger contains short attributed summaries and links, not redistributed article text or figures.
