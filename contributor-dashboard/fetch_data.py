import requests
import json
import os
import time
TOKEN = os.environ["GITHUB_TOKEN"]
REPO_COMMITS = "shivanipods/openclaw"  # fork — has commit history
REPO_PRS     = "openclaw/openclaw"     # original — has PRs, issues, reviews, comments
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}
os.makedirs("data", exist_ok=True)
def paginate(url, save_path):
    results = []
    page = 1
    while url:
        print(f"  Page {page}...", end=" ", flush=True)
        # Retry up to 5 times on any network error
        r = None
        for attempt in range(5):
            try:
                r = requests.get(url, headers=HEADERS, timeout=30)
                break
            except Exception as e:
                wait = (attempt + 1) * 10
                print(f"\\n  Error (attempt {attempt+1}/5), retrying in {wait}s: {e}")
                time.sleep(wait)
        if r is None:
            print(f"\\n  All retries failed. Saving {len(results)} records and stopping.")
            json.dump(results, open(save_path, "w"), indent=2)
            return results
        # Handle rate limit
        if r.status_code in (403, 429):
            reset_time = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset_time - int(time.time()), 15)
            print(f"\\n  Rate limited! Waiting {wait}s...")
            time.sleep(wait)
            continue  # retry same page, don't advance
        if r.status_code != 200:
            print(f"\\n  Error {r.status_code}: {r.text[:300]}")
            json.dump(results, open(save_path, "w"), indent=2)
            return results
        data = r.json()
        if not data:
            break
        results.extend(data)
        print(f"{len(data)} items (total: {len(results)})")
        url = r.links.get("next", {}).get("url")
        page += 1
        time.sleep(0.5)
    json.dump(results, open(save_path, "w"), indent=2)
    return results
def fetch_reviews_for_prs(prs, save_path):
    reviews_all = {}
    print(f"  Fetching reviews for {len(prs)} PRs...")
    for i, pr in enumerate(prs):
        number = pr["number"]
        print(f"  [{i+1}/{len(prs)}] PR #{number}", end=" ", flush=True)
        r = None
        for attempt in range(5):
            try:
                url = f"https://api.github.com/repos/{REPO_PRS}/pulls/{number}/reviews"
                r = requests.get(url, headers=HEADERS, timeout=30)
                break
            except Exception as e:
                wait = (attempt + 1) * 5
                print(f"retrying in {wait}s... ", end="")
                time.sleep(wait)
        if r and r.status_code == 200:
            reviews_all[str(number)] = r.json()
            print(f"({len(r.json())} reviews)")
        else:
            print("(skipped)")
        time.sleep(0.3)
    json.dump(reviews_all, open(save_path, "w"), indent=2)
    return reviews_all
# ── 1. Commits ────────────────────────────────────────────────────────────────
print("\\n[1/5] Fetching commits (from fork)...")
commits = paginate(
    f"https://api.github.com/repos/{REPO_COMMITS}/commits?per_page=100",
    "data/commits.json"
)
print(f"  Done. Total: {len(commits)}\\n")
# ── 2. Pull Requests ──────────────────────────────────────────────────────────
print("[2/5] Fetching pull requests (from original repo)...")
prs = paginate(
    f"https://api.github.com/repos/{REPO_PRS}/pulls?state=all&per_page=100",
    "data/prs.json"
)
print(f"  Done. Total: {len(prs)}\\n")
# ── 3. Issues ─────────────────────────────────────────────────────────────────
print("[3/5] Fetching issues (from original repo)...")
issues = paginate(
    f"https://api.github.com/repos/{REPO_PRS}/issues?state=all&per_page=100",
    "data/issues.json"
)
print(f"  Done. Total: {len(issues)}\\n")
# ── 4. Comments ───────────────────────────────────────────────────────────────
print("[4/5] Fetching comments (from original repo)...")
comments = paginate(
    f"https://api.github.com/repos/{REPO_PRS}/issues/comments?per_page=100",
    "data/comments.json"
)
print(f"  Done. Total: {len(comments)}\\n")
# ── 5. Reviews ────────────────────────────────────────────────────────────────
print("[5/5] Fetching PR reviews (first 100 PRs)...")
reviews = fetch_reviews_for_prs(prs[:100], "data/reviews.json")
print(f"  Done. Total PRs covered: {len(reviews)}\\n")
print("=" * 50)
print("All data fetched successfully!")
print(f"  Commits  : {len(commits)}")
print(f"  PRs      : {len(prs)}")
print(f"  Issues   : {len(issues)}")
print(f"  Comments : {len(comments)}")
print(f"  Reviews  : {len(reviews)} PRs covered")
print("=" * 50)
