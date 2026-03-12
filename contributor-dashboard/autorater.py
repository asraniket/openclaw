import json
import os
import time
import requests
from groq import Groq
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
REPO = "openclaw/openclaw"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}
client = Groq(api_key=GROQ_API_KEY)
# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading data...")
contributors = json.load(open("data/contributors.json"))
prs_data     = json.load(open("data/prs.json"))
pr_by_author = {}
for pr in prs_data:
    try:
        user  = pr.get("user", {})
        login = user.get("login") if user else None
        if login:
            pr_by_author.setdefault(login, []).append(pr)
    except Exception:
        continue
print(f"Loaded {len(contributors)} contributors, {len(prs_data)} PRs")
# ── Safe HTTP GET ──────────────────────────────────────────────────────────────
def safe_get(url, headers, max_attempts=5):
    """HTTP GET with retries. Always returns response or None — never raises."""
    for attempt in range(max_attempts):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                return r
            elif r.status_code in (403, 429):
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait  = max(reset - int(time.time()), 15)
                print(f"\\n    GitHub rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"\\n    HTTP {r.status_code} on attempt {attempt+1}/{max_attempts}")
                time.sleep(5)
        except Exception as e:
            wait = (attempt + 1) * 5
            print(f"\\n    Network error (attempt {attempt+1}/{max_attempts}), retrying in {wait}s: {type(e).__name__}")
            time.sleep(wait)
    return None
# ── Fetch PR diff ──────────────────────────────────────────────────────────────
def fetch_pr_diff(pr_number):
    """Fetch PR diff truncated to 1000 chars. Returns empty string on failure."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}"
    r   = safe_get(url, {**HEADERS, "Accept": "application/vnd.github.diff"})
    return r.text[:1000] if r else ""
# ── Build PR summary ───────────────────────────────────────────────────────────
def build_pr_summary(login, max_prs=2):
    """Build text summary of contributor PRs for the prompt. Never raises."""
    try:
        my_prs = pr_by_author.get(login, [])[:max_prs]
        if not my_prs:
            return "No PRs found for this contributor."
        summaries = []
        for pr in my_prs:
            try:
                number = pr["number"]
                title  = pr.get("title", "No title")
                body   = (pr.get("body") or "")[:400]
                merged = "MERGED" if pr.get("merged_at") else "NOT MERGED"
                diff   = fetch_pr_diff(number)
                summaries.append(
                    f"PR #{number} [{merged}]\\n"
                    f"Title: {title}\\n"
                    f"Description: {body}\\n"
                    f"Diff (truncated):\\n{diff}\\n"
                    f"{'='*60}"
                )
                time.sleep(0.2)
            except Exception as e:
                summaries.append(f"PR #{pr.get('number','?')}: failed to load ({type(e).__name__})")
        return "\\n".join(summaries)
    except Exception as e:
        return f"Failed to build PR summary: {type(e).__name__}"
# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a senior software engineer evaluating open-source contributors.
Given a contributor's stats and sample PRs, rate them across four dimensions.
Be calibrated and critical — most contributors should score 2-3, not 4-5.
Only give 5 if the evidence is clearly exceptional.
Always respond with valid JSON only. No markdown, no extra text, no code fences.
Use exactly this schema:
{
  "code_quality": <int 1-5>,
  "problem_significance": <int 1-5>,
  "review_engagement": <int 1-5>,
  "consistency": <int 1-5>,
  "overall": <float, weighted average>,
  "tier": "<one of: Core Maintainer | Active Contributor | Occasional Contributor | Drive-by Contributor>",
  "reasoning": "<2-4 sentences explaining the scores with specific evidence>"
}
Scoring guide:
- code_quality: cleanliness of diffs, scope, tests, naming
- problem_significance: does the PR fix something real or meaningful
- review_engagement: do they review others PRs (use reviews_given count)
- consistency: reliable over time, or one-hit contributor
- overall: (code_quality*0.3 + problem_significance*0.3 + review_engagement*0.2 + consistency*0.2)
"""
# ── Parse wait time from Groq rate limit error message ────────────────────────
def parse_wait_seconds(error_message):
    """Extract wait time in seconds from Groq rate limit error. Returns 3600 if not found."""
    try:
        
        import re
        match = re.search(r"try again in\\s+(?:(\\d+)h)?\\s*(?:(\\d+)m)?\\s*(?:([\\d.]+)s)?", str(error_message))
        if match:
            hours   = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = float(match.group(3) or 0)
            total   = hours * 3600 + minutes * 60 + seconds
            return int(total) + 5  # add 5s buffer
    except Exception:
        pass
    return 300  # default 5 min if parsing fails
# ── Call LLM with full retry including daily token limit handling ──────────────
def call_llm(login, user_prompt):
    """
    Call Groq LLM. Retries forever on rate limits (waits the exact time told to).
    Retries 5 times on other errors. Never raises — returns default on total failure.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown fences if model adds them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            rating = json.loads(raw)
            rating["login"] = login
            return rating
        except json.JSONDecodeError:
            if attempt <= 5:
                print(f"\\n    Invalid JSON from LLM (attempt {attempt}), retrying in 5s...")
                time.sleep(5)
                continue
            else:
                print(f"\\n    LLM kept returning invalid JSON. Using default for {login}.")
                break
        except Exception as e:
            err_str = str(e)
            # Daily token limit (TPD) — wait exact amount told and retry
            if "TPD" in err_str or ("tokens per day" in err_str.lower()):
                wait = parse_wait_seconds(err_str)
                print(f"\\n    Daily token limit hit. Waiting {wait//60}m {wait%60}s then retrying...")
                time.sleep(wait)
                attempt = 0  # reset attempt counter after waiting
                continue
            # Per-minute rate limit — wait 65 seconds and retry
            if "rate_limit_exceeded" in err_str or "429" in err_str:
                print(f"\\n    Per-minute rate limit. Waiting 65s...")
                time.sleep(65)
                continue
            # Other errors — retry up to 5 times
            if attempt <= 5:
                wait = attempt * 5
                print(f"\\n    LLM error (attempt {attempt}/5), retrying in {wait}s: {type(e).__name__}")
                time.sleep(wait)
                continue
            else:
                print(f"\\n    All attempts failed for {login}: {type(e).__name__}")
                break
    # Return safe default if everything failed
    return {
        "login":                login,
        "code_quality":         1,
        "problem_significance": 1,
        "review_engagement":    1,
        "consistency":          1,
        "overall":              1.0,
        "tier":                 "Unknown",
        "reasoning":            "Automated rating failed — manual review needed."
    }
# ── Rate one contributor ───────────────────────────────────────────────────────
def rate_contributor(c):
    """Rate a single contributor. Never raises."""
    login = c.get("login", "unknown")
    try:
        pr_summary  = build_pr_summary(login)
        user_prompt = f"""
Contributor: {login}
Stats:
  - Total commits       : {c.get('commits', 0)}
  - Recent commits (90d): {c.get('recent_commits', 0)}
  - PRs opened          : {c.get('prs_opened', 0)}
  - PRs merged          : {c.get('prs_merged', 0)}
  - Issues opened       : {c.get('issues_opened', 0)}
  - Reviews given       : {c.get('reviews_given', 0)}
  - Comments made       : {c.get('comments_made', 0)}
  - First contribution  : {c.get('first_contribution', 'unknown')}
  - Last contribution   : {c.get('last_contribution', 'unknown')}
  - Top directories     : {list(c.get('directories', {}).keys())[:5]}
Sample PRs:
{pr_summary}
Output valid JSON only. No markdown, no code fences.
"""
        return call_llm(login, user_prompt)
    except Exception as e:
        print(f"\\n    Unexpected error for {login}: {type(e).__name__}: {e}")
        return {
            "login":                login,
            "code_quality":         1,
            "problem_significance": 1,
            "review_engagement":    1,
            "consistency":          1,
            "overall":              1.0,
            "tier":                 "Unknown",
            "reasoning":            f"Unexpected error: {type(e).__name__}"
        }
# ── Main loop ──────────────────────────────────────────────────────────────────
top_contributors = [c for c in contributors if c.get("commits", 0) > 0][:15]
print(f"\\nRating {len(top_contributors)} contributors")
ratings = []
for i, c in enumerate(top_contributors):
    login = c.get("login", "unknown")
    print(f"\\n  [{i+1}/{len(top_contributors)}] Rating {login}...", end=" ", flush=True)
    rating = rate_contributor(c)
    ratings.append(rating)
    print(f"overall={rating['overall']} | {rating['tier']}")
    # Save after every single contributor — never lose progress
    try:
        json.dump(ratings, open("data/ratings.json", "w"), indent=2)
    except Exception as e:
        print(f"    Warning: could not save ratings.json: {e}")
    time.sleep(2)  # small pause between contributors
# ── Final save & summary ───────────────────────────────────────────────────────
json.dump(ratings, open("data/ratings.json", "w"), indent=2)
print("\\n" + "="*50)
print("RATINGS SUMMARY")
print("="*50)
for r in sorted(ratings, key=lambda x: x.get("overall", 0), reverse=True):
    print(f"  {r['login']:<25} overall={r.get('overall', 0):.1f}  |  {r.get('tier', 'Unknown')}")
print("="*50)
print(f"\\nDone. Saved {len(ratings)} ratings to data/ratings.json")
