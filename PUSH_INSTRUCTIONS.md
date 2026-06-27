# PUSH_INSTRUCTIONS.md

Nothing was auto-pushed. Main is untouched. The decision is yours.

> **Note (outreach/resume docs):** The resume and outreach deliverables (in connect-ai-runtime, outside this repo) are finalized — the HEC-RAS/SWMM wording has been corrected to "input/output workflow automation" (not engine development). This repo's own content (README, CASE_NOTE, notebooks) is unchanged by that correction. Once you push this repo public, you can immediately attach **github.com/JUNPINMOON/water-ml-demo** as the CAMELS portfolio link in those documents.

---

## Current state

Branch: `claude/nervous-poincare-eac901`

Recent commits on this branch (run `git log --oneline -5` for the live list):
```
<newest>  Refresh PUSH_INSTRUCTIONS: accurate commit list + public repo URL
423f093  Add PUSH_INSTRUCTIONS.md: human-follow-only merge/push/discard guide
db9c881  Recruiter-facing README rewrite + 1-page CASE_NOTE (honest, results-first)
a407572  Streamflow forecasting demo: LightGBM on USGS + NASA POWER (NSE 0.94 / KGE 0.92, leave-one-basin-out eval)
```

---

## Step 1 — Review before deciding

From the **main repo root** (`C:\Users\mjb58\antigravity-projects\water-ml-demo`), run:

```bash
git diff main..claude/nervous-poincare-eac901
```

This shows every change that would be added to main if you merge.

---

## Step 2a — Merge to main (if you want to keep the changes)

```bash
# From the main repo root (NOT the worktree path)
cd C:\Users\mjb58\antigravity-projects\water-ml-demo

git switch main
git merge claude/nervous-poincare-eac901
```

---

## Step 3 — Push to remote (choose one)

**Option A — GitHub CLI (no remote configured yet):**
```bash
gh repo create water-ml-demo --public --source . --push
```
This creates **github.com/JUNPINMOON/water-ml-demo** (authenticated account = JUNPINMOON).
Use this URL as the CAMELS portfolio link in your resume, gig proposals, and cold pitches.

**Option B — existing origin already configured:**
```bash
git push -u origin main
```

---

## Step 2b — Discard (if you do NOT want these changes)

```bash
# Remove the worktree (run from main repo root)
git worktree remove "C:\Users\mjb58\antigravity-projects\water-ml-demo\.claude\worktrees\nervous-poincare-eac901"

# Then delete the branch
git branch -D claude/nervous-poincare-eac901
```

---

## Notes

- No automatic push was performed.
- `main` is untouched — none of the new commits landed there.
- The worktree at `.claude/worktrees/nervous-poincare-eac901` is isolated.
- All decisions (merge, push, discard) are yours to make manually.
