# Project Memory Ledger｜项目记忆账本

一个可移植的 Agent Skill，用普通文件实现项目记忆分层：完整保留当前可访问的对话历史，以追加式账本记录记忆变化，再逐步将经验证的知识晋升到合适的层级。

- `AGENTS.md`：高注意力规则和事实。
- `memory.md`：有长期价值但不必每个任务都强提醒的经验。
- `memory/`：原始会话、证据、追加式记忆账本、索引和详细历史。

本技能采用开放的 Agent Skills 目录格式（`SKILL.md` 加可选 references、schemas、scripts 和模板）。但支持 Skill 格式不代表每个 Agent 都能自动导出对话记录；请严格遵循技能中的归档完整性规则。

## 安装

### 安装到兼容 Agent Skills 的工具

从包含该技能的目录执行你所用工具支持的安装流程。使用 `skills` CLI 时，可尝试：

```bash
npx skills add ./project-memory-ledger --skill project-memory-ledger
```

如果本机 CLI 版本的参数不同，请以其当前说明为准。也可以将整个 `project-memory-ledger/` 目录复制到对应 Agent 能识别的 Skills 目录。

### 初始化项目

先检查目标项目已有的指令、文档和记忆系统，再运行：

```bash
python /path/to/project-memory-ledger/scripts/init_memory.py --root /path/to/your-project
```

初始化器只创建缺失文件，不会覆盖现有 `AGENTS.md`、`memory.md` 或记忆记录。若确认适合将标准记忆说明追加到 `AGENTS.md`，先审查 `assets/templates/AGENTS-memory-block.md`，再执行：

```bash
python /path/to/project-memory-ledger/scripts/init_memory.py --root /path/to/your-project --patch-agents
```

工具不会自动提交或推送任何文件。将原始对话日志纳入 Git 前，请先评估其中可能包含的隐私和项目机密。

## 常用请求

- “初始化项目记忆协议。”
- “总结本次工作，把值得复用的发现存下来。”
- “找出我们关于缓存迁移的经验，并给出原始证据。”
- “审查候选记忆，只把经过验证、长期有用的内容晋升。”
- “检查记忆账本的格式、坏引用和过时晋升。”

## 刷新索引与校验

```bash
python /path/to/project-memory-ledger/scripts/rebuild_index.py --root /path/to/your-project
python /path/to/project-memory-ledger/scripts/validate_memory.py --root /path/to/your-project
```

脚本只使用 Python 标准库。索引脚本只替换 `memory/INDEX.md` 中由标记包围的区域；没有标记时会停止，而不是覆盖自定义索引。校验器检查 JSONL 语法、基础数据格式、事件顺序、重复 ID、当前视图中的 ID，以及本地对话引用。它不能证明一条经验在现实中一定正确，仍需人工/Agent 按证据复核。

## 核心设计

原始会话与账本事件只追加。`AGENTS.md`、`memory.md` 和 `memory/INDEX.md` 是当前状态视图，可以有控制地修订；每条晋升知识仍需保留稳定的 `MEM-*` ID 和证据引用。不要把当前摘要误认为完整的证据历史。

## 文件说明

- `SKILL.md`：技能入口与执行约定。
- `references/PROTOCOL.md`：目录、分层、生命周期与晋升门槛。
- `references/WORKFLOWS.md`：初始化、归档、检索、验证、晋升和审计流程。
- `references/GOVERNANCE.md`：证据、冲突、信任与隐私治理。
- `references/SCHEMAS.md` 和 `schemas/`：JSONL 数据约定。
- `scripts/`：非破坏性初始化、索引重建与校验脚本。
- `assets/templates/`：可复制到项目内的模板。
