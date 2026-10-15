# 智能服务 Agent：WS-1 至 WS-4 连续实施方案

## 1. 方案适用范围

本方案使用以下目录作为所有工作区的统一根目录：

```text
D:\LLM_study\Stage3_Analysis_Agent
```

其中 `project/` 是只读原始 Demo，`smart-service-agent/` 是唯一允许修改的新项目。所有命令均在 `smart-service-agent/` 内执行。

系统目标是构建面向智能扫地机器人场景的服务 Agent，提供稳定的对话交互、结构化工具调用、知识检索、报告生成、质量评测和可观测能力。

后续所有工作区都打开 `Stage3_Analysis_Agent`，但只允许写入 `smart-service-agent`。原 Demo `project` 仅作为只读参考，不作为阶段启动文件依赖。

## 2. WS-0 实际基线

### 2.1 已存在并通过检查的内容

| 类别 | 实际产物 | 状态 |
|---|---|---|
| 项目元数据 | `pyproject.toml` | 已存在 |
| 安全配置模板 | `.env.example`、`.gitignore` | 已存在 |
| 项目说明 | `README.md` | 已存在 |
| 公共契约 | `core/contracts.py` | 已存在 |
| 契约测试 | `tests/test_contracts.py` | 4 项通过 |
| 架构决策 | `docs/decisions.md` | 已存在 |
| 阶段交接 | `docs/handoffs/WS-0.md` | 已存在 |
| 模块骨架 | `agent`、`tools`、`rag`、`core` | 已存在 |

### 2.2 WS-1 开始前需要处理的基线问题

这些事项直接纳入 WS1-1，不另设补充工作区：

1. `pyproject.toml` 的 description 需要改成系统用途描述。
2. `docs/handoffs/WS-0.md` 中“公共协议测试待处理”与实际状态不一致，需要校正。
3. 项目尚未初始化 Git；是否初始化由项目维护者决定，不阻塞 WS-1 功能开发。
4. 现有 `ToolResult` 和 `StreamEvent` 是最小契约，WS-1 可以兼容扩展，但不得无理由删除已有字段。

## 3. 阶段连续性规则

### 3.1 唯一阶段状态来源

每个工作区只依赖三类内容：

1. 项目中已经存在的代码和测试。
2. `docs/decisions.md` 中已接受的架构决策。
3. 上一阶段明确创建的 `docs/handoffs/WS-X.md`。

任何提示词引用的文件，都必须满足以下一种条件：

- 在 WS-0 实际基线中已经存在；
- 在上一工作区的“必须产出”中明确创建；
- 属于当前工作区将要创建的文件，提示词不得要求开始前读取它。

### 3.2 工作区结束条件

一个工作区只有同时满足以下条件才算完成：

- 必须产出的代码和文档全部存在；
- 本阶段测试通过；
- README 当前阶段已更新；
- `docs/handoffs/WS-X.md` 与实际状态一致；
- 下一阶段启动检查中的所有文件已经存在。

### 3.3 分步执行方式

每次只实施一个编号步骤，流程固定为：

```text
检查当前代码
→ 说明当前功能的问题与目标
→ 讲解实现原理
→ 给出当前步骤所需代码
→ 执行验证
→ 校正问题
→ 确认后进入下一步
```

不得一次性完成整个工作区，也不得提前创建下一阶段才需要的复杂实现。

## 4. WS-1：工程运行基线

### 4.1 阶段目标

建立稳定的配置、数据校验、异常处理、日志和最小运行入口，使后续 Agent、工具与 RAG 可以复用统一工程能力。

### 4.2 启动输入（均已存在）

- `README.md`
- `pyproject.toml`
- `.env.example`
- `.gitignore`
- `core/contracts.py`
- `tests/test_contracts.py`
- `docs/decisions.md`
- `docs/handoffs/WS-0.md`

### 4.3 实施步骤

#### WS1-1：校正项目基线

实现内容：

- 将项目元数据中的 description 改成系统用途描述。
- 根据实际测试结果更新 WS-0 交接记录。
- 补充 Ruff、Pytest 和类型检查所需的开发依赖与配置。
- 验证当前 4 个契约测试仍然通过。

原理重点：项目元数据、事实一致的交接文档、开发依赖与运行依赖的区别。

#### WS1-2：类型化配置

创建：

- `core/config.py`
- `tests/test_config.py`

实现内容：

- 从环境变量读取模型、Embedding、Chroma 和 Top-K 配置。
- 对缺失字段、整数范围和路径进行校验。
- 测试环境允许使用安全占位值，不调用真实服务。
- 错误信息只说明缺少哪个配置，不输出密钥值。

#### WS1-3：扩展公共契约

修改：

- `core/contracts.py`
- `tests/test_contracts.py`

实现内容：

- 在兼容现有测试的前提下，为 `ToolResult` 增加稳定错误码和元数据。
- 扩展流式事件类型，至少覆盖状态、工具开始、工具结束、文本片段、引用、错误和完成。
- 明确哪些字段必填，哪些字段可选。

#### WS1-4：统一异常

创建：

- `core/exceptions.py`
- `tests/test_exceptions.py`

实现内容：

- 定义配置、模型、工具、检索和输入错误。
- 区分用户可见消息与内部诊断信息。
- 建立异常转换为 `StreamEvent.ERROR` 的统一入口。

#### WS1-5：结构化日志

创建：

- `core/logging.py`
- `tests/test_logging.py`

实现内容：

- 日志包含 request ID、组件、状态和耗时。
- 对 API Key、Authorization 等敏感字段脱敏。
- 不记录完整提示词和完整检索上下文。

#### WS1-6：最小应用入口

创建：

- `app.py`
- `tests/test_app_smoke.py`

实现内容：

- 提供最小 Streamlit 页面或可测试的应用初始化函数。
- 页面只展示服务名称和当前配置状态，不实现 Agent。
- 缺少配置时显示可操作提示，不展示堆栈。

#### WS1-7：工程验证与说明

更新：

- `README.md`
- `docs/decisions.md`（仅在产生新决策时）

创建：

- `docs/handoffs/WS-1.md`

执行格式、静态检查、类型检查和全部测试，记录真实结果。

### 4.4 必须产出

```text
app.py
core/config.py
core/exceptions.py
core/logging.py
core/contracts.py
tests/test_config.py
tests/test_exceptions.py
tests/test_logging.py
tests/test_app_smoke.py
docs/handoffs/WS-1.md
```

### 4.5 WS-2 启动门禁

以下条件全部满足才能开始 WS-2：

- `docs/handoffs/WS-1.md` 存在且记录了验证结果；
- 配置、契约、异常、日志测试通过；
- `app.py` 可以启动最小页面；
- 测试不需要真实 API Key；
- 项目文档与元数据只描述系统用途。

### 4.6 WS-1 启动提示词

```text
你正在实施智能服务 Agent 的 WS-1：工程运行基线。

当前工作区根目录必须是：
D:\LLM_study\Stage3_Analysis_Agent

目录边界：
- project/：原始 Demo，只允许读取和分析。
- smart-service-agent/：唯一允许修改的目录。
- 所有测试、检查和启动命令必须在 smart-service-agent/ 中执行。
- 后文相对路径均指 smart-service-agent/ 下的文件。

开始前只读取并核验以下现有文件：
- docs/implementation-plan.md
- README.md
- pyproject.toml
- .env.example
- .gitignore
- core/contracts.py
- tests/test_contracts.py
- docs/decisions.md
- docs/handoffs/WS-0.md

执行规则：
1. 以当前文件真实状态为准。
2. 每次只开展 WS1-1 至 WS1-7 中的一个步骤；先说明原理和本步改动，再提供本步代码与验证方式。
3. 当前步骤通过验证并得到我的确认后，才能进入下一步。
4. 禁止修改、删除、移动、格式化或覆盖 project/ 中的任何文件。
5. 禁止提前实现 Agent、业务工具和 RAG。
6. 测试不得调用真实模型，任何文件和输出不得包含真实密钥。
7. 每步结束时说明已完成内容、验证结果和下一步所依赖的现有文件。

WS-1 步骤摘要（完整要求以 docs/implementation-plan.md 为准）：
- WS1-1：校正项目基线
- WS1-2：类型化配置
- WS1-3：扩展公共契约
- WS1-4：统一异常
- WS1-5：结构化日志
- WS1-6：最小应用入口
- WS1-7：验证与交接

如果 docs/implementation-plan.md 不存在，停止执行并报告缺失，不得根据步骤名称自行猜测实现范围。

先检查 WS1-1 是否已完成；如果未完成，只开展 WS1-1，然后停止等待确认。
```

## 5. WS-2：Agent、工具与报告工作流

### 5.1 阶段目标

实现可测试的模型适配、结构化工具、单轮与多轮 Agent，以及由代码控制的报告工作流。

### 5.2 启动输入（全部由 WS-1 产出或确认）

- `docs/handoffs/WS-1.md`
- `core/config.py`
- `core/contracts.py`
- `core/exceptions.py`
- `core/logging.py`
- `app.py`
- WS-1 全部测试

### 5.3 实施步骤

#### WS2-1：模型适配器与 Fake 模型

创建 `agent/model.py` 和对应测试。定义统一调用接口，使真实通义模型与 Fake 模型可替换。

#### WS2-2：第一项强类型工具

创建工具输入模型、输出模型和最小工具执行器；覆盖正常、参数错误和执行失败。

#### WS2-3：确定性业务工具集

实现用户、月份、天气和月度记录 Mock。相同输入必须得到相同结果，禁止随机用户和随机月份。

#### WS2-4：单轮 Agent

创建 `agent/react_agent.py`，支持工具选择、最大步数和标准流式事件。

#### WS2-5：多轮状态

创建会话状态模型，将受控历史传给 Agent；加入轮次或 Token 限制。

#### WS2-6：工具事件与异常降级

将工具开始、结束、错误和耗时转换成 WS-1 定义的事件协议。

#### WS2-7：意图路由

区分普通问答和报告请求，建立明确、可测试的路由结果。

#### WS2-8：报告状态与节点

创建 `agent/report_workflow.py`，先定义状态转移表，再实现用户、月份、取数、校验节点。

#### WS2-9：完整报告工作流

接入报告生成；数据缺失时停止生成，不编造字段。

#### WS2-10：集成与回归

更新最小页面用于验证多轮问答和报告流程；补齐端到端测试。

#### WS2-11：阶段交接

创建：

- `docs/agent-workflow.md`
- `docs/handoffs/WS-2.md`

### 5.4 必须产出

```text
agent/model.py
agent/react_agent.py
agent/report_workflow.py
tools/（业务工具实现）
data/mock/（确定性示例数据）
prompts/（Agent 与报告提示词）
docs/agent-workflow.md
docs/handoffs/WS-2.md
对应单元与集成测试
```

### 5.5 WS-3 启动门禁

- `docs/handoffs/WS-2.md` 和 `docs/agent-workflow.md` 存在；
- 多轮指代测试通过；
- 工具成功、参数错误、无数据和异常测试通过；
- 普通问答与报告工作流路由测试通过；
- Fake 模型可以离线跑通主要链路；
- RAG 仍通过接口占位，不要求 WS-2 提前优化检索。

### 5.6 WS-2 启动提示词

```text
你正在实施智能服务 Agent 的 WS-2：Agent、工具与报告工作流。

当前工作区根目录必须是 D:\LLM_study\Stage3_Analysis_Agent。project/ 只读，smart-service-agent/ 是唯一允许修改的目录；所有命令在 smart-service-agent/ 中执行，后文相对路径均相对于该目录。

开始前必须确认以下文件存在并读取：
- docs/implementation-plan.md
- docs/handoffs/WS-1.md
- core/config.py
- core/contracts.py
- core/exceptions.py
- core/logging.py
- app.py

然后运行 WS-1 交接文档记录的验证命令。如果文件缺失或验证失败，停止 WS-2，明确指出应返回 WS-1 修复的事项，不创建替代文件绕过门禁。

执行规则：
1. 每次只开展 WS2-1 至 WS2-11 中的一个步骤。
2. 先解释当前功能的数据流和设计原因，再给本步最小代码及测试。
3. 当前步骤通过验证并得到确认后才能继续。
4. 所有外部依赖必须可由 Fake 或确定性 Mock 替换。
5. 报告流程由显式工作流控制，不允许仅依赖提示词保证调用顺序。
6. 不实施混合检索、重排或完整 RAG 评测，这些属于 WS-3。
7. 禁止修改、删除、移动、格式化或覆盖 project/ 中的任何文件。

WS-2 步骤摘要（完整要求以 docs/implementation-plan.md 为准）：
- WS2-1：模型适配器与 Fake 模型
- WS2-2：第一项强类型工具
- WS2-3：确定性业务工具集
- WS2-4：单轮 Agent
- WS2-5：多轮状态
- WS2-6：工具事件与异常降级
- WS2-7：意图路由
- WS2-8：报告状态与节点
- WS2-9：完整报告工作流
- WS2-10：集成与回归
- WS2-11：阶段交接

如果实施计划或 WS-1 交接文件缺失，停止执行，不得自行猜测或创建替代计划。

先检查 WS2-1 是否已完成；如果未完成，只开展 WS2-1，然后停止等待确认。
```

## 6. WS-3：RAG、引用与质量评测

### 6.1 阶段目标

建立可追溯知识索引、引用输出、检索基线、混合检索、重排和可复现评测。

### 6.2 启动输入（全部由 WS-2 产出或确认）

- `docs/handoffs/WS-2.md`
- `docs/agent-workflow.md`
- `agent/react_agent.py`
- `core/contracts.py`
- `core/config.py`
- Agent 使用的 RAG 接口或占位工具
- WS-2 全部测试

### 6.3 实施步骤

1. **WS3-1 文档与元数据**：建立稳定 document ID、chunk ID 和来源字段。
2. **WS3-2 切分实验**：比较至少两种切分方式并保存样例结果。
3. **WS3-3 Chroma 索引**：实现可清理、可重建的新索引。
4. **WS3-4 向量检索基线**：保存 Top-K 基线结果和耗时。
5. **WS3-5 引用协议**：兼容扩展 `StreamEvent`，让答案能定位来源片段。
6. **WS3-6 评测数据 v1**：先建立 10 条样本并验证格式。
7. **WS3-7 检索指标**：实现 Hit@K、Recall@K 或 MRR，并用手算样本校验。
8. **WS3-8 扩展评测集**：扩展至 30–50 条，包含不可回答问题。
9. **WS3-9 BM25**：实现关键词检索并与向量检索对比。
10. **WS3-10 Hybrid/RRF**：实现排名融合并记录指标。
11. **WS3-11 重排**：加入轻量重排并记录质量与延迟变化。
12. **WS3-12 无答案策略**：建立低置信度拒答和对应指标。
13. **WS3-13 完整实验**：同一数据集对比 Baseline、Hybrid 和最终方案。
14. **WS3-14 阶段交接**：创建评测报告和交接文档。

### 6.4 必须产出

```text
rag/（文档、切分、索引、检索、融合、重排实现）
data/knowledge/（允许使用的知识文件）
evals/dataset.*
evals/run_retrieval_eval.py
evals/results/（可复现的机器可读结果）
docs/rag-evaluation.md
docs/handoffs/WS-3.md
对应测试
```

### 6.5 WS-4 启动门禁

- `docs/handoffs/WS-3.md` 和 `docs/rag-evaluation.md` 存在；
- 评测数据通过格式校验；
- 基线与最终结果来自同一评测集；
- 引用可以追溯到原文档和 chunk；
- 不可回答样本有单独结果；
- `docs/handoffs/WS-3.md` 明确给出 WS-4 可展示的真实指标文件路径。

### 6.6 WS-3 启动提示词

```text
你正在实施智能服务 Agent 的 WS-3：RAG、引用与质量评测。

当前工作区根目录必须是 D:\LLM_study\Stage3_Analysis_Agent。project/ 只读，smart-service-agent/ 是唯一允许修改的目录；所有命令在 smart-service-agent/ 中执行，后文相对路径均相对于该目录。

开始前必须确认并读取：
- docs/implementation-plan.md
- docs/handoffs/WS-2.md
- docs/agent-workflow.md
- agent/react_agent.py
- core/contracts.py
- core/config.py

先执行 WS-2 的验证命令。缺少输入或测试失败时，停止并返回 WS-2 修复，不得自行创建伪造交接文件。

执行规则：
1. 每次只开展 WS3-1 至 WS3-14 中的一个步骤。
2. 每项优化先建立假设和基线，再实现代码和记录真实结果。
3. 不复制原 Demo 的旧 Chroma 索引或 md5 文件，新项目独立构建索引。
4. 所有指标必须来自实际评测结果，不得预填或推测。
5. 引用协议扩展必须兼容 WS-1/WS-2 的公共契约和页面事件处理。
6. 不提前进行完整页面美化或发布部署。
7. 禁止修改、删除、移动、格式化或覆盖 project/ 中的任何文件。

WS-3 步骤摘要（完整要求以 docs/implementation-plan.md 为准）：
- WS3-1～WS3-5：文档元数据、切分、Chroma、向量基线、引用
- WS3-6～WS3-8：评测数据与检索指标
- WS3-9～WS3-12：BM25、Hybrid/RRF、重排、无答案策略
- WS3-13～WS3-14：完整实验与阶段交接

如果实施计划或 WS-2 交接文件缺失，停止执行，不得自行猜测或创建替代计划。

先检查 WS3-1 是否已完成；如果未完成，只开展 WS3-1，然后停止等待确认。
```

## 7. WS-4：交互体验、运行观测与交付文档

### 7.1 阶段目标

完善本地 Streamlit 使用体验，将 Agent、工作流、引用和运行指标以清晰、一致的方式呈现，并形成可复现的运行与维护说明。

### 7.2 启动输入（全部由 WS-3 产出或确认）

- `docs/handoffs/WS-3.md`
- `docs/rag-evaluation.md`
- `evals/results/` 中交接文档指定的结果
- 完整 Agent、报告工作流和 RAG 接口
- WS-3 全部测试

### 7.3 实施步骤

1. **WS4-1 页面与应用服务边界**：整理 `app.py`，页面不直接解析框架原始消息。
2. **WS4-2 完整流式聚合**：保证页面展示内容和保存内容一致。
3. **WS4-3 会话状态**：支持多轮历史和清空会话。
4. **WS4-4 工具进度**：展示工具开始、结束和错误摘要，不展示内部推理。
5. **WS4-5 引用展示**：展示来源、片段和可核验信息。
6. **WS4-6 运行摘要**：展示请求、检索、工具耗时和调用次数。
7. **WS4-7 反馈记录**：保存有帮助/无帮助反馈，不记录敏感内容。
8. **WS4-8 失败体验**：覆盖配置缺失、工具失败、无答案和报告无数据。
9. **WS4-9 README 与系统文档**：补充启动、架构、评测、排错和限制。
10. **WS4-10 全量验收**：执行检查、测试、评测和空环境启动演练。
11. **WS4-11 阶段交接**：创建最终交付清单和已知限制。

### 7.4 必须产出

```text
app.py（完整本地界面）
data/feedback/ 或约定的本地反馈文件
docs/system-architecture.md
docs/operation-guide.md
docs/demo-guide.md
docs/known-limitations.md
docs/handoffs/WS-4.md
页面与事件处理测试
```

### 7.5 完成门禁

- README 从空环境可以指导启动；
- 核心功能不依赖随机结果；
- 回答、引用和会话保存一致；
- 错误不向页面暴露内部堆栈；
- 文档中的指标都能定位到 `evals/results/`；
- 全部相关测试和评测完成，限制如实记录。

### 7.6 WS-4 启动提示词

```text
你正在实施智能服务 Agent 的 WS-4：交互体验、运行观测与交付文档。

当前工作区根目录必须是 D:\LLM_study\Stage3_Analysis_Agent。project/ 只读，smart-service-agent/ 是唯一允许修改的目录；所有命令在 smart-service-agent/ 中执行，后文相对路径均相对于该目录。

开始前必须确认并读取：
- docs/implementation-plan.md
- docs/handoffs/WS-3.md
- docs/rag-evaluation.md
- 交接文档指定的 evals/results 结果文件
- 当前 app.py
- 当前公共事件协议

先运行 WS-3 交接文档记录的验证命令。输入缺失、指标文件不存在或测试失败时，停止并返回 WS-3 修复，不得在文档或页面中伪造结果。

执行规则：
1. 每次只开展 WS4-1 至 WS4-11 中的一个步骤。
2. 先说明本步解决的用户问题和事件数据流，再给本步最小实现与测试。
3. 当前步骤验证并确认后才能继续。
4. 保持 Streamlit 本地运行，不实施 Docker 或公网部署。
5. 不展示内部思维过程，只展示状态、工具摘要和证据。
6. 所有展示指标必须来自 WS-3 的真实结果文件。
7. 禁止修改、删除、移动、格式化或覆盖 project/ 中的任何文件。

WS-4 步骤摘要（完整要求以 docs/implementation-plan.md 为准）：
- WS4-1～WS4-3：页面边界、流式聚合、会话状态
- WS4-4～WS4-6：工具进度、引用、运行摘要
- WS4-7～WS4-8：反馈记录与失败体验
- WS4-9～WS4-11：系统文档、全量验收与阶段交接

如果实施计划、WS-3 交接文档或指标文件缺失，停止执行，不得自行猜测或伪造结果。

先检查 WS4-1 是否已完成；如果未完成，只开展 WS4-1，然后停止等待确认。
```

## 8. 阶段产物依赖总表

| 下阶段 | 启动前必须存在 | 由哪个阶段创建 |
|---|---|---|
| WS-1 | `core/contracts.py`、`tests/test_contracts.py`、`docs/handoffs/WS-0.md` | WS-0，当前已存在 |
| WS-2 | `core/config.py`、`core/exceptions.py`、`core/logging.py`、`docs/handoffs/WS-1.md` | WS-1 |
| WS-3 | `agent/react_agent.py`、`docs/agent-workflow.md`、`docs/handoffs/WS-2.md` | WS-2 |
| WS-4 | `docs/rag-evaluation.md`、真实评测结果、`docs/handoffs/WS-3.md` | WS-3 |
| 完成 | 系统、运行、演示、限制和 `docs/handoffs/WS-4.md` | WS-4 |

如果表中任一文件不存在，下一阶段必须停止，返回上一阶段完成产物，不允许通过创建空文件绕过。

## 9. 交接文档统一模板

```markdown
# WS-X 阶段交接

## 阶段目标

## 实际完成内容

## 必须产出检查
| 文件/能力 | 是否存在 | 验证方式 | 结果 |
|---|---|---|---|

## 公共契约变化
- 新增：
- 兼容性：
- 下阶段禁止破坏的内容：

## 验证结果
| 检查 | 命令 | 真实结果 |
|---|---|---|

## 未完成事项

## 下一阶段启动输入
| 文件/接口 | 用途 |
|---|---|

## 下一阶段启动门禁
- [ ] 所有输入文件存在
- [ ] 所有验证通过
- [ ] 文档与代码状态一致
```
