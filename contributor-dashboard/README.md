# 🦞 OpenClaw Contributor Intelligence Dashboard
A data pipeline + LLM-powered dashboard that analyzes contributor activity and impact
across the [OpenClaw](https://github.com/openclaw/openclaw) open-source project.
Built as part of a take-home assessment. The system fetches real GitHub data,
processes it into contributor profiles, runs an LLM autorater on the top 15 contributors,
and presents everything in an interactive Streamlit dashboard.
---
## 📸 What It Looks Like
The dashboard has 4 tabs:
| Tab | What it shows |
|-----|--------------|
| 📊 **Volume** | Commits, PRs opened/merged, issues, reviews, comments per contributor |
| ⏱ **Recency** | Recent (last 90 days) vs historic activity — who is still active? |
| 🗂 **Scope** | Which directories/files each contributor touches — breadth of codebase coverage |
| 🤖 **Autorater** | LLM-generated impact scores (code quality, significance, engagement, consistency) with reasoning |
---
## 🗂 Project Structure
```
openclaw/
└── contributor-dashboard/
    ├── fetch_data.py        # Step 1 — Pulls all data from GitHub API
    ├── process_data.py      # Step 2 — Builds contributor profiles from raw data
    ├── autorater.py         # Step 3 — LLM-based impact rating (uses Groq + LLaMA 3.3)
    ├── dashboard.py         # Step 4 — Streamlit interactive dashboard
    ├── requirements.txt     # Python dependencies
    ├── README.md            # This file
    ├── REPORT.md            # Written analysis and findings
    └── data/                # Auto-generated data folder (created by scripts)
        ├── commits.json
        ├── prs.json
        ├── issues.json
        ├── comments.json
        ├── reviews.json
        ├── contributors.json
        └── ratings.json
```
---
## ⚙️ Requirements
- **Python 3.9 or higher**
- **Git** installed and accessible in your terminal
- A **GitHub Personal Access Token** (free, read-only)
- A **Groq API Key** (free, no credit card required)
---
## 🔑 API Keys You Need
### 1. GitHub Personal Access Token
Used to read commits, PRs, issues, reviews, and comments from GitHub.
**How to get it:**
1. Go to [github.com](https://github.com) → Profile picture → **Settings**
2. Scroll to bottom of left sidebar → **Developer settings**
3. Click **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**
4. Give it a name (e.g. `openclaw-dashboard`), set expiry to 30 days
5. Check the **`repo`** scope (read access to public repos)
6. Click **Generate token** and copy it immediately — it won't be shown again
7. It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
> ⚠️ Never paste your token directly into code or commit it to GitHub.
> Always use environment variables as shown below.
---
### 2. Groq API Key
Used by the LLM autorater. Groq provides free access to LLaMA 3.3 70B.
**How to get it:**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up with Google or GitHub (no credit card needed)
3. Click **API Keys** → **Create API Key**
4. Copy the key — it looks like: `gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`
> **Free tier limits:** 30 requests/minute, 100,000 tokens/day.
> The autorater uses ~6,000-8,000 tokens per run for 15 contributors.
---
## 🚀 Setup & Run — Step by Step
### Step 1 — Clone the repo
```bash
git clone https://github.com/asraniket/openclaw.git
cd openclaw/contributor-dashboard
```
---
### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```
If you have multiple Python versions or `pip` isn't found:
```bash
pip3 install -r requirements.txt
# or
python -m pip install -r requirements.txt
# or
python3 -m pip install -r requirements.txt
```
---
### Step 3 — Set environment variables
You must set your API keys as environment variables before running the scripts.
#### 🪟 Windows — Command Prompt
```cmd
set GITHUB_TOKEN=ghp_yourTokenHere
set GROQ_API_KEY=gsk_yourKeyHere
```
#### 🪟 Windows — PowerShell
```powershell
$env:GITHUB_TOKEN = "ghp_yourTokenHere"
$env:GROQ_API_KEY = "gsk_yourKeyHere"
```
#### 🍎 macOS / 🐧 Linux — Terminal
```bash
export GITHUB_TOKEN=ghp_yourTokenHere
export GROQ_API_KEY=gsk_yourKeyHere
```
> ⚠️ These variables are set for the current terminal session only.
> If you open a new terminal window, you'll need to set them again.
**Tip — Save them permanently:**
On macOS/Linux, add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export GITHUB_TOKEN=ghp_yourTokenHere' >> ~/.zshrc
echo 'export GROQ_API_KEY=gsk_yourKeyHere' >> ~/.zshrc
source ~/.zshrc
```
On Windows, you can set them permanently via:
System Properties → Advanced → Environment Variables → New (under User variables)
---
### Step 4 — Fetch data from GitHub
```bash
python fetch_data.py
```
This fetches commits, PRs, issues, comments, and reviews from GitHub and saves them
to the `data/` folder. It takes **5–20 minutes** depending on your internet speed
(the repo has 17,000+ commits and 9,000+ PRs).
**What gets saved:**
- `data/commits.json` — all commits (~18,000)
- `data/prs.json` — all pull requests (~9,000)
- `data/issues.json` — all issues
- `data/comments.json` — all issue comments
- `data/reviews.json` — PR reviews for the first 100 PRs
> If the script crashes mid-way due to a network error, just run it again —
> it has retry logic built in and will attempt to re-fetch automatically.
---
### Step 5 — Process data into contributor profiles
```bash
python process_data.py
```
Runs in ~10–30 seconds. Reads all raw JSON files and builds a profile for each
contributor including commits, PRs, recency, and directory-level scope data
(using `git log` from the cloned repo).
Saves result to `data/contributors.json` (~18,000 contributor profiles).
---
### Step 6 — Run the LLM autorater
```bash
python autorater.py
```
Rates the top 15 contributors by commit count using LLaMA 3.3 70B via Groq.
Takes ~3–5 minutes (includes fetching PR diffs and LLM calls).
Saves result to `data/ratings.json`.
> If it hits the Groq daily token limit (100,000 tokens/day on free tier),
> the script automatically detects this, waits for the reset time printed in
> the error message, and continues — no manual intervention needed.
> You can also just re-run the script after the reset time.
---
### Step 7 — Launch the dashboard
```bash
python -m streamlit run dashboard.py
```
Alternative commands if the above doesn't work:
```bash
streamlit run dashboard.py           # if streamlit is in PATH
python3 -m streamlit run dashboard.py  # on macOS/Linux with python3
```
The dashboard opens automatically in your browser at **http://localhost:8501**
If it doesn't open automatically, navigate to http://localhost:8501 manually.
---
## 🔄 Re-fetching Fresh Data
```bash
python fetch_data.py    # fetches everything fresh (overwrites existing files)
python process_data.py  # re-processes
python autorater.py     # re-rates
```
---
## 📊 Data Sources
| Source | Repo | What's fetched |
|--------|------|----------------|
| Commits | `shivanipods/openclaw` (fork) | Full commit history |
| Pull Requests | `openclaw/openclaw` (original) | All PRs (open + closed + merged) |
| Issues | `openclaw/openclaw` (original) | All issues |
| Comments | `openclaw/openclaw` (original) | All issue + PR comments |
| Reviews | `openclaw/openclaw` (original) | Reviews for first 100 PRs |
| Directory data | Local git clone | `git log --name-only` for file paths |
> Commits are fetched from the fork because the fork preserves the full commit
> history. PRs, issues, reviews, and comments are fetched from the original repo
> because forks don't copy that data.
---
## 🤖 Autorater — How It Works
The autorater uses **LLaMA 3.3 70B** (via Groq's free API) to evaluate each
contributor across 4 dimensions:
| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Code Quality | 30% | Clean diffs, well-scoped changes, evidence of testing |
| Problem Significance | 30% | Does the PR fix something real or ship something meaningful? |
| Review Engagement | 20% | Do they review others' PRs substantively? |
| Consistency | 20% | Reliable over time, or one-hit contributor? |
**Overall score** = `(code_quality × 0.3) + (problem_significance × 0.3) + (review_engagement × 0.2) + (consistency × 0.2)`
**Tiers:**
- 🏆 Core Maintainer — overall ≥ 3.5, high consistency
- ⭐ Active Contributor — overall 2.5–3.5
- 🔵 Occasional Contributor — overall 1.5–2.5
- ⚪ Drive-by Contributor — overall < 1.5
Each contributor is rated using their stats (commits, PRs, reviews, comments) plus
summaries of their 2 most recent PRs including truncated diffs.
---
## 🛠 Troubleshooting
**`streamlit: command not found` or not recognized**
```bash
python -m streamlit run dashboard.py
```
**`ModuleNotFoundError`**
```bash
pip install -r requirements.txt
```
**`KeyError: GITHUB_TOKEN`**
You forgot to set the environment variable. See Step 3 above.
**GitHub API rate limit (403)**
The script handles this automatically by waiting for the rate limit reset.
If you're hitting it frequently, use a token with higher rate limits.
**Groq daily token limit (429 TPD)**
The autorater detects this and prints how long to wait. Either wait or re-run
after the reset time. The free tier resets every 24 hours.
**`FileNotFoundError: data/contributors.json`**
Make sure you're running from inside the `contributor-dashboard/` folder:
```bash
cd openclaw/contributor-dashboard
python -m streamlit run dashboard.py
```
**Dashboard shows old data after re-running scripts**
Press `R` or `F5` in the browser to reload the Streamlit app.
---
## 📋 Full Run Checklist
- [ ] Python 3.9+ installed
- [ ] `git clone` done
- [ ] `cd openclaw/contributor-dashboard`
- [ ] `pip install -r requirements.txt`
- [ ] `GITHUB_TOKEN` environment variable set
- [ ] `GROQ_API_KEY` environment variable set
- [ ] `python fetch_data.py` — completed, data/ folder has 5 JSON files
- [ ] `python process_data.py` — completed, contributors.json created
- [ ] `python autorater.py` — completed, ratings.json has 15 entries
- [ ] `python -m streamlit run dashboard.py` — dashboard open at localhost:8501
---
## 📄 Written Report
See [REPORT.md](./REPORT.md) for:
- Rating schema design decisions
- 3–5 interesting findings from the data
- Limitations of the autorater
- What I'd build next
---
## 🔧 Tech Stack
| Component | Technology |
|-----------|-----------|
| Data fetching | GitHub REST API v3 |
| Data processing | Python, `collections`, `datetime` |
| LLM autorater | LLaMA 3.3 70B via Groq API |
| Dashboard | Streamlit + Plotly |
| Language | Python 3.9+ |
