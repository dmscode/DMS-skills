# 记忆目录策略

- `sessions/YYYY-MM/*.jsonl`：追加式归档当前可访问的用户可见对话及工具交互；每行一个 JSON 对象。
- `ledger.jsonl`：追加式生命周期事件。每条事件包含变更后的完整记忆快照。
- `INDEX.md`：人类可读的当前导航视图。
- `records/`：可选详细记忆文件，账本记录应指向它们。
- `decisions/`：可选决策记录；如果仓库已有 ADR 约定，应优先沿用。
- `archive/`：退役的当前视图或安全的历史导出，不能用来藏匿当前真相。

## 隐私与 Git

对话日志可能包含专有信息或个人信息。不得保存凭据或隐藏思维链。将原始日志纳入 Git 或共享前，检查仓库可见范围和数据保留规则。本协议不允许自动提交或上传。删除当前文件中的秘密，并不一定意味着 Git 历史或备份中的副本也已删除。

## 证据与状态

每条晋升的知识都应有稳定的 `MEM-*` ID 和证据链接。`candidate` 不等于事实；`verified` 表示已有支持；`in_memory` 和 `in_agents` 标明当前存放层；`superseded`、`rejected`、`archived` 不能作为当前指引。详见技能的 `references/PROTOCOL.md` 与 `references/GOVERNANCE.md`。
