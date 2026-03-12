import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone, timedelta
# ── Path setup ────────────────────────────────────────────────────────────────
# contributor-dashboard/ is one level inside the repo root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_PATH  = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
print("Loading raw data...")
commits  = json.load(open("data/commits.json"))
prs      = json.load(open("data/prs.json"))
issues   = json.load(open("data/issues.json"))
comments = json.load(open("data/comments.json"))
reviews  = json.load(open("data/reviews.json"))
now = datetime.now(timezone.utc)
recent_cutoff = now - timedelta(days=90)
# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_date(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
def update_dates(c, date_str):
    d = parse_date(date_str)
    if d is None:
        return
    if c["first_contribution"] is None or d < parse_date(c["first_contribution"]):
        c["first_contribution"] = date_str
    if c["last_contribution"] is None or d > parse_date(c["last_contribution"]):
        c["last_contribution"] = date_str
# ── Contributor map ───────────────────────────────────────────────────────────
contributors = defaultdict(lambda: {
    "login": "",
    "commits": 0,
    "recent_commits": 0,
    "historic_commits": 0,
    "prs_opened": 0,
    "prs_merged": 0,
    "issues_opened": 0,
    "reviews_given": 0,
    "comments_made": 0,
    "first_contribution": None,
    "last_contribution": None,
    "directories": {},
    "files_touched": [],
})
# ── Commits ───────────────────────────────────────────────────────────────────
print("Processing commits...")
for commit in commits:
    author = commit.get("author")
    if not author:
        continue
    login = author.get("login")
    if not login:
        continue
    c = contributors[login]
    c["login"] = login
    c["commits"] += 1
    date_str = commit.get("commit", {}).get("author", {}).get("date")
    update_dates(c, date_str)
    d = parse_date(date_str)
    if d:
        if d >= recent_cutoff:
            c["recent_commits"] += 1
        else:
            c["historic_commits"] += 1
# ── PRs ───────────────────────────────────────────────────────────────────────
print("Processing PRs...")
for pr in prs:
    user = pr.get("user")
    if not user:
        continue
    login = user.get("login")
    if not login:
        continue
    c = contributors[login]
    c["login"] = login
    c["prs_opened"] += 1
    if pr.get("merged_at"):
        c["prs_merged"] += 1
    update_dates(c, pr.get("created_at"))
# ── Issues ────────────────────────────────────────────────────────────────────
print("Processing issues...")
for issue in issues:
    if "pull_request" in issue:
        continue
    user = issue.get("user")
    if not user:
        continue
    login = user.get("login")
    if not login:
        continue
    c = contributors[login]
    c["login"] = login
    c["issues_opened"] += 1
    update_dates(c, issue.get("created_at"))
# ── Comments ──────────────────────────────────────────────────────────────────
print("Processing comments...")
for comment in comments:
    user = comment.get("user")
    if not user:
        continue
    login = user.get("login")
    if not login:
        continue
    c = contributors[login]
    c["login"] = login
    c["comments_made"] += 1
    update_dates(c, comment.get("created_at"))
# ── Reviews ───────────────────────────────────────────────────────────────────
print("Processing reviews...")
for pr_number, pr_reviews in reviews.items():
    for review in pr_reviews:
        user = review.get("user")
        if not user:
            continue
        login = user.get("login")
        if not login:
            continue
        c = contributors[login]
        c["login"] = login
        c["reviews_given"] += 1
        update_dates(c, review.get("submitted_at"))
# ── Git log — directory & file data ───────────────────────────────────────────
print(f"\\nProcessing git log from repo: {REPO_PATH}")
git_log_success = False
try:
    result = subprocess.run(
        ["git", "log", "--name-only", "--pretty=format:COMMIT:%ae", "--no-merges"],
        capture_output=True,
        text=True,
        cwd=REPO_PATH,
        timeout=120  # give it up to 2 minutes
    )
    if result.returncode != 0:
        print(f"  git log returned error: {result.stderr[:200]}")
    elif not result.stdout.strip():
        print("  git log returned no output")
    else:
        # Build email -> login lookup from commits data
        email_to_login = {}
        for commit in commits:
            author      = commit.get("author")
            commit_data = commit.get("commit", {})
            email       = commit_data.get("author", {}).get("email", "").lower()
            login       = author.get("login") if author else None
            if email and login:
                email_to_login[email] = login
        print(f"  Built email→login map for {len(email_to_login)} emails")
        current_login = None
        files_processed = 0
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("COMMIT:"):
                email = line.replace("COMMIT:", "").strip().lower()
                current_login = email_to_login.get(email)
            elif line and current_login and current_login in contributors:
                filepath = line
                parts    = filepath.split("/")
                top_dir  = parts[0]
                c = contributors[current_login]
                # Count directory
                c["directories"][top_dir] = c["directories"].get(top_dir, 0) + 1
                # Track unique files (limit to 500 per contributor to save memory)
                if len(c["files_touched"]) < 500 and filepath not in c["files_touched"]:
                    c["files_touched"].append(filepath)
                files_processed += 1
        print(f"  Git log processed: {files_processed} file-touch events")
        git_log_success = True
except FileNotFoundError:
    print("  git not found. Make sure git is installed and in your PATH.")
except subprocess.TimeoutExpired:
    print("  git log timed out after 2 minutes.")
except Exception as e:
    print(f"  git log failed: {type(e).__name__}: {e}")
# ── Fallback: PR keyword method if git log failed ─────────────────────────────
if not git_log_success:
    print("\\nFalling back to PR keyword method for directory data...")
    dir_keywords = {
        "packages":   "packages",
        "apps":       "apps",
        "docs":       "docs",
        "extensions": "extensions",
        "channels":   "channels",
        "gateway":    "packages/gateway",
        "telegram":   "channels/telegram",
        "discord":    "channels/discord",
        "slack":      "channels/slack",
        "whatsapp":   "channels/whatsapp",
        "ios":        "apps/ios",
        "android":    "apps/android",
        "macos":      "apps/macos",
        "ui":         "packages/ui",
        "cli":        "packages/cli",
    }
    for pr in prs:
        user = pr.get("user")
        if not user:
            continue
        login = user.get("login")
        if not login or login not in contributors:
            continue
        title = (pr.get("title") or "").lower()
        body  = (pr.get("body") or "").lower()
        text  = title + " " + body
        for keyword, directory in dir_keywords.items():
            if keyword in text:
                contributors[login]["directories"][directory] = contributors[login]["directories"].get(directory, 0) + 1
    print("  PR keyword fallback complete")
# ── Save ──────────────────────────────────────────────────────────────────────
print("\\nSaving...")
final = []
for login, c in contributors.items():
    if not c["login"]:
        continue
    final.append(dict(c))
final.sort(key=lambda x: x["commits"], reverse=True)
json.dump(final, open("data/contributors.json", "w"), indent=2)
print(f"Saved {len(final)} contributors")
# ── Preview top 10 ────────────────────────────────────────────────────────────
print("\\nTop 10 contributors:")
for c in final[:10]:
    dirs_count  = len(c.get("directories", {}))
    files_count = len(c.get("files_touched", []))
    print(f"  {c['login']}: commits={c['commits']}, "
          f"prs_merged={c['prs_merged']}, "
          f"reviews={c['reviews_given']}, "
          f"comments={c['comments_made']}, "
          f"dirs={dirs_count}, "
          f"files={files_count}")
