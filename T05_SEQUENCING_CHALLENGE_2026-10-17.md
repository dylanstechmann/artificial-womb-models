# T05 sequencing challenge: defer the independent reviewer, prioritize whole-system in silico design

Date: 17 October 2026
Roadmap tasks: challenges T05, T06 and T11; registers T17 and decision D10
Status: owner-accepted challenge to the recorded sequencing
Contact: no authors, reviewers, institutions or other people contacted

## Owner decision

Designing a plausible whole working system in silico is a high priority. In silico design is not conditioned on the biological or clinical gates, which bind physical execution; nothing in the current evidence chain restricts what may be modeled, simulated or challenged offline, and the design work should proceed ambitiously rather than being trimmed to what is already demonstrated. Independent-reviewer recruitment is deferred — not cancelled — until there is a data-bearing artifact worth a specialist's attention. T05 stays held, T06 stays unsent, and this decision is recorded as D10 with new task T17.

## The challenge to the recorded position

The recorded position holds T05 for a genuinely independent reviewer and treats review as the next scarce resource, while in silico work beyond bounded fixtures is held (T11) as make-work. That sequencing is wrong at this time, for five reasons.

1. **The reviewer is being asked to certify an already-correctly-bounded negative result.** The T05 packet asks reviewers to adjudicate findings the repository already states: the eight candidate cards cannot answer the same-unit delivery/use/progression (D/M/P) question, the Song co-culture is bounded at its day-14 endpoint, and the LIPT1 example is endpoint separation only. No architecture is selected and no gate moves under any answer. The predictable verdict — accept the boundaries, return *insufficient* on the rest — adds almost no information.

2. **Reviewer attention is the scarcest, least-verified resource, and it would be spent at the point of lowest leverage.** No reviewer, facility or committed funding is identified (U13). Specialist attention that can eventually unlock controlled datasets and institutional routes should be spent once, on a data-rich claim or an acquisition decision — not twice, with the first spend certifying an empty-handed packet.

3. **The error-catching function of independent review has largely been performed by other means.** The provisional T05 challenge already caught the one real wording error (LIPT1), and byte-for-byte replay audits, pinned source hashes, bundle verification and the test suite check transcription and arithmetic more reliably than a human pass would. What remains for a human reviewer today is credibility certification, and credibility has nothing to unlock while every biological gate stays closed and nothing is published.

4. **The binding constraint is prospective measurement design, which an in silico lab produces and a reviewer cannot.** T02 established that existing data cannot answer the question, and the packet's own questions 1 and 4 ask what the smallest discriminating observation would be. That is a quantitative design question. The existing identifiability machinery already shows that even a two-compartment system is non-identifiable under plausible sampling `(e,d,ℓ) ≡ (2d,e/2,ℓ)`. A whole-system in silico design can compute whether D, M and P are separately estimable for each candidate measurement set, freeze the analysis plan on synthetic ground truth before real data exists, and convert the six-part T04 contract into a numeric minimum-measurement specification (compartments, timepoints, resolution, units per cohort) that a laboratory can quote and a reviewer can audit. A completed design analysis is itself "materially new" evidence under T05's own resumption condition.

5. **Allocate the verified resource, not the unverified one.** T07 measured local compute as abundant; reviewer capacity and physical measurement remain unverified. Holding the in silico option idle while waiting for an unverified reviewer inverts resource logic at the exact point where the program's own analysis says the bottleneck is design and measurement capability.

## What survives the challenge

- A reviewer still holds information a simulation cannot supply: knowledge of controlled datasets, institutional routes and access conditions (packet question 4). Deferral loses nothing here because no route is currently being pursued and no deadline moves a gate.
- Independent scrutiny is load-bearing before any human-use gate (G5/G6). Deferring it now delays no obligation, because no physical or human work is being started by this decision.
- One data-integrity rule travels with the in silico work: synthetic results are never registered as biological assays. That rule protects the evidence ledger, not the design ambition; it does not limit what may be designed or simulated.

## In silico design scope (T17)

Build on the existing modules — `exchange.py`, `developmental_models.py`, `state_estimation.py`, `transport_identifiability.py`, `design_sweep.py` and the machine-concept schematic renderer — toward one inspectable, plausible whole working system:

- a functional decomposition of the whole support path at the early exchange boundary, with the living-interface, staged and synthetic allocations instantiated as competing designs rather than prose;
- compartment, exchange, control and monitoring models covering the full support interval, with declared failure modes and fault-propagation behavior per allocated function;
- an identifiability-driven minimum-measurement specification: which same-unit measurements, at what sampling and resolution, would make D, M and P separately estimable and distinguish the three allocations;
- synthetic longitudinal same-unit fixtures run end-to-end through intake, validation, fitting and identifiability, so the analysis plan is frozen and pre-registered before any real or controlled dataset arrives;
- design sweeps that expose where the architectures genuinely diverge, so the next measurement or acquisition decision has a named discriminator.

## Roadmap disposition

- **T05 — remains held.** Status unchanged; reviewer recruitment deferred per D10. Resumption conditions unchanged: a genuinely independent reviewer or materially new source-linked evidence.
- **T06 — remains waiting_dependency.** The unsent packet is retained for the later review, which will receive a stronger artifact.
- **T11 — remains held.** GPU jobs, hardware and make-work sweeps stay held; whole-system design scope is authorized separately under T17.
- **T17 — registered, ready.** Whole-system in silico design; 16 aggregate agent-hour cap; acceptance and stop rule in the register.
- **D10 — recorded.** No biological gate advances. In silico design is engineering and method development, not biological evidence; physical execution and human-use gates are untouched by this document.
