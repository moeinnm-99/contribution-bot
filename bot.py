import os
import logging
import datetime
import random
import time
from github import Github
from github.GithubException import UnknownObjectException
from github.InputGitAuthor import InputGitAuthor
from github.InputGitTreeElement import InputGitTreeElement

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

# توکن از Secrets گیت‌هاب خوانده می‌شود
GITHUB_TOKEN = os.environ["GH_TOKEN"]
GITHUB_USERNAME = "moeinnm-99"
GITHUB_EMAIL = "moeinnm-99@users.noreply.github.com"

REPO_NAMES = [
    "Todo-List",
    "Backtest",
    "Brain-Tumor-Detection",
    "Driver-Drowsiness-Detection",
    "EDITH",
    "Medical-Chatbot",
    "contribution-bot",   # ریپوی خود بات (برای فعال ماندن)
]
TARGET_FILE = "README.md"

g = Github(GITHUB_TOKEN)
user = g.get_user(GITHUB_USERNAME)

repos = []
for name in REPO_NAMES:
    try:
        repos.append(user.get_repo(name))
        logging.info(f"Connected to: {name}")
    except Exception as e:
        logging.error(f"Cannot access {name}: {e}")

def commit_to_github(repo, file_path, new_content, commit_message, target_datetime):
    default_branch = repo.default_branch
    ref = repo.get_git_ref(f"heads/{default_branch}")
    latest_commit = repo.get_git_commit(ref.object.sha)
    base_tree = latest_commit.tree

    blob = repo.create_git_blob(new_content, "utf-8")
    element = InputGitTreeElement(path=file_path, mode="100644", type="blob", sha=blob.sha)
    new_tree = repo.create_git_tree([element], base_tree)

    date_str = target_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    author = InputGitAuthor(name=GITHUB_USERNAME, email=GITHUB_EMAIL, date=date_str)
    committer = InputGitAuthor(name=GITHUB_USERNAME, email=GITHUB_EMAIL, date=date_str)

    new_commit = repo.create_git_commit(
        message=commit_message, tree=new_tree,
        parents=[latest_commit], author=author, committer=committer
    )
    ref.edit(new_commit.sha)
    return new_commit.sha

def get_initial_file_content(repo, file_path):
    try:
        return repo.get_contents(file_path).decoded_content.decode('utf-8')
    except UnknownObjectException:
        return ""

def run_bot_for_date(target_date):
    if not repos:
        return
    total_commits = random.randint(5, 12)
    adds_count = total_commits // 2
    removes_count = total_commits - adds_count
    logging.info(f"=== Date: {target_date.date()} | total={total_commits} | add={adds_count} | remove={removes_count} ===")

    actions = ['add'] * adds_count + ['remove'] * removes_count
    random.shuffle(actions)
    hours = sorted(random.randint(8, 22) for _ in range(total_commits))
    repo_states = {}

    for i, action in enumerate(actions):
        repo = random.choice(repos)
        repo_name = repo.full_name

        if repo_name not in repo_states:
            repo_states[repo_name] = get_initial_file_content(repo, TARGET_FILE)

        current_content = repo_states[repo_name]

        if action == 'add':
            new_content = current_content + "A\n"
            commit_msg = f"add A ({i+1}/{total_commits})"
        else:
            if "A\n" in current_content:
                new_content = current_content.replace("A\n", "", 1)
                commit_msg = f"remove A ({i+1}/{total_commits})"
            else:
                new_content = current_content + "A\n"
                commit_msg = f"add A - fallback ({i+1}/{total_commits})"
                logging.warning(f"{repo_name}: nothing to remove -> fallback to add")

        commit_time = target_date.replace(hour=hours[i], minute=random.randint(0, 59),
                                          second=random.randint(0, 59), microsecond=0)
        try:
            commit_to_github(repo, TARGET_FILE, new_content, commit_msg, commit_time)
            repo_states[repo_name] = new_content
            logging.info(f"[{repo_name}] OK -> {commit_msg} @ {commit_time.strftime('%H:%M')}")
            time.sleep(1)
        except Exception as e:
            logging.error(f"[{repo_name}] FAILED -> {e}")

# اجرای بات برای امروز
run_bot_for_date(datetime.datetime.now())
