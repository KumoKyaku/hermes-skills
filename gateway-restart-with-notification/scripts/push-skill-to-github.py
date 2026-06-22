#!/usr/bin/env python
"""
Push the gateway-restart-with-notification skill to GitHub.
Handles classic PATs, fine-grained PATs, and SSH-only setups.

Usage:
    python scripts/push-skill-to-github.py

Requires (one of):
    - A valid PAT in ~/OneDrive/Key/Github/PAT.txt or ~/.hermes/.env as GITHUB_TOKEN
    - SSH key configured for GitHub (git@github.com)
    - Network access to api.github.com
"""
import json, os, subprocess, shutil, urllib.request, urllib.error
from urllib.request import urlopen, Request

REPO_NAME = "hermes-skills"
SKILL_DIR = os.path.expanduser("~/.hermes/skills/devops/gateway-restart-with-notification")
WORKDIR = os.path.expanduser(f"~/{REPO_NAME}")

# ── Check SSH first (works independently of PAT) ──
HAS_SSH = False
try:
    r = subprocess.run(["ssh", "-T", "git@github.com"],
                       capture_output=True, text=True, timeout=10)
    HAS_SSH = "successfully authenticated" in r.stderr or "Hi" in r.stderr
except Exception:
    pass
if HAS_SSH:
    print("SSH: git@github.com authenticated ✅")

# ── Resolve PAT ──
pat = ""
for p in [os.path.expanduser("~/OneDrive/Key/Github/PAT.txt"),
           os.path.expanduser("~/.hermes/.env")]:
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                s = line.strip()
                if "GITHUB_TOKEN" in s or "ghp_" in s or "github_pat_" in s:
                    if s.startswith("GITHUB_TOKEN="):
                        pat = s.split("=", 1)[1].strip().strip('"\'')
                    elif s.startswith("ghp_") or s.startswith("github_pat_"):
                        pat = s
                    if pat:
                        break
        if pat:
            break

if pat:
    print(f"PAT: {pat[:4]}...{pat[-4:]}")

if not pat and not HAS_SSH:
    print("No PAT found and no SSH key configured.")
    print("Add a token to ~/OneDrive/Key/Github/PAT.txt or set GITHUB_TOKEN in .env")
    print("Or set up SSH: ssh-keygen && ssh-copy-id ... && ssh -T git@github.com")
    exit(1)

# ── Get GitHub username ──
GH_USER = None
if pat:
    try:
        req = Request("https://api.github.com/user",
                      headers={"Authorization": f"Bearer {pat}",
                               "Accept": "application/vnd.github.v3+json"})
        with urlopen(req, timeout=10) as resp:
            user = json.loads(resp.read())
            GH_USER = user["login"]
            print(f"Auth OK: {GH_USER}")
    except Exception as e:
        print(f"PAT auth failed: {e}")
        if not HAS_SSH:
            exit(1)
        print("Falling back to SSH-only mode")

if not GH_USER and HAS_SSH:
    # Resolve user from SSH
    r = subprocess.run(["ssh", "-T", "git@github.com"],
                       capture_output=True, text=True, timeout=10)
    for line in r.stderr.split("\n"):
        if "Hi " in line:
            GH_USER = line.split("Hi ")[1].split("!")[0]
            print(f"SSH user: {GH_USER}")
            break

# ── Create repo (PAT only; fine-grained PATs may fail with 403) ──
CLONE_URL = None
if pat:
    repo_data = json.dumps({
        "name": REPO_NAME,
        "description": f"{GH_USER}'s Hermes Agent skills collection 💧",
        "private": False,
        "auto_init": True,
    }).encode()
    try:
        req = Request("https://api.github.com/user/repos", data=repo_data,
                      headers={"Authorization": f"Bearer {pat}",
                               "Content-Type": "application/json"})
        with urlopen(req, timeout=15) as resp:
            repo = json.loads(resp.read())
            print(f"Repo created: {repo['html_url']}")
            CLONE_URL = repo["clone_url"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        if e.code == 422:
            print(f"Repo '{REPO_NAME}' already exists")
            CLONE_URL = f"https://github.com/{GH_USER}/{REPO_NAME}.git"
        elif e.code == 403:
            print(f"Cannot create repo with this PAT (403): {body[:80]}")
            print("This is normal for fine-grained PATs without repo:create permission.")
            if HAS_SSH:
                print("SSH is available — will clone via SSH")
            else:
                print("Go to https://github.com/new and create 'hermes-skills' manually,")
                print("then re-run this script.")
                exit(1)
        else:
            print(f"Failed: {e.code} - {body}")
            exit(1)

if not CLONE_URL and HAS_SSH:
    CLONE_URL = f"git@github.com:{GH_USER}/{REPO_NAME}.git" if GH_USER else None

if not CLONE_URL:
    print("No clone URL available. Create the repo on GitHub first.")
    exit(1)

# ── Clone ──
if os.path.exists(WORKDIR):
    shutil.rmtree(WORKDIR)

if CLONE_URL.startswith("https://") and pat:
    auth_url = CLONE_URL.replace("https://", f"https://{pat}@")
    subprocess.run(["git", "clone", auth_url, WORKDIR], check=True, capture_output=True)
    push_url = auth_url
elif CLONE_URL.startswith("git@"):
    subprocess.run(["git", "clone", CLONE_URL, WORKDIR], check=True, capture_output=True)
    push_url = CLONE_URL
else:
    print("Cannot clone: no valid URL")
    exit(1)

print(f"Cloned: {CLONE_URL}")

# ── Copy skill into repo ──
dest = os.path.join(WORKDIR, "gateway-restart-with-notification")
if os.path.exists(dest):
    shutil.rmtree(dest)
shutil.copytree(SKILL_DIR, dest)

# ── Git commit & push ──
os.chdir(WORKDIR)
subprocess.run(["git", "add", "."], check=True, capture_output=True)
subprocess.run(["git", "commit", "-m", "Add gateway-restart-with-notification skill"],
               check=True, capture_output=True)
subprocess.run(["git", "push", push_url], check=True, capture_output=True)

print(f"\n✅ Done!")
print(f"📦 Repo: https://github.com/{GH_USER}/{REPO_NAME}")
print(f"📥 Install:")
print(f"   hermes skills install https://raw.githubusercontent.com/{GH_USER}/{REPO_NAME}/main/gateway-restart-with-notification/SKILL.md")
