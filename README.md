# DMS-skills

个人维护的 Agent Skills 仓库。每个子目录是一个独立技能，采用开放的 Agent Skills 目录格式（`SKILL.md` + 可选的 references、scripts、assets、schemas 等），可被支持该格式的 AI 工具直接加载。

## 技能一览

| 技能 | 作用 | 触发场景 |
|---|---|---|
| [obsidian-note-format](obsidian-note-format/SKILL.md) | Obsidian 笔记的格式规范：Front Matter 字段与顺序、id 生成、标签体系、Markdown 语法与内容规范 | 新增/修改/整理 Obsidian 笔记，或检查某篇笔记是否合规 |
| [obsidian-vault-organization](obsidian-vault-organization/SKILL.md) | 笔记仓库的文件组织：顶层结构、编号规则、各文件夹归属 | 决定笔记放哪里、新建或调整文件夹、按编号指代文件夹 |
| [obsidian-workspace-init](obsidian-workspace-init/SKILL.md) | `99_AI` 下 AI 工作区的初始化：目录模板、AGENTS.md 模板、映射记录格式 | 新建工作区、初始化结构、编写工作区说明、管理 `notes/` 与 `skills/` 映射 |
| [project-memory-ledger](project-memory-ledger/SKILL.md) | 以普通文件实现跨 Agent 的项目记忆：JSONL 会话归档 + 追加式账本 + 分层晋升（`AGENTS.md` / `memory.md` / `memory/`） | 保存会话经验、检索旧决策、审核记忆冲突、晋升长期知识 |

前三个技能构成一套相互引用的 Obsidian 笔记体系，配合使用；`project-memory-ledger` 与之无关，是可移植到任意项目的独立技能，自带 Python 脚本与模板。

## 目录结构

```text
DMS-skills/
├── obsidian-note-format/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── obsidian-vault-organization/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── obsidian-workspace-init/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/onboarding.md     参数清单驱动的引导流程
└── project-memory-ledger/
    ├── SKILL.md
    ├── README.md
    ├── references/                  协议、工作流、治理、数据格式
    ├── schemas/                     JSONL 数据 Schema
    ├── scripts/                     初始化、索引重建、校验脚本（仅标准库）
    └── assets/templates/            可复制到项目内的模板
```

## 使用方式

把需要的技能目录整个复制到所用 Agent 能识别的 skills 目录即可。若使用 `skills` CLI：

```bash
npx skills add ./obsidian-note-format
```

技能之间以名称互相引用（如格式规范声明「Obsidian 语法遵循 obsidian-markdown 技能」），只装单个技能时，被引用的外部技能不可用属于预期情况。

## 技能文件约定

- `SKILL.md` 为入口，Front Matter 至少包含 `name` 与 `description`；`description` 决定技能何时被自动调用，需写清触发场景。
- 详细内容放 `references/`，脚本放 `scripts/`，模板与静态资源放 `assets/`，数据结构放 `schemas/`，避免 `SKILL.md` 过长。
- `agents/openai.yaml` 提供展示名、简短描述与是否允许隐式调用（`allow_implicit_invocation`）。
- 修改技能时保持 `SKILL.md` 内的交叉引用有效——本仓库多个技能以名称相互指向。
