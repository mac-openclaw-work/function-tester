---
name: reborn
description: 重生技能 - OpenClaw workspace 完整生命周期管理：备份到 GitHub + Gitee + CNB 三仓库、从备份恢复、验证完整性、查看历史记录。触发条件：(1) 用户要求备份、恢复、重生 workspace；(2) 手动或定时触发三仓库备份；(3) 验证备份完整性。
仓库地址：
- GitHub: https://github.com/mac-openclaw-work/function-tester
- Gitee: https://gitee.com/mac-openclaw-work/function-tester
- CNB: https://cnb.cool/mac-openclaw/work/function-tester
---

# 🔥 重生 Skill

让你的 OpenClaw 实现完整的**双仓库生命周期管理**：同时备份到 GitHub + Gitee，支持一键恢复。

## 核心能力

- **双仓库并行备份**：一句话同时推送到 GitHub + Gitee
- **一键恢复**：从任一仓库快速还原完整 workspace
- **冲突处理**：备份前自动拉取最新代码，避免仓库冲突
- **安全恢复**：恢复前自动备份当前状态到 `.pre-reborn/` 目录
- **完整性验证**：自动检查关键文件（IDENTITY.md、USER.md、SOUL.md、MEMORY.md）
- **操作历史**：自动记录所有操作到当日记忆文件

## 使用方法

### 首次配置（一次性）

```bash
python3 skills/reborn/reborn.py init-config \
  <github_url> <github_token> \
  <gitee_url> <gitee_token>
```

**示例：**
```bash
python3 skills/reborn/reborn.py init-config \
  "https://github.com/你的用户名/your-repo.git" \
  "<GITHUB_PAT>" \
  "https://gitee.com/你的用户名/your-repo.git" \
  "your-gitee-token"
```

配置自动保存到 `~/.openclaw/config/reborn-repos.json`。

### 双仓库备份（日常使用）

```bash
python3 skills/reborn/reborn.py backup-dual
```

同时推送到 GitHub 和 Gitee，自动处理 token 认证。

### 从备份恢复

```bash
python3 skills/reborn/reborn.py reborn <repo_url> <token>
```

### 验证备份完整性

```bash
python3 skills/reborn/reborn.py verify <repo_url> <token>
```

### 查看操作历史

```bash
python3 skills/reborn/reborn.py history
```

## 工作流程

```
backup-dual 命令
      │
      ▼
配置 remotes（origin → GitHub, gitee → Gitee）
      │
      ▼
  Git 初始化（如需要）
      │
      ▼
  拉取最新代码（双仓库）
      │
      ▼
  git add + git commit
      │
      ▼
  同时推送到 GitHub + Gitee
      │
      ▼
  记录到当日 memory 文件
```

## 配置说明

### 前置条件

1. **GitHub 私有仓库**（建议）
2. **Gitee 私有仓库**（国内镜像，加速）
3. **GitHub PAT**：具有 `repo` 权限
4. **Gitee PAT**：具有仓库拉取和推送权限
5. **本地 git**：OpenClaw 环境默认已安装

### 关键文件验证

备份和恢复时自动验证以下关键文件：
- IDENTITY.md
- USER.md
- SOUL.md
- MEMORY.md

## 备份范围

**自动备份的内容：**
- 所有 `.md` 配置文件（SOUL.md / USER.md / IDENTITY.md / MEMORY.md 等）
- 所有自定义 Skill 目录
- memory 目录下的所有记忆文件
- workspace 下的所有项目数据

**自动忽略的内容：**
- 临时文件、缓存、日志（`*.tmp`, `*.log`, `*.temp`）
- 依赖目录（`node_modules/`、`vendor/`、`__pycache__/`）
- 敏感配置文件（`.env`、`.secrets` 等）
- 编辑器配置（`.idea/`、`.vscode/` 等）

## 恢复流程

```
reborn 命令
     │
     ▼
备份当前 workspace 到 .pre-reborn/
     │
     ▼
克隆备份仓库到临时目录
     │
     ▼
验证关键文件完整性
     │
     ▼
覆盖当前 workspace
     │
     ▼
记录操作到当日 memory 文件
     │
     ▼
清理临时文件
```

## 注意事项

### ⚠️ 重要警告

1. **不可逆操作**：恢复会完全覆盖当前 workspace，执行前请确认
2. **备份验证**：首次恢复前建议先用 `verify` 命令检查备份完整性
3. **Git 状态**：如果当前 workspace 有未提交的变更，恢复前会被提交
4. **技能刷新**：恢复后需要重启 OpenClaw 才能加载新恢复的技能

### 推荐工作流

1. 首次使用 `init-config-triple` 配置 GitHub + Gitee + CNB 三仓库
2. 定期执行 `backup-triple` 保持三仓库同步
3. 数据损坏或换机器时，用 `reborn` 一键还原（支持任一仓库恢复）

## 技术细节

| 项目 | 路径 |
|------|------|
| 备份仓库配置 | `reborn.py` 同目录 `reborn-repos.json`（首次使用请填写 `reborn-repos.json.example`）|
| Workspace 路径 | `reborn.py` 顶部 `WORKSPACE_PATH` 变量（可配置）|
| Gitee 凭证 | `/root/.git-credentials` |
| 临时克隆目录 | `/tmp/openclaw-reborn-{timestamp}/` |
| 恢复前备份 | `workspace/.pre-reborn/` |
| 操作日志 | `/tmp/openclaw-reborn.log` |

## 版本信息

- **版本**：v3.3（配置文件内置版）
- **更新日期**：2026-05-18
- **说明**：配置文件 `reborn-repos.json` 放在 skill 目录内（随 skill 迁移），Workspace 路径在 `WORKSPACE_PATH` 中填写
- **兼容性**：OpenClaw 全版本
- **依赖**：git、python3
