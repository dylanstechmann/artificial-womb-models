# Project guidance

- Preserve the long-term ambition of complete human ectogenesis from IVF through birth while labeling achieved, reported, announced, prospective and unassessed capabilities separately.
- This repository contains evidence mapping and offline computational fixtures. Do not add donor collection or IVF procedures, embryo-culture instructions, animal surgery/trial protocols, device assembly, physiological setpoints, live hardware controls or clinical recommendations.
- Every numerical example is an artificial dimensionless software fixture unless a future explicitly reviewed data/model contract establishes otherwise. Do not silently assign biological units or equate runtime with gestational time.
- Keep species, actual developmental intervals, stage coverage, comparators, adverse outcomes and source classes distinct. Never concatenate studies into complete gestation evidence or infer fewer congenital defects from environmental control.
- Complete human gestation, surrogacy replacement and reduced congenital defects remain unassessed/undemonstrated in the initial ledger. Add human-reviewed primary evidence before revising such claims; do not upgrade an announcement, proposed trial or regulator discussion into a measured result.
- Do not produce readiness percentages, biological safety scores or lifetime benefit predictions from software fixtures. Oracle monitoring ground truth is unavailable in real deployment; label that limitation.
- Runtime uses Python standard library only. Inputs must remain bounded and must not select arbitrary code, hardware endpoints or remote control actions.
- Output destinations are exclusive. Publish receipt last, preserve exact inputs, hash source implementation and outputs, and reject malformed/nonfinite values. Do not register synthetic exchange results as biological assays.
- ResearchDesk is an optional loose bridge for normal searches, campaigns and dossiers. Local status discovery may export only ectogenesis blueprint metadata, not private notes/campaigns or credentials; do not submit jobs through it.
- Use the parent workspace `dev` Compose service for compatible test/build commands. Run meaningful tests for numerical limits, conservation, event boundaries, provenance/claim separation and malformed inputs after changes.
- CI sees only tracked files, and `artifacts/` is untracked. Before committing or pushing, run `python scripts/clean_checkout_tests.py`. A test that reads `artifacts/` must carry `requires_local_evidence` (`tests/local_evidence.py`), so a clean clone reports it as skipped. Pinned SHA-256 values and byte sizes must hold on the committed bytes: `.gitattributes` keeps `config/observations`, `config/perfusion_observations` and `config/source_inventories` byte-exact, so hash those files as they are, not after a line-ending change.
- Update `tests/test_program_status.py` pinned structural spot-checks in the same change as any `config/program/roadmap.json` status or dependency edit; eligibility itself is derived, not hardcoded.
- Work in this repository's own Git history. Do not push, publish or commit another repository's changes without the user's task authorization.

## Agent tooling (portable across harnesses)

<!-- agent-toolbox:installed -->

This repo vendors its agent tooling (no secrets inside) so Claude Code,
Cline, Codex, OpenCode, Kilo Code, Kimi Code and Grok share one setup:

- `.mcp.json` — project MCP servers `scholar` (PubMed, OpenAlex, Semantic
  Scholar, CORE, ORCID, Crossref) and `web` (Exa, Brave, Jina, Firecrawl).
- `opencode.json` — same servers for OpenCode; `AGENT_TOOLS.md` has the
  merge snippets for Codex / Cline / Kilo Code and notes for Kimi/Grok.
- `.claude/skills/` — project skills: citation-check, literature-search, web-research, secrets-guard, regen-guardrails, fold-providers.
- Keys: `~/.config/ai-keys.env` via the `agentkeys` loader — never in git,
  MCP config or chat. Run `secrets-guard` (`--staged`) before committing.
