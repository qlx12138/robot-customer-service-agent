# 智扫通 · 扫地机器人智能客服 Agent

基于 LangChain 构建的垂直领域客服 Agent。面向扫地机器人场景，提供知识问答、故障排查、选购建议，以及基于设备使用记录的个人报告生成；通过 RAG 检索本地知识库，并调用真实外部接口完成定位与天气查询。

项目定位为**功能验证型 Demo**：重点是把「对话入口 → Agent 编排 → 工具调用 → RAG 检索 → 结构化报告」这条链路完整跑通，而非追求生产级完备度。差距诊断与演进方向见 [`docs/enterprise-roadmap/`](docs/enterprise-roadmap/README.md)。

## 功能特性

| 能力 | 说明 |
|---|---|
| 流式对话界面 | Streamlit 单页聊天入口，逐字返回模型输出 |
| ReAct Agent 编排 | 基于 `langchain.agents.create_agent` 构建，注册 8 个业务工具，由模型自主决定调用顺序 |
| 中间件机制 | 统一记录工具调用入参与结果、记录模型调用前的消息规模、按运行上下文动态切换系统提示词 |
| RAG 知识问答 | 本地 txt / pdf → 文本分片 → 向量化 → Chroma 持久化 → Top-K 检索 → 提示词总结 |
| 增量入库 | 按文件 MD5 去重，已入库文件跳过，避免重复向量化与重复写入 |
| 月度使用报告 | 校验用户身份 → 列出可用月份 → 取数 → 切换报告提示词生成结构化报告 |
| 真实外部数据 | 客户端公网 IP 定位（ipwho.is）+ 实时天气（Open-Meteo），返回中标注数据来源与实际使用的 IP 口径 |

## 技术栈

| 层面 | 选型 |
|---|---|
| 语言 | Python 3.12 |
| 对话界面 | Streamlit |
| Agent 框架 | LangChain（`create_agent` + middleware）、LangGraph 运行时 |
| 大模型 | 阿里云百炼 `qwen-plus` |
| 向量模型 | 阿里云百炼 `text-embedding-v4` |
| 向量库 | Chroma（本地持久化） |
| 配置 | YAML（`config/*.yml`） |

## 目录结构

```
robot-customer-service-agent/
├── app.py                          # Streamlit 入口
├── requirements.txt
├── agent/
│   ├── react_agent.py              # Agent 组装与流式执行
│   └── tools/
│       ├── agent_tools.py          # 8 个业务工具
│       └── middleware.py           # 工具监控 / 模型日志 / 提示词动态切换
├── rag/
│   ├── vector_store.py             # 向量库构建与 MD5 增量入库
│   └── rag_service.py              # 检索 + 总结链路
├── model/
│   └── factory.py                  # 聊天模型与向量模型工厂
├── prompts/                        # 主提示词 / RAG 总结 / 报告提示词
├── config/                         # 3 份 YAML 配置 + 1 份模板（rag.yml 不入库，见下）
├── data/                           # 本地知识文件与模拟业务数据
├── utils/                          # 配置加载、路径、日志、文件读取
└── docs/enterprise-roadmap/        # 企业级演进设计文档（尚未实现）
```

## 快速开始

### 1. 环境准备

```bash
git clone <你的仓库地址>
cd robot-customer-service-agent

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置 API Key

`config/rag.yml` 含密钥，已在 `.gitignore` 中排除，仓库里只提供模板：

```bash
# Windows
copy config\rag.yml.example config\rag.yml
# macOS / Linux
cp config/rag.yml.example config/rag.yml
```

然后编辑 `config/rag.yml`，把 `DASHSCOPE_API_KEY` 换成你自己的阿里云百炼 Key（控制台「API-KEY 管理」创建）。

### 3. 构建知识库（首次运行必做）

```bash
python -m rag.vector_store
```

该脚本会读取 `data/` 下所有 txt / pdf，分片、向量化并写入本地 `chroma_db/`，同时把文件 MD5 记入 `md5.text`；再次运行时会自动跳过已入库文件。

### 4. 启动

```bash
streamlit run app.py
```

## 业务工具清单

| 工具 | 作用 |
|---|---|
| `search_product_knowledge` | 从知识库检索故障排查、维护保养、选购与使用建议 |
| `get_user_location` | 依据客户端公网 IP 定位到城市级经纬度 |
| `get_weather` | 获取指定城市实时天气（温度 / 湿度 / 降水 / 风速） |
| `get_current_month` | 返回 `Asia/Shanghai` 时区的当前月份 |
| `validate_user_id` | 校验用户 ID 是否存在于设备使用记录中 |
| `list_available_report_months` | 列出该用户可生成报告的月份 |
| `get_device_usage_record` | 查询指定用户指定月份的使用记录 |
| `start_report_generation` | 标记进入报告生成场景，触发提示词切换 |

## 设计要点

**配置与代码分离。** `utils/config_handler.py` 在模块导入时统一加载 YAML 配置，`utils/path_tool.py` 统一把相对路径解析为基于项目根目录的绝对路径，因此脚本在任意工作目录下都能正确定位资源文件。向量库的持久化目录同样以项目根为基准锚定，因此无论从哪个工作目录启动，读写到的都是同一个 chroma_db，不会因工作目录不同而散落出多个知识库。

**用中间件而不是散落的日志语句。** `agent/tools/middleware.py` 通过 `@wrap_tool_call` 统一捕获每个工具的调用与结果，`@before_model` 记录模型调用前的消息条数，`@dynamic_prompt` 在每次生成提示词前根据 `runtime.context` 判断当前是否处于报告场景，从而在同一套 Agent 上切换「普通问答」与「报告生成」两套系统提示词。业务代码中没有任何日志埋点。

**工具返回统一为 JSON 字符串。** 所有对外工具都返回 `json.dumps(..., ensure_ascii=False)` 的结果，模型解析更稳定，日志审计也更清晰；参数错误抛 `ValueError`，外部服务失败抛统一的 `ToolDataError`。

**外部依赖的降级与可追溯。** 定位与天气接口都设了 8 秒超时，异常统一转换为可读错误；定位结果中额外返回 `source`、`ip_scope`（区分「转发来的客户端 IP」与「服务出口 IP」）与精度说明，避免把近似结果当作精确信息使用。

**客户端 IP 的传递方式。** 前端从请求头取 `X-Forwarded-For` / `X-Real-Ip`，通过 `ContextVar` 传给定位工具，而不是把它塞进工具函数签名——避免框架生成的工具 schema 里多出一个模型不该填的参数。

**RAG 增量入库。** `rag/vector_store.py` 在写入前先比对文件 MD5，已处理的文件直接跳过，因此重复执行构建脚本不会产生重复向量。

## 数据说明

- `data/` 下的 txt / pdf 为扫地机器人知识资料，用于构建 RAG 知识库。
- `data/external/records.csv` 为**模拟**的设备使用记录，用于演示月度报告流程，非真实业务数据。
- 用户 ID 需要与 `records.csv` 中的记录匹配；不存在时 `validate_user_id` 会明确返回未找到，不会随机编造身份。

## 已知局限

本项目定位为 Demo，以下为已知且未处理的问题：

- 会话状态只存在于 Streamlit 的 session 中，刷新或换设备即丢失。
- 界面是单页聊天，没有登录、会话列表、停止生成、重试与反馈入口。
- 每轮请求只把当前提问交给模型，历史消息并未回传给 Agent，因此多轮上下文是有限的。
- 报告流程依赖提示词约束模型按顺序调用工具，缺少代码层的状态机、参数校验与幂等保障。
- 检索只有单一向量 Top-K，没有混合检索、重排、置信度门槛，也没有向用户展示引用来源。
- 用户与使用记录来自本地 CSV，未接入真实业务系统。
- 没有自动化测试、容器化、CI/CD 与结构化可观测性。

## 设计文档

[`docs/enterprise-roadmap/`](docs/enterprise-roadmap/README.md) 存放企业级演进的设计文档（**仅设计，未实现**）：

- **`企业级优化蓝图.md`** —— 与生产级产品的差距诊断、目标架构与目标目录结构、C01 ~ C10 待确认决策项，以及 WS-0 ~ WS-7 分工作区执行方案与 M1 ~ M3 验收门槛。
- **`智能服务Agent_WS1至WS4连续实施方案.md`** —— WS-1 ~ WS-4 的连续实施方案：统一工作区根目录、各工作区交付物与验收口径。

该文档不改变本 Demo 的现有行为；其描述的目标工程为独立新建项目，不在本仓库内落地。

## 安全说明

- 本仓库**不包含任何 API Key**。`config/rag.yml` 已被 `.gitignore` 排除，请从 `config/rag.yml.example` 复制后填写自己的 Key。
- `logs/`、`chroma_db/`、`output/`、`tmp/`、`md5.text` 等运行产物同样不入库。
