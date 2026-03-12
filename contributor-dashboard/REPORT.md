# OpenClaw Contributor Intelligence — Written Report
**Project:** Contributor Intelligence Dashboard + LLM Autorater  
**Repo:** [asraniket/openclaw](https://github.com/asraniket/openclaw)  
**Branch:** candidate/asraniket  
---
## 1. Dashboard Overview
The dashboard pulls live data from the OpenClaw GitHub repository and presents
contributor activity across four dimensions — volume, recency, scope, and
LLM-rated impact. All data is real, fetched directly from the GitHub API and
processed through a local pipeline.
**Key stats from the data:**
| Metric | Value |
|--------|-------|
| Total contributors | 18,904 |
| Total commits | 17,506 |
| Total PRs merged | 3,136 |
| Total reviews recorded | 209 |
| Contributors active in last 90 days | 966 |
The dashboard is organized into four tabs:
- **Volume** — who contributed what and how much (commits, PRs, issues, reviews, comments)
- **Recency** — recent vs historic activity to identify who is still active
- **Scope** — which directories and files each contributor touches, powered by `git log`
- **Autorater** — LLM-generated structured impact scores alongside raw metrics
---
## 2. Rating Schema — Design and Reasoning
### Why I didn't use commit count as the primary signal
The most obvious metric — commit count — is also the most misleading. `steipete`
has 11,801 commits, which is 27× more than the second-highest contributor. But
raw commit count conflates meaningful architectural changes with one-line typo
fixes, version bumps, and formatting runs. A contributor with 50 well-scoped,
impactful PRs is more valuable than one with 500 trivial commits.
I designed the autorater to measure **impact**, not volume. The four dimensions
and their weights are:
---
### Dimension 1 — Code Quality (weight: 30%)
**What it measures:** Is the actual code change clean, well-scoped, and
thoughtfully written? Does the diff suggest the contributor understands what
they're changing, or are they making broad sweeping edits without clear intent?
**Why 30%:** Code quality is the most direct signal of engineering skill. A
contributor who writes clean, minimal, well-structured diffs consistently
demonstrates mastery of the codebase. This is weighted highest alongside
problem significance because both directly measure the quality of output
rather than the quantity.
**How the LLM evaluates it:** The prompt includes truncated PR diffs alongside
titles and descriptions. The model looks for: single-responsibility changes,
descriptive naming, absence of unrelated edits, and evidence of testing
or documentation where appropriate.
---
### Dimension 2 — Problem Significance (weight: 30%)
**What it measures:** Does the PR address something that actually matters?
A real bug that affected users, a meaningful new feature, a performance
improvement with measurable impact — or is it a cosmetic change, a dependency
bump, or a config tweak that required no real thought?
**Why 30%:** Open source health depends on whether contributors are moving
the project forward. Drive-by contributors often fix typos or update
documentation because it's low friction — that's valuable, but it's not
the same as shipping a channel integration or fixing a critical memory leak.
Equal weight to code quality because a perfectly clean diff of a trivial
change is still less valuable than a slightly rough fix of a critical bug.
**How the LLM evaluates it:** The model reads the PR title and body for
signals like "fixes #issue", "closes bug where...", "adds support for...",
or "improves performance of...". It looks at the diff to verify the change
matches the description.
---
### Dimension 3 — Review Engagement (weight: 20%)
**What it measures:** Do they review other contributors' PRs, and do they
give substantive feedback — or do they only submit their own code and never
engage with the broader community?
**Why 20%:** Review engagement is a strong signal of project ownership and
community health. A contributor who reviews PRs is investing in the project
beyond their own work. However, this dimension is weighted lower (20%) because
review data from the GitHub API is limited — we only have reviews for the first
100 PRs, which under-counts reviewers. To compensate, the model also looks at
the `reviews_given` and `comments_made` counts from the full dataset.
**How the LLM evaluates it:** Primarily uses the `reviews_given` stat.
A score of 0 reviews across hundreds of PRs is penalized. High review counts
relative to PR output is rewarded.
---
### Dimension 4 — Consistency (weight: 20%)
**What it measures:** Is the contributor reliable over time, or did they
have a single burst of activity (e.g., one week of PRs, then nothing)?
Consistency predicts future contribution and signals genuine project investment
versus opportunistic one-time engagement.
**Why 20%:** Consistency matters for project health but is already partially
captured by commit recency data in the dashboard. It's weighted lower because
a contributor who was extremely active for six months and then took a break is
still highly valuable — penalizing them too heavily for reduced recent activity
would be unfair.
**How the LLM evaluates it:** Uses `first_contribution`, `last_contribution`,
`recent_commits` vs `historic_commits`, and the total time span of activity.
A contributor active over 12+ months scores higher than one with the same
total commits compressed into two weeks.
---
### Overall Score Formula
```
overall = (code_quality × 0.3) + (problem_significance × 0.3)
        + (review_engagement × 0.2) + (consistency × 0.2)
```
### Tier Classification
| Tier | Criteria |
|------|----------|
| Core Maintainer | overall ≥ 3.5 |
| Active Contributor | overall 2.5–3.5 |
| Occasional Contributor | overall 1.5–2.5 |
| Drive-by Contributor | overall < 1.5 |
---
## 3. Autorater Results
| Contributor | Overall | Tier | Code Quality | Problem Sig. | Reviews | Consistency |
|-------------|---------|------|-------------|-------------|---------|-------------|
| steipete | 3.7 | Core Maintainer | 4 | 4 | 1 | 5 |
| mbelinky | 3.5 | Active Contributor | 4 | 4 | 1 | 4 |
| shakkernerd | 3.5 | Active Contributor | 4 | 5 | 1 | 3 |
| sebslight | 3.2 | Active Contributor | 4 | 3 | 1 | 4 |
| thewilloftheshadow | 3.2 | Active Contributor | 4 | 4 | 1 | 3 |
| vincentkoc | 3.1 | Active Contributor | 4 | 4 | 1 | 3 |
| vignesh07 | 3.1 | Active Contributor | 4 | 4 | 1 | 3 |
| gumadeiras | 3.1 | Active Contributor | 4 | 4 | 1 | 3 |
| obviyus | 3.1 | Active Contributor | 4 | 4 | 1 | 3 |
| Takhoffman | 3.1 | Active Contributor | 4 | 4 | 1 | 3 |
| tyler6204 | 3.1 | Active Contributor | 4 | 4 | 1 | 3 |
| joshavant | 3.1 | Active Contributor | 4 | 4 | 1 | 3 |
| joshp123 | 3.1 | Active Contributor | 4 | 4 | 1 | 3 |
| Sid-Qin | 2.9 | Occasional Contributor | 4 | 4 | 1 | 2 |
| cpojer | 2.1 | Occasional Contributor | 3 | 2 | 1 | 2 |
---
## 4. Interesting Findings
### Finding 1 — The project has an extreme bus factor problem
`steipete` alone accounts for **11,801 out of 17,506 commits** — that is **67.4%
of all commits in the entire project history**. The next highest contributor
(`vignesh07`) has 436 commits, which is 96% fewer. If `steipete` stopped
contributing tomorrow, the project would lose its primary architect, most
active reviewer, and the person who understands the broadest swath of the
codebase. This is a critical single point of failure for the project.
This was the most surprising finding — even for a project with one dominant
founder, a 67% concentration is unusually high.
---
### Finding 2 — High commit count does not predict high impact score
`cpojer` ranked 8th by commit count (156 commits) but received the lowest
autorater score (2.1, Occasional Contributor). Looking at the data: only 3
PRs merged out of 8 opened, very few comments, and low review engagement.
The commits appear to be from an early burst of activity that did not sustain.
Conversely, `Takhoffman` ranked 9th by commits (121) but had 85 PRs merged —
a 87% merge rate — and received a 3.1 score. Fewer commits, more meaningful
output. This validates the core design decision to rate impact rather than volume.
---
### Finding 3 — Almost no one reviews other people's PRs
Across all 15 rated contributors, `reviews_given` is 0 for nearly everyone
based on the reviews captured (first 100 PRs). `steipete` is the exception
with the highest review activity, but even his review engagement score is 1
because the volume of PRs he reviews relative to his role as maintainer is
still lower than expected. This creates a review bottleneck — one person is
responsible for merging the vast majority of community PRs.
---
### Finding 4 — Most contributors are very recent (project age vs contributor age)
966 out of 18,904 contributors (5.1%) made a commit in the last 90 days.
But the data also shows that most contributors have a `first_contribution`
date from late 2025 or early 2026 — meaning the vast majority of the
contributor base joined in the last few months. This suggests the project
is in a rapid growth phase, not a mature steady state. The bus factor risk
is amplified because most contributors haven't had time to build deep
codebase knowledge yet.
---
### Finding 5 — `vincentkoc` has the highest PR merge rate among top contributors
`vincentkoc` opened 295 PRs and had 228 merged — a **77% merge rate**, the
highest among the top contributors. Despite having fewer commits than
`steipete`, `vignesh07`, or `obviyus`, this contributor's work is accepted
at the highest rate, suggesting consistently well-scoped and clean contributions.
The autorater confirms this with a code quality score of 4. This is a hidden
gem contributor that raw commit counts would miss entirely.
---
## 5. Limitations of the Autorater
### Limitation 1 — Diff truncation hides large architectural changes
PR diffs are truncated to 1,000 characters due to token limits. A contributor
who makes a 2,000-line architectural refactor looks identical in the prompt
to one who makes a 50-line fix. The LLM cannot see the full scope of large
changes, which likely causes it to under-rate contributors who tackle complex,
large-scale work. This is the most significant limitation.
### Limitation 2 — Review data is severely undersampled
We only fetched reviews for the first 100 PRs out of 9,000+. This means
the `reviews_given` count in the contributor profiles is almost always 0,
which causes the LLM to score review engagement as 1 for nearly everyone.
The real review behavior of these contributors is likely much richer than
the data shows. A proper implementation would fetch reviews for all PRs,
or at least for a random sample spread across time.
### Limitation 3 — The LLM has no domain knowledge of the codebase
The model doesn't know that a 5-line change to `packages/gateway/src/channel.ts`
might be more critical than a 500-line change to documentation. Without
architectural context, it evaluates changes purely on surface signals
(PR title, description, diff style) rather than strategic importance.
A maintainer reading the same PR would immediately know whether a change
is in a hot path or an obscure edge case.
### Limitation 4 — Recency bias in PR sampling
The LLM sees the contributor's most recent PRs. A contributor who was
highly active 6 months ago with high-quality work but has slowed down
recently may be unfairly rated on their current state rather than their
full history. Conversely, a contributor who just joined and made two
impressive PRs might be over-rated because their sample looks good even
though they haven't demonstrated consistency yet.
### Limitation 5 — Scores cluster too tightly
Most contributors scored between 3.0 and 3.2, which limits differentiation.
This is partly by design (the prompt instructs the model to be calibrated
and not inflate scores) but also reflects that with limited diff data,
the model defaults to "average quality" when it can't see enough signal.
A richer prompt with more PR context would produce more spread in scores.
---
## 6. What I'd Build Next (One More Week)
### Trajectory Analysis — Is a contributor rising or declining?
The single most useful addition would be plotting each contributor's monthly
commit velocity over time on a simple line chart. With the commit data already
fetched (each commit has a timestamp), this requires no new API calls —
just grouping commits by month per contributor.
This would let you immediately see:
- **Rising stars** — contributors whose activity is accelerating (e.g., went
  from 5 commits/month to 30 commits/month over 6 months)
- **Fading contributors** — previously active people who are drifting away
  (could be a retention signal worth acting on)
- **Burst contributors** — one-time spikes that never sustained
This is small enough to implement in a single afternoon (one new chart in the
Recency tab), easy to explain in an interview ("I grouped the existing commit
timestamps by contributor and month"), and adds genuine analytical value
that the current dashboard doesn't have.
---
## 7. Honest Reflection
### What worked well
The data pipeline is solid. Fetching from both the fork (for commits) and the
original repo (for PRs, issues, reviews, comments) was the critical insight
that unblocked the whole project — without that fix, all PR and review data
was zero.
The Streamlit dashboard is clean and interactive. The four-tab structure maps
directly to the four required dimensions (volume, recency, scope, impact),
making it easy for a reviewer to navigate.
The autorater produces reasonable, defensible scores. `steipete` as Core
Maintainer and `cpojer` as the lowest scorer are both correct assessments
that match what the raw data shows.
### What I would do differently
The biggest thing I'd change is review data completeness. Fetching reviews
for only the first 100 PRs out of 9,000 means review engagement scores are
almost meaningless. I would prioritize fetching a random sample of 500 PRs
spread across time rather than the 100 most recent — this would give a
much more representative picture of who actually does code review work.
I would also invest more in prompt engineering for the autorater. The current
prompt produces reasonable scores but the tight clustering (most contributors
score 3.0–3.2) suggests the model needs more differentiation signals. Adding
the contributor's merge rate, the age of PRs they typically fix (older issues
= higher significance), and a comparison to the median contributor would
help the model make finer distinctions.
---
*Report written by Aniket Asr as part of the OpenClaw Contributor Intelligence take-home.*
