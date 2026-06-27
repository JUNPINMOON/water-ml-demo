# PUSH_INSTRUCTIONS.md

Nothing was auto-pushed. Main is untouched. The decision is yours.

---

## Current state

Branch: `claude/nervous-poincare-eac901`

Recent commits on this branch:
```
db9c881 Recruiter-facing README rewrite + 1-page CASE_NOTE (honest, results-first)
a407572 Streamflow forecasting demo: LightGBM on USGS + NASA POWER (NSE 0.94 / KGE 0.92, leave-one-basin-out eval)
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
