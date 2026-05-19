#!/usr/bin/env python3
"""
重生技能 - 独立备份与恢复脚本
支持同时备份到 GitHub + Gitee 双仓库
"""
import os
import sys
import subprocess
import shutil
import json
import fnmatch
from datetime import datetime
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────────
WORKSPACE_PATH = os.path.expanduser("/Users/zonkiddshao/.openclaw-work/workspace-work/")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reborn-repos.json")
CREDENTIAL_FILE = os.path.expanduser("~/.git-credentials")
ENV_FILE = os.path.expanduser("~/.openclaw/workspace-work/.env")

# ══════════════════════════════════════════════════════════════
# ⚙️  配置文件：reborn-repos.json（位于本脚本同目录下）
#    首次使用请填写本目录下的 reborn-repos.json
# ══════════════════════════════════════════════════════════════
LOG_PATH = "/tmp/openclaw-reborn.log"
PRE_REBORN_DIR = os.path.join(WORKSPACE_PATH, ".pre-reborn")

# 需要验证的关键文件
KEY_FILES = ["IDENTITY.md", "USER.md", "SOUL.md", "MEMORY.md"]

# 忽略的文件和目录
IGNORE_PATTERNS = [
    "*.tmp", "*.log", "*.temp", ".DS_Store", "Thumbs.db",
    ".cache", ".temp", "tmp/",
    "node_modules/", "vendor/", "__pycache__/",
    ".env", ".env.local", "*.env", ".secrets",
    ".fuse_hidden*", ".directory", ".Trash-*", ".nfs*",
    ".idea/", ".vscode/", "*.swp", "*.swo", "*~",
    ".pre-reborn/", "参赛材料/", "参赛提交/",
    ".pre-reincarnation/"
]

# ── 日志 ──────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

# ── 工具函数 ─────────────────────────────────────────────────
def should_ignore(filename: str) -> bool:
    for pat in IGNORE_PATTERNS:
        if pat.endswith("/"):
            if filename.startswith(pat.rstrip("/")):
                return True
        else:
            if fnmatch.fnmatch(filename, pat):
                return True
    return False

def load_repos_config() -> dict:
    """从 skill 内 reborn-repos.json 加载配置。"""
    if not os.path.exists(CONFIG_PATH):
        print(f"⚠️  配置文件不存在: {CONFIG_PATH}")
        print("   请复制 reborn-repos.json.example 为 reborn-repos.json 并填写配置")
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def ensure_git_initialized():
    """确保 Git 仓库已初始化。"""
    git_dir = os.path.join(WORKSPACE_PATH, ".git")
    if not os.path.exists(git_dir):
        subprocess.run(["git", "init"], cwd=WORKSPACE_PATH, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "OpenClaw Reborn Bot"],
            cwd=WORKSPACE_PATH, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "reborn@openclaw.local"],
            cwd=WORKSPACE_PATH, check=True, capture_output=True
        )
        log("Git 仓库初始化完成")
    # 确保 .gitignore 存在
    gi_path = os.path.join(WORKSPACE_PATH, ".gitignore")
    if not os.path.exists(gi_path):
        with open(gi_path, "w") as f:
            f.write("\n".join(IGNORE_PATTERNS) + "\n")

def configure_gitee_credential(repo_url: str, token: str):
    """
    配置 Gitee 的 credential helper。
    GitHub 使用 URL 内嵌 token 的方式推送（git remote 已处理），
    Gitee 必须通过 credential helper。
    """
    # 写入 .git-credentials
    os.makedirs(os.path.dirname(CREDENTIAL_FILE), exist_ok=True)
    cred_url = f"https://{token}@gitee.com"
    # 保留现有 credential（如果有 github 条目）
    existing = ""
    if os.path.exists(CREDENTIAL_FILE):
        with open(CREDENTIAL_FILE, "r") as f:
            existing = f.read()
    if cred_url not in existing:
        with open(CREDENTIAL_FILE, "a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(cred_url + "\n")

    # 配置 git credential helper
    subprocess.run(
        ["git", "config", "credential.helper", "store"],
        cwd=WORKSPACE_PATH, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "credential.useHttpPath", "true"],
        cwd=WORKSPACE_PATH, check=True, capture_output=True
    )
    log("Gitee credential helper 配置完成")

def configure_remotes(config: dict):
    """
    配置 git remote：
    - origin  → GitHub（含 token）
    - gitee   → Gitee（credential helper）
    - cnb     → CNB（cnb.cool，含 token）
    """
    ensure_git_initialized()

    gh_url = config.get("github", {}).get("url", "")
    gh_token = config.get("github", {}).get("token", "")
    gitee_url = config.get("gitee", {}).get("url", "")
    gitee_token = config.get("gitee", {}).get("token", "")
    cnb_url = config.get("cnb", {}).get("url", "")
    cnb_token = config.get("cnb", {}).get("token", "")

    # 清理旧 remote
    for name in ["origin", "gitee", "cnb"]:
        subprocess.run(["git", "remote", "remove", name],
                       cwd=WORKSPACE_PATH, capture_output=True)

    # 设置 GitHub remote（含 token）
    if gh_url and gh_token:
        auth_url = gh_url.replace("https://", f"https://{gh_token}@")
        subprocess.run(
            ["git", "remote", "add", "origin", auth_url],
            cwd=WORKSPACE_PATH, check=True, capture_output=True
        )
        log(f"GitHub remote 配置完成: {gh_url}")

    # 设置 Gitee remote（Gitee 用 Basic Auth: username:token@）
    if gitee_url and gitee_token:
        # Gitee HTTPS Git 需要 username:token 格式，token 对应的用户名通过 API 获得
        gitee_api_token = gitee_token  # token 本身
        # 先查 token 对应的 username
        try:
            result = subprocess.run(
                ["curl", "-s", "-H", f"Authorization: token {gitee_api_token}",
                 "https://gitee.com/api/v5/user"],
                capture_output=True, text=True, check=True
            )
            import json as json_lib
            user_info = json_lib.loads(result.stdout)
            gitee_username = user_info.get("login", "")
        except Exception:
            gitee_username = ""  # fallback
        auth_url = gitee_url.replace("https://", f"https://{gitee_username}:{gitee_api_token}@")
        subprocess.run(
            ["git", "remote", "add", "gitee", auth_url],
            cwd=WORKSPACE_PATH, check=True, capture_output=True
        )
        log(f"Gitee remote 配置完成: {gitee_url}")

    # 设置 CNB remote（cnb.cool）
    if cnb_url and cnb_token:
        auth_url = cnb_url.replace("https://", f"https://cnb:{cnb_token}@")
        subprocess.run(
            ["git", "remote", "add", "cnb", auth_url],
            cwd=WORKSPACE_PATH, check=True, capture_output=True
        )
        log(f"CNB remote 配置完成: {cnb_url}")

    # 确保 main 分支
    subprocess.run(["git", "branch", "-M", "main"],
                   cwd=WORKSPACE_PATH, capture_output=True)

# ── 备份当前 workspace ────────────────────────────────────────
def backup_current_workspace():
    log("备份当前 workspace 到 .pre-reborn ...")
    if os.path.exists(PRE_REBORN_DIR):
        shutil.rmtree(PRE_REBORN_DIR)
    os.makedirs(PRE_REBORN_DIR, exist_ok=True)

    for item in os.listdir(WORKSPACE_PATH):
        if should_ignore(item):
            continue
        src = os.path.join(WORKSPACE_PATH, item)
        dst = os.path.join(PRE_REBORN_DIR, item)
        try:
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                log(f"  备份文件: {item}")
            elif os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", ".DS_Store"))
                log(f"  备份目录: {item}/")
        except Exception as e:
            log(f"  ⚠️  备份 {item} 出错: {e}")
    log("当前 workspace 备份完成")

# ── 克隆仓库 ─────────────────────────────────────────────────
def clone_backup_repo(repo_url: str, token: str, verify_only: bool = False) -> str:
    log(f"开始克隆备份仓库: {repo_url}")
    auth_url = repo_url.replace("https://", f"https://{token}@") if "@" not in repo_url else repo_url

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = f"/tmp/openclaw-reborn-{ts}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        subprocess.run(
            ["git", "clone", auth_url, temp_dir],
            capture_output=True, text=True, check=True
        )
        log("仓库克隆成功")

        missing = [f for f in KEY_FILES if not os.path.exists(os.path.join(temp_dir, f))]
        if missing:
            log(f"⚠️  备份不完整，缺少: {', '.join(missing)}")
            if not verify_only:
                raise Exception(f"备份验证失败，缺少关键文件: {', '.join(missing)}")
        else:
            log("✅ 备份验证通过，所有关键文件完整")
        return temp_dir
    except subprocess.CalledProcessError as e:
        raise Exception(f"仓库克隆失败: {e.stderr}")

# ── 恢复 ──────────────────────────────────────────────────────
def restore_from_backup(backup_dir: str):
    log("开始恢复 workspace ...")
    for item in os.listdir(backup_dir):
        src = os.path.join(backup_dir, item)
        dst = os.path.join(WORKSPACE_PATH, item)
        try:
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                log(f"  恢复文件: {item}")
            elif os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                log(f"  恢复目录: {item}/")
        except Exception as e:
            log(f"  ⚠️  恢复 {item} 出错: {e}")
    log("workspace 恢复完成")

# ── 记录操作 ─────────────────────────────────────────────────
def record_operation(operation_type: str, repo_url: str):
    log(f"记录 {operation_type} 操作到记忆文件 ...")
    memory_dir = os.path.join(WORKSPACE_PATH, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = os.path.join(memory_dir, f"{today}.md")

    existing = ""
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            existing = f.read()

    if operation_type == "备份":
        record = f"""
## 备份操作
- 备份时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 备份目标：{repo_url}
- 状态：✅ 备份成功

"""
    else:
        record = f"""
## 重生操作
- 重生时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 备份来源：{repo_url}
- 状态：✅ 重生成功

"""
    with open(memory_file, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(record)
    log(f"{operation_type} 记录已写入记忆文件")

# ── 双仓库备份 ────────────────────────────────────────────────
def backup_to_triple_repos(config: dict):
    """
    同时备份到 GitHub + Gitee + CNB 三仓库。
    配置通过 config dict 传入，格式：
    {
      "github": {"url": "...", "token": "..."},
      "gitee": {"url": "...", "token": "..."},
      "cnb":   {"url": "...", "token": "..."}   # token 可选，会从 CNB_COOL_GIT_TOKEN 自动读取
    }
    """
    log("=== 开始三仓库备份 ===")
    configure_remotes(config)

    os.chdir(WORKSPACE_PATH)

    try:
        # 拉取最新代码避免冲突
        log("拉取最新代码（GitHub）...")
        subprocess.run(["git", "fetch", "origin"],
                       capture_output=True, text=True)
        subprocess.run(["git", "checkout", "main"],
                       capture_output=True)
        subprocess.run(["git", "pull", "origin", "main", "--quiet"],
                       capture_output=True, text=True)

        log("拉取最新代码（Gitee）...")
        subprocess.run(["git", "fetch", "gitee"],
                       capture_output=True, text=True)
        subprocess.run(["git", "pull", "gitee", "main", "--quiet"],
                       capture_output=True, text=True)

        cnb_url = config.get("cnb", {}).get("url", "")
        if cnb_url:
            log("拉取最新代码（CNB）...")
            subprocess.run(["git", "fetch", "cnb"],
                           capture_output=True, text=True)
            subprocess.run(["git", "pull", "cnb", "main", "--quiet"],
                           capture_output=True, text=True)

        # 添加所有变更
        log("添加文件变更 ...")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)

        status = subprocess.run(["git", "status", "--porcelain"],
                                capture_output=True, text=True)
        if not status.stdout.strip():
            log("ℹ️  没有变更，无需备份")
            return

        commit_msg = f"auto backup: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg, "--quiet"],
                       check=True, capture_output=True)

        # 推送到三仓库
        results = {}
        for remote in ["origin", "gitee"]:
            log(f"推送到 {remote} ...")
            result = subprocess.run(
                ["git", "push", remote, "main", "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                log(f"  ✅ {remote} 推送成功")
                results[remote] = "success"
            else:
                log(f"  ❌ {remote} 推送失败: {result.stderr}")
                results[remote] = f"error: {result.stderr}"

        if cnb_url:
            log("推送到 CNB ...")
            result = subprocess.run(
                ["git", "push", "cnb", "main", "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                log(f"  ✅ cnb 推送成功")
                results["cnb"] = "success"
            else:
                log(f"  ❌ cnb 推送失败: {result.stderr}")
                results["cnb"] = f"error: {result.stderr}"

        all_ok = all(v == "success" for v in results.values())
        if all_ok:
            log_msg = f"✅ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 三仓库备份成功"
            print(log_msg)
            record_operation("备份", "GitHub + Gitee + CNB 三仓库")
        else:
            log(f"⚠️  部分仓库推送失败: {results}")
            raise Exception(f"部分仓库推送失败: {results}")

    except subprocess.CalledProcessError as e:
        raise Exception(f"备份失败: {e.stderr.decode() if e.stderr else e}")

# ── 验证 ──────────────────────────────────────────────────────
def verify_backup(repo_url: str, token: str):
    log("=== 备份验证模式 ===")
    try:
        temp_dir = clone_backup_repo(repo_url, token, verify_only=True)
        log("=== 备份内容清单 ===")
        for item in sorted(os.listdir(temp_dir)):
            kind = "📁" if os.path.isdir(os.path.join(temp_dir, item)) else "📄"
            log(f"  {kind} {item}")
        log("✅ 备份验证完成")
        shutil.rmtree(temp_dir)
    except Exception as e:
        log(f"❌ 备份验证失败: {e}")
        sys.exit(1)

# ── 重生恢复 ─────────────────────────────────────────────────
def reborn(repo_url: str, token: str):
    log("=== 开始重生恢复 ===")
    try:
        backup_current_workspace()
        backup_dir = clone_backup_repo(repo_url, token)
        restore_from_backup(backup_dir)
        record_operation("重生", repo_url)
        shutil.rmtree(backup_dir)
        log("=== ✅ 重生恢复成功 ===")
        log("💡 提示：请重启 OpenClaw 以加载恢复的技能")
    except Exception as e:
        log(f"❌ 重生恢复失败: {e}")
        log(f"🔧 当前 workspace 已备份到: {PRE_REBORN_DIR}")
        sys.exit(1)

# ── 历史记录 ─────────────────────────────────────────────────
def show_history():
    memory_dir = os.path.join(WORKSPACE_PATH, "memory")
    if not os.path.exists(memory_dir):
        log("未找到记忆目录")
        return
    log("=== 操作历史记录 ===")
    for filename in sorted(os.listdir(memory_dir), reverse=True):
        if filename.endswith(".md"):
            filepath = os.path.join(memory_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if "备份操作" in content or "重生操作" in content:
                    for line in content.split("\n"):
                        if "备份操作" in line or "重生操作" in line:
                            log(f"\n📅 {filename}")
                            break

# ── 主入口 ─────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python reborn.py backup-dual                   # 双仓库备份 GitHub+Gitee（需先 init-config）")
        print("  python reborn.py backup-triple                 # 三仓库备份 GitHub+Gitee+CNB（需先 init-config-triple）")
        print("  python reborn.py backup <repo_url> <token>     # 备份到单仓库")
        print("  python reborn.py reborn <repo_url> <token>     # 从备份恢复")
        print("  python reborn.py verify <repo_url> <token>     # 验证备份")
        print("  python reborn.py history                       # 查看历史")
        print("  python reborn.py init-config <github_url> <gh_token> <gitee_url> <gitee_token>  # 初始化双仓库配置")
        print("  python reborn.py init-config-triple <github_url> <gh_token> <gitee_url> <gitee_token> <cnb_url>  # 初始化三仓库配置")
        sys.exit(1)

    action = sys.argv[1]

    try:
        if action == "backup-dual":
            config = load_repos_config()
            if not config.get("github") or not config.get("gitee"):
                log("❌ 双仓库配置未完成，请先运行 init-config 初始化配置")
                log(f"   配置路径: {CONFIG_PATH}")
                sys.exit(1)
            backup_to_triple_repos(config)

        elif action == "backup-triple":
            config = load_repos_config()
            if not config.get("github") or not config.get("gitee"):
                log("❌ 三仓库配置未完成，请先运行 init-config-triple 初始化配置")
                log(f"   配置路径: {CONFIG_PATH}")
                sys.exit(1)
            backup_to_triple_repos(config)

        elif action == "init-config":
            if len(sys.argv) < 6:
                print("参数错误: python reborn.py init-config <github_url> <gh_token> <gitee_url> <gitee_token>")
                sys.exit(1)
            gh_url, gh_token, gitee_url, gitee_token = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
            config = {
                "github": {"url": gh_url, "token": gh_token},
                "gitee": {"url": gitee_url, "token": gitee_token}
            }
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=2)
            log(f"✅ 双仓库配置已保存到: {CONFIG_PATH}")
            backup_to_triple_repos(config)

        elif action == "init-config-triple":
            if len(sys.argv) < 7:
                print("参数错误: python reborn.py init-config-triple <github_url> <gh_token> <gitee_url> <gitee_token> <cnb_url>")
                print("   cnb_url 示例: https://cnb.cool/<USER>/<REPO>")
                sys.exit(1)
            gh_url, gh_token, gitee_url, gitee_token, cnb_url = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
            saved_config = load_repos_config()
            cnb_saved_token = saved_config.get("cnb", {}).get("token", "")
            config = {
                "github": {"url": gh_url, "token": gh_token},
                "gitee": {"url": gitee_url, "token": gitee_token},
                "cnb":   {"url": cnb_url,   "token": cnb_saved_token}
            }
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=2)
            log(f"✅ 三仓库配置已保存到: {CONFIG_PATH}")
            backup_to_triple_repos(config)

        elif action == "backup":
            if len(sys.argv) < 4:
                print("参数错误: python reborn.py backup <repo_url> <token>")
                sys.exit(1)
            single_config = {
                "github": {"url": sys.argv[2], "token": sys.argv[3]}
            }
            backup_to_triple_repos(single_config)

        elif action == "reborn":
            if len(sys.argv) < 4:
                print("参数错误: python reborn.py reborn <repo_url> <token>")
                sys.exit(1)
            reborn(sys.argv[2], sys.argv[3])

        elif action == "verify":
            if len(sys.argv) < 4:
                print("参数错误: python reborn.py verify <repo_url> <token>")
                sys.exit(1)
            verify_backup(sys.argv[2], sys.argv[3])

        elif action == "history":
            show_history()

        else:
            print(f"未知操作: {action}")
            sys.exit(1)

    except KeyboardInterrupt:
        log("\n⚠️  操作被中断")
        sys.exit(1)
    except Exception as e:
        log(f"❌ 操作失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
