# T27 reciprocal coupling qualification (2026-10-24)

This AI-assisted software qualification tests one proposed, invented dimensionless feedback law:

```text
bulk_stock' -= leak_coefficient * wall_damage * bulk_stock
```

It asks whether a damage-dependent bulk loss can make boundary bulk-stock trajectories distinguish variants in the existing whole-path fixture. The wall observer is the T23 Kelvin–Voigt software abstraction; damage is advanced over canonical fluidic RK4 substeps and held for the corresponding fluidic derivative evaluations. This is an operator-split numerical coupling, not an inferred physical mechanism.

The CLI entry is `wombmodels reciprocal-twin-model --config examples/reciprocal_twin_fixture.json --out <new-directory>`. The fixture and implementation are dimensionless, synthetic, and offline. Each nonzero-feedback run also computes a zero-feedback baseline and publishes `feedback_only_first_separated`, separating the proposed leak's effect from pre-existing mechanical and internal signatures. The test suite compares every shared zero-feedback trajectory column with T23, checks deterministic publication and work-budget failure without partial output, and verifies publication integrity.

An independent constant-damage case starts with nonzero stock, disables delivery and supplemental feedback, and compares the canonical solver with `stock(t) = stock(0) exp(-(washout + transfer + leak_coefficient * damage) t)`. Refining 10, 20 and 40 substeps checks this isolated leak calculation.

A separate full-system regression disables controller/noise variation and uses evolving damage with nonzero leakage. For each of the three variants, refining the shared event-free schedule by 1, 2, 4 and 8 reduces successive terminal bulk-stock and damage differences by approximately one half, consistent with first-order operator splitting. The schedule includes a conservative leak-rate bound derived from the validated delivery/stock envelope, wall strain envelope, damage rate and duration. Refinement also applies to shortened event-free segments and counts toward the existing work budget. These checks qualify the stated regression behavior, not every allowed configuration.

## Limits

- The feedback coefficient and damage-gated law are invented software parameters, not measured leak behavior.
- Wall damage is accounting, not fatigue, injury, rupture, or a biological prediction.
- Fixture separation is not a cohort result, sampling requirement, capability ranking, or calibrated observation claim.
- No physiological calibration, biological measurement, hardware action, procurement, or gate movement is established.
- The zero-feedback test establishes trajectory equality for the tested fixture only; it does not qualify every allowed configuration.
- Feedback uses beginning-of-substep damage, so the full reciprocal coupling is first-order operator splitting even though each held-damage fluidic substep uses RK4. Full-system refinement is qualified only for the stated regression case.
- The conservative damage-dependent rate bound and work budget do not guarantee numerical accuracy for arbitrary configurations.