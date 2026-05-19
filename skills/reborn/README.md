# 重生 Skill

让OpenClaw实现完整的生命周期管理能力，支持备份和恢复。

## 核心功能

1. **一键备份**：将workspace备份到GitHub私有仓库
2. **一键恢复**：从GitHub快速恢复完整workspace
3. **自动验证**：检查备份完整性
4. **历史记录**：查看所有操作历史

## 使用场景

- **服务器迁移**：2分钟完成，100%数据恢复
- **数据损坏恢复**：1分30秒恢复所有数据
- **多环境同步**：实时同步测试和生产环境
- **灾难恢复**：快速恢复业务运营

## 使用方法

### 备份
```
帮我备份到GitHub，仓库地址是https://github.com/你的用户名/your-backup-repo.git，GitHub PAT是你的访问令牌
```

### 恢复
```
帮我从GitHub恢复，仓库地址是https://github.com/你的用户名/your-backup-repo.git，GitHub PAT是你的访问令牌
```

### 验证
```
验证一下GitHub备份，仓库地址是https://github.com/你的用户名/your-backup-repo.git，GitHub PAT是你的访问令牌
```

### 查看历史
```
查看备份和恢复的历史记录
```

## 安装方法

1. 将 `reborn-skill` 文件夹复制到 `skills/` 目录
2. 重启OpenClaw

## 性能指标

- 小规模workspace（<10MB）：备份/恢复 < 30秒
- 中等规模workspace（10-100MB）：备份/恢复 1-3分钟
- 大规模workspace（>100MB）：备份/恢复 3-10分钟

## 注意事项

⚠️ **重要警告**：
1. 恢复操作不可逆，会覆盖当前workspace
2. 首次恢复前建议先用验证命令检查备份
3. 恢复后需重启OpenClaw加载技能
4. 建议定期备份，保持数据安全

---

**技能作者**：原味虾🤟
**创建时间**：2026-04-02

让OpenClaw实现真正的长生不老！🦐✨
