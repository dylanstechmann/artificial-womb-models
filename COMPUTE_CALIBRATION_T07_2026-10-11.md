# T07 local compute calibration

Date: 2026-10-11  
Roadmap task: T07, “Early compute calibration and conditional job design”  
Calibration cycle: 348

## Result

Five representative local task types completed successfully. Their combined subprocess wall time was **0.967892 seconds**. Individual runs ranged from 0.154572 to 0.230441 seconds. These timings include Python startup and local file access, come from one run per task, and are not a repeatable performance benchmark.

| Task type | Elapsed wall time | Acceptance |
| --- | ---: | --- |
| Usuda source-audit extraction and bundle publication | 0.166086 s | Exit 0; output created in a fresh exclusive directory |
| Program-status render | 0.206344 s | Exit 0; output created in a fresh exclusive directory |
| Strict verification of the Usuda bundle | 0.210449 s | `bytes_verified=true`; no errors or warnings |
| Strict verification of the program-status bundle | 0.230441 s | `bytes_verified=true`; no errors or warnings |
| Rejection of a malformed nonfinite summary | 0.154572 s | Expected `InputError` was caught |

The strict verifier reports byte integrity only; it explicitly leaves scientific review unestablished and reproduction not attempted. The source audit remains an agent-assisted source transcription candidate. No biological or hardware capability was tested.

## Resource observations and decision

The local process reported Python 3.11.15 on Windows 10 and 16 logical CPUs. The five jobs were short, CPU-oriented evidence and reporting tools. GPU telemetry was not inspected. This environment did not expose ChatGPT/Codex account usage or trustworthy sum-agent-hours, so neither is estimated here; the owner’s 24–48 AI-hours/week planning figure remains unverified.

This sample shows no local compute bottleneck for these task types. It does not measure large image, omics, molecular, or biological-model workloads. A scheduler, checkpointing layer, GPU purchase, or long-running job is therefore **deferred** until a named, eligible analysis has a measured duration or resumability need. More compute cannot address missing source-linked observations, independent review, or physical measurement capability.

The command-level record is in [COMPUTE_CALIBRATION_T07_MEASUREMENTS_2026-10-11.json](COMPUTE_CALIBRATION_T07_MEASUREMENTS_2026-10-11.json). It records commands using project-relative paths, exit codes, timings, and acceptance details. The Usuda source SHA-256 was `553bb25875e95db787249c60bab779dc05aebb32f341dce27b3f1c7405430e0a`.

## Next decision

Keep the current compute allocation; do not buy a GPU or add a scheduler based on this evidence. Continue with a named source/observation-intake task that can improve evidence quality or reveal a genuine data-processing bottleneck. Reopen T07 only if an accepted workload needs extended execution, deterministic resume, or account usage data shows a real constraint.