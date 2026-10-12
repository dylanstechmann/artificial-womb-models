# Program register workflow

Read `PROGRAM_PLAN.md` before selecting a task. `roadmap.json` records declared gates, requirements, milestones, accepted contributions, uncertainties, effort caps and prerequisites. `PROGRAM_STATUS.md` at the project root is a reviewed copy of the most recent generated view, not a live service.

For each cycle, record the original task contract, decision consequence and novelty relative to previous work. Preserve exact inputs and outputs in a new artifact directory. Record actual effort, result, remaining uncertainty and acceptance review. A time cap produces a partial checkpoint, never automatic completion. Explicitly release a waiting task to `ready` only after its prerequisites and work contract have been reviewed.

Completed items require project-relative evidence paths and exact SHA-256 values. Update a pin only after inspecting and accepting the changed evidence; refreshing all hashes blindly would hide a stale assessment. The report checks evidence bytes and the full task dependency chain. It cannot judge whether a file actually satisfies its acceptance criteria, authenticate scientific review, or promote a biological/clinical gate.

From the parent workspace, generate a new status bundle (choose an unused output directory for each run):

```powershell
docker compose run --rm -T -w /workspace/artificial-womb-models dev env PYTHONPATH=src python3 -m wombmodels.program_status --register config/program/roadmap.json --root . --out artifacts/program-status-review-001
```

Verify the bundle with the existing strict bundle verification workflow, inspect the view and original acceptance conditions, then copy its `PROGRAM_STATUS.md` to the project root. Preserve the source bundle and receipt. Its reproduction plan requires the pinned external local evidence files as well as the exact saved register. Byte verification and rerunning are separate claims.

The original baseline is `artifacts/program-plan-baseline-2026-10-11/status`. Version two is `artifacts/program-scope-revision-2026-10-11/status`; `prior-v1/` preserves the earlier plan, register, view and reporting implementation. M01 pins the reviewed current plan/tool; T12 pins the owner-scope crosswalk. The generated bundle pins the exact input register and status output without self-referential hashes. Future records must retain species, stage, all-start denominator, adverse outcomes, source class and review boundaries. Owned equipment, ten simultaneous gestations and actual common-date outcomes cannot be replaced by service access or sequential success.

Version three is `artifacts/program-five-year-target-2026-10-11/status`; `prior-v2/` preserves its preceding plan, register and status view. It recorded the earlier five-year owner target.

Version four is `artifacts/program-acceleration-2026-10-11/status`; `prior-v3/` preserves the previous plan, register, view and task-eligibility test. The owner now strongly prefers the earliest outcome, within two to three years or sooner; five years is a comparison scenario and ten years may be tolerable. `planning_calendar` contains proposed short work/decision targets, not validated biological durations or scheduled jobs. T08 resource preparation is ready alongside T01/T16. T05 requires T04 and claim-relevant reproduction evidence, rather than an unrelated generic T03 rerun. Preparation and review do not authorize acquisition or advance biological gates. A completion forecast remains unestablished.

Do not contact authors or other people. This workflow creates no recurring schedule, hardware control, biological procedure or clinical authorization.
