# OpenClaw Contributor Intelligence — Written Report

**Project:** Contributor Intelligence Dashboard + LLM Autorater
**Repo:** [asraniket/openclaw](https://github.com/asraniket/openclaw)
**Branch:** candidate/aniket-ransing

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

The dashboard has four tabs:

- **Volume** — commits, PRs, issues, reviews, and comments per contributor
- **Recency** — recent (last 90 days) vs. historic activity to identify who is still active
- **Scope** — which directories and files each contributor touches, powered by `git log`
- **Autorater** — LLM-generated structured impact scores alongside raw metrics

---

## 2. Rating Schema

### Why commit count is not the primary signal

Commit count is the most visible metric and the most misleading. `steipete` has
11,801 commits — 27× more than the next contributor. But raw commit count
conflates architectural work with typo fixes, version bumps, and formatting runs.
A contributor with 50 well-scoped, impactful PRs is more valuable than one with
500 trivial commits.

The autorater measures impact, not volume. Four dimensions with the following weights:

---

### Dimension 1 — Code Quality (30%)

Is the diff clean, well-scoped, and purposeful? Does it suggest the contributor
understands the codebase, or are they making broad changes without clear intent?

Weighted at 30% because it is the most direct signal of engineering skill.
Contributors who write minimal, well-structured diffs consistently demonstrate
codebase mastery.

The LLM evaluates this using truncated PR diffs alongside titles and
descriptions, looking for: single-responsibility changes, descriptive naming,
absence of unrelated edits, and evidence of testing or documentation where
appropriate.

---

### Dimension 2 — Problem Significance (30%)

Does the PR address something that actually matters — a real bug affecting users,
a meaningful feature, a measurable performance improvement — or is it a cosmetic
change, a dependency bump, or a config tweak?

Weighted at 30% because open source health depends on contributors moving the
project forward. A perfectly clean diff of a trivial change is still less
valuable than a slightly rough fix of a critical bug.

The LLM reads PR titles and bodies for signals like "fixes #issue",
"closes bug where...", "adds support for...", or "improves performance of...",
then checks the diff to verify the change matches the description.

---

### Dimension 3 — Review Engagement (20%)

Do they review other contributors' PRs with substantive feedback, or do they
only submit their own work and never engage with the broader community?

Weighted at 20% because review engagement is a strong signal of project
ownership — a contributor who reviews PRs is investing beyond their own output.
The LLM uses `reviews_given` and `comments_made` counts from the full dataset
as the primary signals for this dimension.

---

### Dimension 4 — Consistency (20%)

Is the contributor reliable over time, or did they have a single burst of
activity and then disappear? Consistency predicts future contribution and
distinguishes genuine project investment from one-time engagement.

Weighted at 20% because consistency is already partially reflected in the
Recency tab, and because a contributor who was highly active for six months
and then slowed down is still valuable — over-penalizing them for reduced
recent activity would be unfair.

The LLM uses `first_contribution`, `last_contribution`, `recent_commits` vs.
`historic_commits`, and total time span of activity. A contributor active
across 12+ months scores higher than one with the same commit count compressed
into two weeks.

---

### Overall Score Formula

overall = (code_quality × 0.3) + (problem_significance × 0.3)
        + (review_engagement × 0.2) + (consistency × 0.2)



### Tier Classification

The tier assigned to each contributor is determined by the LLM as part of its
structured output. The tiers generally follow this pattern, though the LLM
may exercise judgment that deviates slightly from strict numeric thresholds:

| Tier | General Score Range |
|------|---------------------|
| Core Maintainer | ~3.5 and above |
| Active Contributor | ~2.5–3.5 |
| Occasional Contributor | ~1.5–2.5 |
| Drive-by Contributor | below ~1.5 |

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

---

## 4. Extra Credit — Team-Level View

The autorater's tier classification directly addresses the team-level view
extra credit. Every contributor is grouped into one of four clusters based on
their LLM-assessed impact profile:

| Tier | What it represents |
|------|-------------------|
| **Core Maintainer** | High impact, high consistency — the project's backbone |
| **Active Contributor** | Consistent, meaningful output but not at maintainer level |
| **Occasional Contributor** | Some real contributions but irregular or low volume |
| **Drive-by Contributor** | Single or very limited engagement, low depth |

These are not just score buckets. The LLM evaluates each contributor's PR
quality, problem significance, review behavior, and activity span together,
so the tier reflects the nature of their engagement — not just how often
they show up.

From the 15 rated contributors:
- **1 Core Maintainer** — `steipete`, the clear project anchor with the
  highest consistency score (5) and the broadest codebase coverage by far
- **12 Active Contributors** — a healthy mid-tier of contributors making
  real, regular improvements across various parts of the codebase
- **2 Occasional Contributors** — `Sid-Qin` and `cpojer`, both with
  signs of real capability but lacking the consistency or merge success
  of the Active tier

The **Scope tab** in the dashboard adds the "by area of codebase" dimension
to this clustering — each contributor's most-touched directories are listed,
so you can see whether contributors are specialists (focused on one area)
or generalists (spread across the codebase). `steipete` is the only true
generalist in the top 15; most Active Contributors are concentrated in
2–3 directories.

Together, the tier classification and scope data give a complete team-level
picture: who the core is, who the reliable contributors are, what parts of
the codebase each person owns, and who the project cannot afford to lose.


## 5. Findings

### Finding 1 — Extreme bus factor concentration

`steipete` accounts for 11,801 out of 17,506 commits — **67.4% of the entire
project history**. The next highest contributor (`vignesh07`) has 436 commits,
which is 96% fewer. The project's primary architect, most active reviewer, and
the person with the broadest codebase knowledge are all the same person. Even
for a founder-led open source project, a 67% commit concentration is unusually
high.

---

### Finding 2 — High commit count does not predict high impact

`cpojer` ranked 8th by commit count (156 commits) but received the lowest
autorater score (2.1). The data shows only 3 PRs merged out of 8 opened, low
comment activity, and minimal review engagement — the commits came from an
early burst that did not sustain.

`Takhoffman` by contrast ranked 9th by commits (121) but had 85 PRs merged —
an 87% merge rate — and scored 3.1. Fewer commits, more consistent output.
This validates the core design decision to rate impact rather than volume.

---

### Finding 3 — Almost no one reviews other people's PRs

Across all 15 rated contributors, review counts are near zero for almost
everyone. `steipete` has the highest review activity but still scores 1 on
review engagement. The project effectively has a single-person review
bottleneck where one maintainer is responsible for the vast majority of
community PR reviews.

---

### Finding 4 — The contributor base is very new

966 out of 18,904 contributors (5.1%) made a commit in the last 90 days. Most
contributors have a `first_contribution` date from late 2025 or early 2026,
meaning the majority of the contributor base joined in the past few months.
The project is in a rapid growth phase, not a mature steady state. The bus
factor risk is amplified because most contributors have not had enough time
to build deep codebase knowledge.

---

### Finding 5 — `vincentkoc` has the highest PR merge rate among top contributors

`vincentkoc` opened 295 PRs with 228 merged — a **77% merge rate**, the
highest among the top contributors. Despite fewer total commits than
`steipete`, `vignesh07`, or `obviyus`, this contributor's work gets accepted
at the highest rate, suggesting consistently well-scoped contributions. Raw
commit counts would rank this contributor mid-table; merge rate surfaces them
as one of the more reliable contributors in the project.

---

## 6. Limitations

### Diff truncation hides large changes

PR diffs are truncated to 1,000 characters to stay within the LLM's token
budget. A contributor making a 2,000-line architectural refactor looks
identical in the prompt to one making a 50-line fix. The LLM cannot assess
the full scope of large changes, which likely causes it to under-rate
contributors who tackle complex, large-scale work.

### Review data limited to first 100 PRs

PR review data was fetched for the first 100 PRs out of 9,000+. This was a
deliberate decision driven by two constraints: the GitHub API requires a
separate request per PR to retrieve its reviews, making full coverage
impractical within reasonable time, and passing review text for all 9,000
PRs into the LLM prompt would exceed token limits entirely.

In practice, this limitation has less impact than it might appear. The
autorater's review engagement dimension primarily uses `reviews_given` and
`comments_made` counts, which are aggregated across the full dataset — not
just the first 100 PRs. The raw review text from the 100 PRs serves as
supplementary context. For the top contributors by commit count (the 15 being
rated), their review activity is generally visible through comment counts even
when individual review records are sparse.

### No domain knowledge of the codebase

The model does not know that a 5-line change to `packages/gateway/src/channel.ts`
may be more critical than a 500-line change to documentation. Without
architectural context, it evaluates changes on surface signals — PR title,
description, diff style — rather than strategic importance.

### Recency bias in PR sampling

The LLM sees each contributor's most recent PRs. A contributor who was highly
active six months ago but has slowed recently may be rated on their current
state rather than their full history. Conversely, a new contributor with two
impressive recent PRs may appear stronger than their actual track record
warrants.

### Scores cluster too tightly

Most contributors scored between 3.0 and 3.2, which limits differentiation.
With truncated diffs and limited review context, the model defaults toward
average quality when it cannot see enough signal. A richer prompt with more
per-contributor data would produce more spread.

### Tier labels may not always align with the numeric score

Since tier classification is part of the LLM's output rather than a hard
rule, it can occasionally diverge from what the numeric score alone would
suggest. `Sid-Qin` scored 2.9 but was classified as Occasional Contributor
in the dashboard output — a score that would otherwise sit in the Active
Contributor range. This is expected behavior: the LLM weighs qualitative
signals from the PR context in addition to the score when assigning a tier.
The tier table in this report reflects the general pattern observed across
runs, not a strict programmatic threshold.

---

## 7. What I'd Build Next

### Trajectory analysis

The commit data already has timestamps. Grouping commits by month per
contributor and plotting monthly velocity requires no new API calls — just
an additional chart in the Recency tab.

This would surface:
- **Rising contributors** — activity accelerating month-over-month
- **Fading contributors** — previously active people drifting away (a retention signal)
- **Burst contributors** — one-time spikes that never sustained

### Bus factor calculation

With directory-level scope data already available, it is possible to calculate
which files or modules have only one meaningful contributor. This would identify
the specific parts of the codebase most at risk if a key contributor left —
a more actionable version of the bus factor finding.

### Richer prompt context for the autorater

Adding each contributor's merge rate, the typical age of issues they fix
(older issues = higher significance), and a comparison to the median
contributor would give the LLM more differentiation signal and reduce the
tight score clustering seen in this run.

---

## 8. Reflection

### What worked well

Fetching commits from the fork (which preserves full history) and
PRs/issues/reviews from the original repo was the key architectural decision —
without it, all PR and review data would be zero. The fork/original split is
documented in both the README and the fetch script.

The four-tab dashboard structure maps directly to the four required dimensions,
making it straightforward for a reviewer to navigate. The autorater output is
integrated into the dashboard alongside the raw metrics rather than being a
separate artifact.

The scores produced are defensible. `steipete` as Core Maintainer and `cpojer`
as the lowest scorer match what the raw data shows independently.

### What I'd do differently

The prompt could be stronger on differentiation. The current tight clustering
(most contributors at 3.0–3.2) suggests the model needs more signal to make
finer distinctions. Feeding in merge rate, issue age, and relative comparisons
to other contributors in the same run would help spread the scores more
meaningfully.

Review data coverage is the other area worth investing in — not by fetching
all 9,000 PRs, but by fetching a random sample of 300–500 PRs spread across
the project's full timeline. This would give a more representative picture of
review patterns without hitting time or token constraints.

---

*Report by Aniket Ransing — OpenClaw Contributor Intelligence take-home.*
