# T27 reciprocal coupling qualification (2026-10-24)

This AI-assisted software qualification tests one proposed, invented dimensionless feedback law:

```text
bulk_stock' -= leak_coefficient * wall_damage * bulk_stock
```

It asks whether a damage-dependent bulk loss can make boundary bulk-stock trajectories distinguish variants in the existing whole-path fixture. The wall observer is the T23 Kelvin–Voigt software abstraction; damage is advanced over canonical fluidic RK4 substeps and held for the corresponding fluidic derivative evaluations. This is an operator-split numerical coupling, not an inferred physical mechanism.

The CLI entry is `wombmodels reciprocal-twin-model --config examples/reciprocal_twin_fixture.json --out <new-directory>`. The fixture and implementation are dimensionless, synthetic, and offline. The test suite compares every shared zero-feedback trajectory column with T23, checks boundary separation against a zero-feedback baseline for the stated fixture, checks deterministic publication, and verifies publication integrity.

An independent constant-damage case starts with nonzero stock, disables delivery and supplemental feedback, and compares the canonical solver with `stock(t) = stock(0) exp(-(washout + transfer + leak_coefficient * damage) t)`. Refining 10, 20 and 40 substeps checks this isolated leak calculation. This is not a convergence qualification of the full damage-evolving reciprocal system.

## Limits

- The feedback coefficient and damage-gated law are invented software parameters, not measured leak behavior.
- Wall damage is accounting, not fatigue, injury, rupture, or a biological prediction.
- Fixture separation is not a cohort result, sampling requirement, capability ranking, or calibrated observation claim.
- No physiological calibration, biological measurement, hardware action, procurement, or gate movement is established.
- The zero-feedback test establishes trajectory equality for the tested fixture only; it does not qualify every allowed configuration.
- Feedback uses beginning-of-substep damage, so the full reciprocal coupling is first-order operator splitting even though each held-damage fluidic substep uses RK4. Full-system step-refinement qualification remains outstanding.
- The existing fluidic rate schedule does not include a damage-dependent leak stiffness bound. The coefficient limit alone is not an accuracy or stability guarantee for arbitrary configurations.