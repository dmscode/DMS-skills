# 项目记忆协议

版本：0.1.0

## 1. 目标与非目标

本协议通过普通文件实现跨 Agent 连续性、来源追溯、渐进式整理、冲突可见和人工可审计。它不承诺某个 Agent 能访问其他产品的隐藏对话、私有思维链或当前环境未暴露的工具事件；不要求向量数据库、网络服务或厂商记忆 API。

## 2. 建议的规范目录

```text
project-root/
├── AGENTS.md                         # 高注意力项目记忆
├── memory.md                         # 次级经验库
└── memory/
    ├── README.md                     # 本地策略、范围和隐私提醒
    ├── INDEX.md                      # 当前记忆导航索引
    ├── ledger.jsonl                  # 追加式生命周期事件
    ├── sessions/
    │   └── YYYY-MM/<session-id>.jsonl # 追加式会话历史
    ├── records/                      # 可选的详细记忆条目（MEM-*.md）
    ├── decisions/                    # 可选的决策记录或链接
    └── archive/                      # 旧视图与已退役导出
```

只在需要时创建空目录。优先沿用项目已有的文档/ADR 习惯，避免建立竞争性的第二套知识源。这是推荐协议，而不是声称所有文件名均为行业标准。

### 2.1 原始来源与当前视图

- `sessions/**/*.jsonl` 是当时实际归档的、当前可访问会话内容的历史来源。会话关闭后原则上不可变；只有按规则执行隐私删减或更正时例外。
- `ledger.jsonl` 是追加式事件流。每次改变记忆项的内容或状态都追加新事件。每个事件携带变更后的完整快照，因此取每个 `memory_id` 的最新事件即可重建当前状态。
- `INDEX.md` 是便于人阅读的导航视图，应可由账本的最新快照重建；它可以总结，但不能代替证据。
- `memory.md` 和 `AGENTS.md` 是经过筛选的当前视图。晋升、纠正或降级记忆时更新它们，并在每条知识旁保留稳定 ID。
- `records/` 用于存放放不进 `memory.md` 的详细说明，例如复现步骤。账本保留摘要、状态和指向详细记录的链接。

同一条知识不应在多个文件里全文重复。用 ID 和链接连接各层。

## 3. 注意力分层

### A 层：`AGENTS.md`（高注意力）

仅加入稳定且高影响、会实质改变多数工作方式，或对某个范围明确的关键子系统具有决定性影响的内容，例如：

- 必须执行的验证命令、构建/测试约束；
- 硬性架构边界、规范事实源；
- 安全、隐私、破坏性操作、迁移或发布约束；
- 仍然有效且应由 Agent 遵循的维护者明确决定；
- 针对具体目录但影响重大的模块规则。

不要放时间线式工作日记、长篇教程、未经验证的诊断、普通状态、猜测或所有个人偏好。优先链接到 `memory.md`、ADR 或详细记录。保持简洁；如果 `AGENTS.md` 明显膨胀，应整理并将细节迁出，不要把它变成记忆垃圾场。

### B 层：根目录 `memory.md`（次级记忆）

放置跨会话有用，但不必在每个任务中都作为强提醒加载的稳定知识：

- 重复出现的坑和已知失败模式；
- 调试方法与已验证的变通方案；
- 不明显的领域背景或实现细节；
- 项目相关的反复偏好；
- 不够重要、不适合作为强制规则的经验与限制；
- 指向 ADR、详细记录或源会话的短链接。

每条记录包含 `MEM-*` ID、状态、适用范围、结论、置信度、更新时间和证据链接。候选或不确定内容必须明确标记；通常先留在 `memory/INDEX.md`，没有必要不要立刻写入 `memory.md`。

### C 层：`memory/`（证据和细节历史）

保存 JSONL 会话、生命周期账本、索引、可选详细记录、证据链接、交接信息和退役视图。这是可检索的历史层，不应在每个任务中整份加入上下文。

## 4. 稳定标识符

- 会话 ID：`S-YYYYMMDD-<短名称>-<随机串或计数器>`；在项目内保持唯一。
- 消息 ID：每个会话内部从 `MSG-000001` 开始递增。
- 记忆 ID：`MEM-YYYYMMDD-NNNN` 或其他唯一的 `MEM-*` 格式。
- 账本事件 ID：`MEVT-YYYYMMDD-NNNNN` 或其他唯一的 `MEVT-*` 格式。

记忆被拒绝或退役后，也不得复用原 ID。ID 标识一个知识主张及其历史链，而不只是某一版措辞。如果主张含义实质改变，应创建新 ID 并将旧项标为被取代；轻微澄清可以在保留旧账本快照的前提下修订同一 ID。

## 5. 记忆记录字段

每个当前记忆快照应至少包含：

- `title`：简短、可搜索的标题；
- `kind`：`project_fact`、`decision`、`constraint`、`pitfall`、`lesson`、`workflow`、`open_question`、`preference`、`hypothesis` 或 `work_state`；
- `status`：`candidate`、`verified`、`in_memory`、`in_agents`、`superseded`、`rejected` 或 `archived`；
- `claim`：简洁的结论，明确表达不确定性和限制；
- `scope`：项目、模块/路径、环境、版本或时间范围；
- `confidence`：`low`、`medium` 或 `high`；
- `importance`：`low`、`medium` 或 `high`；
- `stability`：`volatile`、`recurring` 或 `durable`；
- `evidence_refs`：来源引用；已验证或晋升的条目必须包含可访问的证据；
- `created_at`、`updated_at`：ISO-8601 时间戳；
- `valid_until`：到期时间戳或 `null`；
- `related_ids`：相关记忆 ID 列表；
- `destination`：例如 `memory/INDEX.md`、`memory.md`、`AGENTS.md`、`docs/decisions/ADR-005.md` 或 `memory/records/MEM-....md`；
- `superseded_by`：替代它的新记忆 ID，或 `null`。

账本事件需要记录完整 `record` 快照以及变更原因。事件行只追加；不得为了“修好”旧记录而直接修改历史行。

## 6. 证据引用

优先使用以下形式：

- 对话消息：`memory/sessions/2026-10/S-20261019-cache-a1b2.jsonl#MSG-000007`
- 当前源文件：`src/cache/adapter.ts#L40-L65`（行号可能变化；重要结论也应注明 Git commit 或内容校验和）
- 测试证据：`tests/cache.test.ts::test_redis_fallback`，并注明测试的 commit 或执行日期/结果
- 决策记录：`docs/decisions/ADR-005.md`
- 用户批准：对应的会话消息 ID

引用只是到达证据的路径，不是证据本身。避免引用失效链接或没有路径的行号。如果会话只是摘要而非完整记录，引用不得暗示原始对话仍然存在。

## 7. 分类和生命周期

典型状态路径：

`candidate → verified → in_memory → in_agents`

并非每条记忆都要经过全部状态。其他历史/终态为 `superseded`、`rejected`、`archived`。

- **candidate：**提取出来但尚未充分验证或解决冲突的候选条目。
- **verified：**证据和范围足够清晰，可供后续参考；不代表一定要晋升。
- **in_memory：**已在根目录 `memory.md` 中表达。
- **in_agents：**已进入 `AGENTS.md`，因为它值得高注意力提醒。
- **superseded：**被更新、更准确或范围更窄的新结论取代；保留历史，并填写 `superseded_by`。
- **rejected：**审查后被证明错误或明确决定不采纳；账本保留原因，但不得作为当前指引。
- **archived：**不再活跃、仅用于历史审计的记录。

允许的语义状态变更：

- `create`：创建新 ID，状态必须为 `candidate`。
- `verify`：`candidate` → `verified`，需要新证据或更强的验证，并写明原因。
- `revise`：修订措辞、范围、证据或元数据，但不能静默改变主张含义；状态保持合适。
- `promote_memory`：`verified` → `in_memory`。
- `promote_agents`：`verified` 或 `in_memory` → `in_agents`。
- `supersede`：活跃记录 → `superseded`，并写明替代 ID 与原因。
- `reject`：`candidate` 或 `verified` → `rejected`，必须说明原因。
- `archive`：`superseded` 或 `rejected` → `archived`。
- `reopen`：只有新证据足以重新评估时，才可把历史记录恢复为 `candidate`；必须写明原因，不能抹除历史状态。

若记忆的含义实质变化，创建新 ID，不要只用 `revise`。

## 8. 晋升门槛

在将记录改为 `verified` 前，回答：

1. 这条记忆的精确主张是什么？
2. 依据是什么，下一位 Agent 能否访问该依据？
3. 它是直接观察、用户决定、测试结果、推断还是提议？
4. 有哪些模块、版本、环境或时间限制？
5. 它是否与当前代码、测试、批准的决策或更新的用户要求冲突？
6. 它是否有复用价值，是否已被其他规范知识覆盖？

晋升到 `memory.md` 前，应确认它对未来会话有实际用处，而非只服务于当前任务。晋升到 `AGENTS.md` 还要求它稳定、高影响，且值得持续强提醒。单次观察通常不适合进入 `AGENTS.md`，除非它揭示关键的安全或正确性约束。

## 9. 时效性知识

对可能过期的知识记录绝对日期、版本和环境范围；可行时填写 `valid_until`。复用临时 Bug 状态、依赖行为、部署状态或任务进度时，应检查当前代码、配置、测试、发布说明或其他现时证据。过去正确不代表现在仍然正确。

## 10. 文件一致性

- `ledger.jsonl` 中状态为 `in_memory` 的记录，必须以相同 `MEM-*` ID 出现在 `memory.md`。
- 状态为 `in_agents` 的记录，必须以相同 ID 出现在 `AGENTS.md`。
- 当前 `INDEX.md` 应列出每个非终态条目（`candidate`、`verified`、`in_memory`、`in_agents`）和其位置。
- 被取代或拒绝的记录不得继续以无条件的当前指令形式留在 `AGENTS.md` 或 `memory.md`。
- 索引和根目录文件是当前视图，不是账本的替代品。未实际验证时，不得声称记忆结构一致。

## 11. 保留策略与规模扩展

原始会话按月、按会话拆分，不要把所有历史塞进一个巨型文件。优先用普通文本搜索（`rg`、`grep` 或 Agent 自带的检索）。只有当关键词搜索和索引确实无法满足需求时，才考虑向量检索或数据库。除非项目的明确保留政策要求删除，否则归档旧视图，不删除证据。
