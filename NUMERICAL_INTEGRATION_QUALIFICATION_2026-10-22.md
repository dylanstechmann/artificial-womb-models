# Numerical integration qualification (T26, 2026-10-22)

Artificial dimensionless software fixture; no physiological calibration, biological prediction or machine-control output.

AI-assisted software correction and numerical checks. The owner selected numerical integration stability as the next task. No biological evidence, physical calibration or gate completion is inferred.

## Corrected behavior

- Growth-scaling, growth-mechanics and twin RK4 steps now advance their internal clock.
- All five fixture solvers integrate the actual terminal time, using a shortened final interval when necessary; decimal grids such as 0.3/0.1 no longer truncate the trajectory.
- One canonical fluidic solver serves both twins. It splits steps at outage boundaries and reserve exhaustion, holds the power mode through all RK stages, and accounts for reserve draw analytically. Output observations use the mode at their timestamp.
- The wall alone subcycles against a maximum stiffness/viscosity bound. Its forcing uses a cubic continuous extension of the fluidic RK4 stages, third order inside each fluidic step and matching its endpoints. No interpolation crosses a power event, and wall refinement changes neither fluidic arithmetic nor random draws.
- The fluidic bound includes repair. Each fluidic/wall run permits at most 4,000,000 substeps; excessive work and nonfinite states fail before bundle publication.
- Spatial comparison chains share a rate bound and substep schedule. A fast hidden compartment cannot create an observed-prefix difference through numerical rounding.
- Acquisition surveillance counts include the shortened final interval.

## Independent references

With demand D(t)=D0*(1+g*t), no losses/control and full request, bulk(t)=D0*(t+g*t^2/2). This checks advancing clocks and terminal-time accounting.

For a wall with load L(t)=L0*(1+g*t), constant stiffness E, viscosity eta and initial strain L0/E, the exact strain is

```text
strain(t) = L0/E*(1+g*t) - eta*L0*g/E^2*(1-exp(-E*t/eta))
```

The growth-wall test uses L0=E=eta=1, g=0.25 and t=3. The coupled-wall reference instead uses constant delivery, bulk=t and load=t+0.4, giving strain(t)=0.4+t-(1-exp(-t)). Control, noise and outages are disabled in refinement cases so changing the grid does not change the sampled input.

| Output step | Growth wall absolute error at t=3 | Coupled wall absolute error at t=3 |
| ---: | ---: | ---: |
| 0.75 | 4.49797909e-07 | 1.79919163e-06 |
| 0.25 | 8.43225822e-08 | 3.37290328e-07 |
| 0.0625 | 5.00210717e-09 | 2.00084296e-08 |

Both errors decrease at each refinement. The distinct output steps produce distinct internal resolutions rather than accidentally reusing the same substep size.

A separate coupled-wall case with relaxation rate 1,000 has maximum absolute error 1.66533454e-16 against its exact ramp solution. Every recorded state is finite; all fluidic columns equal the standalone twin exactly.

For an outage from t=0.15 to 0.85, reserve 0.2, draw 1 and backup fraction 0.5, the supply integral is 0.15+0.2*0.5+0.15=0.4. The solver obtains 0.39999999999999997 with reserve zero. This tests reserve exhaustion between output samples and power restoration without RK endpoint leakage.

## Reproduction and scope

The fifteen regression cases are tracked in [test_integration_stability.py](tests/test_integration_stability.py). Run from the repository using the parent workspace dev Compose service:

```text
python -W error::ResourceWarning -m unittest tests.test_integration_stability
```

They also check malformed numerical execution and work limits fail without an output directory, a short terminal interval is counted downstream, and shared spatial observations remain exactly equal when a hidden use rate is raised to 100. Existing modeling and bundle-integrity tests remain applicable.

Passing these cases qualifies the stated software behaviors only. It is not a proof of accuracy for every allowed configuration. Wall subcycling retains fluidic discretization/interpolation error; finer wall steps alone cannot remove it. The sampled controller is tied to the output grid, so convergence comparisons with it enabled require a separate fixed input-sampling contract. Damage accounting and threshold crossing times retain their fixture/output-grid definitions. Work preflight is conservative for shortened intervals. Historical T19-T25 numbers describe their original runs; reruns carry the corrected implementation hashes. No synthetic result is registered as a biological assay.
