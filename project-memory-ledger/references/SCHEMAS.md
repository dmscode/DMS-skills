# JSONL 数据格式与示例

机器可读的初版 Schema 位于 `schemas/`。以下是协议约定；扩展字段时尽量保持向后兼容。每一物理行都是一个独立 JSON 对象，编码为 UTF-8；不要使用行内尾逗号，也不要把一个 JSON 对象拆成多行。

## 1. 会话 JSONL

路径：`memory/sessions/YYYY-MM/<session-id>.jsonl`。

首条必须是 `session_start`，随后是零条或多条 `message` 记录，最后可选一条 `session_end`。只追加，不重新排序或重写已有消息。正在进行的会话可以暂时没有 `session_end`。

### 开始记录

```json
{"schema_version":"1.0","record_type":"session_start","session_id":"S-20261019-cache-a1b2","started_at":"2026-10-19T01:10:00Z","source_agent":"codex","project":"example-project","capture_status":"in_progress","notes":"开始保存当前可访问的对话。"}
```

### 消息记录

```json
{"schema_version":"1.0","record_type":"message","session_id":"S-20261019-cache-a1b2","message_id":"MSG-000001","sequence":1,"timestamp":"2026-10-19T01:10:10Z","role":"user","speaker":"user","content":"需要保留缓存迁移的发现。","tool_name":null,"tool_call_id":null,"attachments":[],"redactions":[]}
```

`role` 可取 `system`、`developer`、`user`、`assistant` 或 `tool`，但不得保存隐藏的系统/开发者提示词正文或私有思维链。该字段用于标注当前环境实际暴露的可见消息；字段允许某类角色不代表可以突破隐私禁区。`content` 是文本。如果内容由多种结构块组成，应将其整理成尽量保真的可读形式，并在会话备注中说明未能保存的非文本内容。`tool_name` 和 `tool_call_id` 可省略或设为 `null`。

附件元数据可包含安全的相对路径、媒体类型和可选校验和。不要将大型二进制内容或秘密嵌入 JSONL；只有在允许且有用时，才保留从附件提取出的文本。

### 结束记录

```json
{"schema_version":"1.0","record_type":"session_end","session_id":"S-20261019-cache-a1b2","ended_at":"2026-10-19T01:25:00Z","capture_status":"complete","message_count":1,"notes":"已保存所有可访问的用户可见消息和工具交互；凭据删减：无。"}
```

`capture_status` 必须是 `complete`、`partial` 或 `summary_only`。`complete` 仅针对当前可访问的用户可见内容，不包括隐藏提示词和内部推理。如果对话历史已经被上下文截断，应使用 `partial` 或 `summary_only`。

消息 ID 必须稳定。来源引用示例：`memory/sessions/2026-10/S-20261019-cache-a1b2.jsonl#MSG-000001`。`sequence` 必须从 1 开始连续递增。

## 2. 记忆账本 JSONL

路径：`memory/ledger.jsonl`。每行记录一次生命周期事件。`record` 必须携带事件完成后的完整快照，而不是只存差异；这样保留历史的同时，最新状态可确定性重建。

```json
{"schema_version":"1.0","event_id":"MEVT-20261019-00001","timestamp":"2026-10-19T01:26:00Z","memory_id":"MEM-20261019-0001","event_type":"create","actor":"agent:codex","reason":"观察到一条可复用的迁移约束，但仍需验证。","record":{"title":"切换缓存后端前需要先建立适配层","kind":"pitfall","status":"candidate","claim":"当前模块依赖进程内缓存对象，直接替换为 Redis 可能破坏调用方。","scope":"src/cache/；当前分支与依赖版本","confidence":"medium","importance":"high","stability":"recurring","evidence_refs":["memory/sessions/2026-10/S-20261019-cache-a1b2.jsonl#MSG-000001"],"created_at":"2026-10-19T01:26:00Z","updated_at":"2026-10-19T01:26:00Z","valid_until":null,"related_ids":[],"destination":"memory/INDEX.md","superseded_by":null}}
```

合法的 `kind`：

- `project_fact`
- `decision`
- `constraint`
- `pitfall`
- `lesson`
- `workflow`
- `open_question`
- `preference`
- `hypothesis`
- `work_state`

合法的 `status`：`candidate`、`verified`、`in_memory`、`in_agents`、`superseded`、`rejected`、`archived`。

合法的 `event_type`：`create`、`verify`、`revise`、`promote_memory`、`promote_agents`、`supersede`、`reject`、`archive`、`reopen`。

事件语义：

- `create`：创建新记忆 ID，状态为 `candidate`。
- `verify`：候选项获得支持，变成 `verified`。
- `revise`：进行不改变主张本意的澄清/修订；快照必须包含修订后的全部字段。
- `promote_memory`：状态变为 `in_memory`，目标为 `memory.md`。
- `promote_agents`：状态变为 `in_agents`，目标为 `AGENTS.md`。
- `supersede`：状态变为 `superseded`，并填写 `superseded_by`。
- `reject`：状态变为 `rejected`，并记录理由。
- `archive`：状态变为 `archived`。
- `reopen`：基于新证据将状态重新变为 `candidate`，并写明原因。

时间戳使用包含时区的 ISO-8601 格式，建议统一用 UTC `Z`。禁止修改旧账本行；需要更新时，追加携带完整新 `record` 快照的事件。某个 `memory_id` 的当前状态，就是其最新事件中的 `record`。

## 3. 状态含义

- `candidate`：刚提取，尚未充分确认或解决冲突。
- `verified`：证据与范围明确，但未必值得提升到根目录文件。
- `in_memory`：已记录在 `memory.md`。
- `in_agents`：已记录在 `AGENTS.md`。
- `superseded`：被更新或更精确的记录取代。
- `rejected`：被证伪或决定不采纳。
- `archived`：保留作历史追溯，但不再活跃。

Agent 生成了一个合理解释，不等于条目已验证。证据可以是用户明确表达的意图、当前测试结果、源码检查或已批准的文档，但应说明属于哪一种。

## 4. 证据引用示例

```text
memory/sessions/2026-10/S-20261019-cache-a1b2.jsonl#MSG-000007
src/cache/adapter.ts#L40-L65
tests/cache.test.ts::test_redis_fallback（commit 9a31d2f；2026-10-19 通过）
docs/decisions/ADR-005.md
```

对本地会话引用，优先包含确切路径和 `message_id`。行号不够稳定，不应作为唯一定位方式。标准引用中不要出现无意添加的前导空格。
