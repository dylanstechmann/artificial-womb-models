# Human fetal circulation waveform benchmarks

Codex ran these analyses for a personal research project. Human scientific review is pending. The observations are in-utero fetal Doppler traces. The numerical replay is an offline circulation model, and both are separate from the repository's dimensionless support simulations. [Villanueva-Baxarias et al.](https://doi.org/10.1371/journal.pcbi.1013096) · [Archived model](https://doi.org/10.5281/zenodo.14826951)

## Participant-held-out baseline

Seven folds each withheld all eight traces from one participant. For each site, a template averaged the other six participants at each of 201 evenly spaced phase coordinates. A flat baseline used the phase-weighted average of that same training template. The template had lower root-mean-square error (RMSE) on **all 56 held-out traces**. Median RMSE across participants ranged from **4.05 cm/s in the middle cerebral artery** to **14.58 cm/s in the ductus arteriosus**. The ductus also had the largest median absolute peak error, 20.58 cm/s. The 56 comparisons share seven participants, and the folds reuse training participants. [Site results](doppler/by-site.tsv) · [Receipt](doppler/receipt.json) · [Publisher S2 data](https://doi.org/10.1371/journal.pcbi.1013096.s003)

The analysis rescaled each exported time span to phase 0–1 and interpolated linearly. It used the measured start and end of each trace, with no fitted time shift. All 28 equal timestamps had velocity differences under 10⁻¹⁰ cm/s and were collapsed. Signed velocities and distinct endpoints were retained. Errors weighted phase intervals equally by the trapezoid rule. Peak error compares maxima on that same phase grid. Sites were recorded with different trace spans, so phase coordinates describe each exported trace individually.

## What the publication and archive reproduce

The authors used all seven controls to tune the healthy model. Their Figure 2 therefore compares with its fitting cohort. The study's nine coarctation cases contributed anatomy measurements to a separate analysis. S2 contains the healthy waveforms, and S1 contains case-level scalar measurements. [Study methods and Figure 2](https://doi.org/10.1371/journal.pcbi.1013096) · [Publisher S1 data](https://doi.org/10.1371/journal.pcbi.1013096.s002)

**Published figure.** The analysis recovered the black simulated centerline at 723 pixel columns per site over phase 0.02–0.98. The visible green mean agreed with the reconstructed S2 mean within 0.65 cm/s RMSE at every site. Varying the black-pixel threshold moved the estimated curve center by at most 0.97 cm/s. The published model's agreement with the S2 mean varied by site, from **3.47 cm/s RMSE at the umbilical artery** to **18.39 cm/s at the aortic isthmus**. These numbers describe agreement with fitted observations, and the raster limits precision. [Published plot](https://doi.org/10.1371/journal.pcbi.1013096.g002) · [Figure comparison](doppler-figure/by-site.tsv)

**Archived equations.** The archive contains the C equations. The scenario driver expects a different C filename, and the plotting notebook expects numerical result arrays absent from the archive. The healthy replay compiled the archived C and integrated the default initial state using SciPy BDF and Radau. It used the notebook's Figure 4 site conversions and its left ventricular valve-opening phase convention. The score uses the same interior phases as the Figure 2 audit. The two solvers agreed within 0.0004 cm/s and the preceding cycle differed by at most 0.040 cm/s at the scored points. Six sites had replay-to-figure RMSE between 0.74 and 3.52 cm/s. The mitral and tricuspid valves had RMSE of 21.63 and 22.83 cm/s, and both replay peaks occurred about 0.10 cycle earlier. The tricuspid peak reached 53.78 cm/s in the replay and 65.08 cm/s in the figure. These differences make the Figure 2 alignment and velocity conversions specific targets for resolving the discrepancy. This replay covers the healthy default equations. [Replay comparison](coa-replay/by-site.tsv) · [Archived plotting code](https://github.com/InmaV/CoA_scenarios/blob/5597e52fda7c1f2385a05bef41912ecf10b23142/Read_results.ipynb) · [Solver documentation](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.integrate.solve_ivp.html)

## Independent measurement to connect next

Roberts et al. published a separate 4D MRI workbook with nine volumetric-flow waveforms in mL/min/kg. Figure 6a has 25 frames each at the ascending aorta, descending aorta, main pulmonary artery and superior vena cava in a healthy fetus at 24 weeks 2 days. Figure 6b has 25 frames each at the same four sites and the ductus arteriosus in a fetus with a right aortic arch at 32 weeks 3 days. The published MRI frames were reconstructed from acquisitions with 72 ms temporal resolution. This source can test selected volumetric-flow outputs after matching the cross section and accounting for gestational age, anatomy and measurement differences. Doppler envelope velocity in cm/s is a separate observable. [Roberts et al.](https://doi.org/10.1038/s41467-020-18790-1) · [Source workbook](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-020-18790-1/MediaObjects/41467_2020_18790_MOESM10_ESM.xlsx)

The 23,630-byte workbook has SHA-256 `91d6674b1526924219551f82e1454e0772bda9b99c0081fa849161af539d72f3`. The time-course sheets agree with the publication's site labels. In the Figure 6c summary sheet, the workbook headers for columns B–F are AAo, DA, DAo, MPA and SVC. Column counts (26, 27, 28, 28, 23) and means (140.50, 126.59, 169.96, 75.57, 72.61 mL/min/kg) match the publication in the order AAo, DAo, MPA, SVC and DA. This inferred labeling discrepancy remains open. Figure 6c pools repeated readings from seven fetuses, and its columns lack a case linkage suitable for held-out scoring. [Figure and counts](https://www.nature.com/articles/s41467-020-18790-1/figures/6) · [Author correction](https://doi.org/10.1038/s41467-020-20353-3)

| MRI observable | Candidate model output |
| --- | --- |
| Ascending aorta (AAo) | `AA_RCL.Qo` |
| Descending aorta (DAo) | `Bif_DA1in_AI2in_AOout.Qo` at the ductal–isthmus confluence |
| Main pulmonary artery (MPA) | `PA_RCL.Qo` |
| Superior vena cava (SVC) | `SVC_RCL.Qo` |
| Ductus arteriosus (DA) | `Bif_PAin_LUNG1out_DA2out.Qo2` |

These candidate mappings follow the model topology and require checking the MRI region of interest before scoring. The model's volumetric outputs use mL/s. Normalization to mL/min/kg would use the model's own mass at its stated gestational age, with the MRI values already normalized. A cross-cohort comparison has yet to be run. [Model source](https://github.com/InmaV/CoA_scenarios/blob/5597e52fda7c1f2385a05bef41912ecf10b23142/FETAL_MODEL_CoA.c) · [Model supplement](https://doi.org/10.1371/journal.pcbi.1013096.s001)

## Reproduce the results

Run from the repository root. The baseline runs with standard-library Python 3.10 or newer. The figure and replay commands below use Python 3.12 in a separate local environment, and the C replay also needs a C compiler. Source files stay in the ignored artifacts directory and each run takes a fresh output path. Reuse `artifacts/public-inputs-v2` if you already fetched it. The receipts pin the input and implementation hashes.

```sh
python3 studies/public-evidence/fetch_inputs.py artifacts/public-inputs-v2
python3 studies/public-evidence/doppler_benchmark.py artifacts/public-inputs-v2/Dataset_S2.csv artifacts/doppler
python3.12 -m venv artifacts/coa-env
artifacts/coa-env/bin/python -m pip install numpy==2.4.6 scipy==1.15.3 pillow==11.3.0
mkdir -p artifacts/coa-sources
curl -fL 'https://journals.plos.org/ploscompbiol/article/figure/image?size=large&id=10.1371/journal.pcbi.1013096.g002' -o artifacts/coa-sources/coa-figure-2.png
curl -fL 'https://raw.githubusercontent.com/InmaV/CoA_scenarios/5597e52fda7c1f2385a05bef41912ecf10b23142/FETAL_MODEL_CoA.c' -o artifacts/coa-sources/FETAL_MODEL_CoA.c
artifacts/coa-env/bin/python studies/public-evidence/doppler_figure.py artifacts/public-inputs-v2/Dataset_S2.csv artifacts/coa-sources/coa-figure-2.png artifacts/doppler-figure
OPENBLAS_NUM_THREADS=1 artifacts/coa-env/bin/python studies/public-evidence/coa_replay.py artifacts/coa-sources/FETAL_MODEL_CoA.c artifacts/coa-sources/coa-figure-2.png artifacts/coa-replay
```

With those inputs in place, the local study tests rerun both analyses and check the eight velocity mappings. The model replay takes a few minutes.

```sh
artifacts/coa-env/bin/python -m unittest discover -s tests -p test_public_study_collection.py -v
```
