# SmartOffice — 智行舟智能办公系统

[![Django](https://img.shields.io/badge/Django-4.x-092E20?logo=django)](https://www.djangoproject.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?logo=vue.js)](https://vuejs.org/)
[![LangChain](https://img.shields.io/badge/LangChain-AI-FF6B35)](https://langchain.com/)
[![GraphRAG](https://img.shields.io/badge/GraphRAG-知识图谱-0078D4)](https://github.com/microsoft/graphrag)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

> 2025 软件杯竞赛参赛作品

## 项目背景

传统办公系统功能单一，往往只能处理流程审批、文件管理等基础事务。随着大语言模型的发展，员工在工作中产生了大量"问一问 AI"的需求——比如查阅公司文档、生成会议纪要、分析图表数据——但这些操作通常需要切换到外部工具，流程割裂，效率不高。

本项目将 AI 能力直接集成到办公系统中，基于 Django 后端 + Vue.js 前端，结合 LangChain 框架和 GraphRAG 知识图谱技术，实现了：

- 基于企业文档的智能问答（RAG 检索增强）
- 图片理解与分析（视觉 AI）
- 日常办公流程管理

用户无需切换工具，在同一个系统内就能完成办公事务处理和 AI 辅助。

## 效果展示

### 系统仪表盘
![系统仪表盘](docs/dashboard.png)

展示任务概览、项目进度、AI 调用统计等关键指标，右侧 AI 助手支持实时对话问答。

### AI 智能对话
![AI 智能对话](docs/ai-chat.png)

基于企业文档的智能问答，支持多轮对话、会议纪要整理、文档检索等场景。

### 文档管理
![文档管理](docs/doc-manage.png)

集中管理企业文档，支持上传、分类、搜索和共享，文件自动纳入 AI 知识库。

### 登录界面
![登录界面](docs/login.png)

## 核心功能

| 功能 | 说明 |
|------|------|
| AI 智能问答 | 接入大语言模型，支持多轮对话，结合知识库检索增强 |
| 文档知识检索 | 基于 GraphRAG 构建文档知识图谱，语义级精准问答 |
| 图片分析 | 集成视觉 AI 模型，支持图片内容理解和数据提取 |
| 仪表盘 | 可视化数据面板，展示关键业务指标 |
| 用户管理 | 独立的用户认证和权限管理体系 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue.js + Element Plus UI |
| 后端 | Django + Django REST Framework |
| AI 框架 | LangChain + GraphRAG |
| 大模型 | 兼容 OpenAI API 的模型 |
| 数据库 | MySQL / SQLite |
| 部署 | Nginx 反向代理 |

## 项目结构

```
SmartOffice/
├── backend/                    # Django 后端
│   ├── apps/                   # 业务模块
│   ├── ai/                     # AI 功能（LangChain 集成）
│   ├── graphrag-main/          # GraphRAG 知识图谱
│   ├── setting.yaml            # 应用配置
│   ├── manage.py
│   └── requirements.txt
├── frontend/                   # Vue.js 前端
│   ├── src/
│   │   ├── api/                # 接口封装
│   │   ├── components/         # 组件
│   │   ├── views/              # 页面
│   │   └── router/             # 路由
│   └── package.json
└── README.md
```

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
# 修改 setting.yaml（数据库、AI API 密钥等）
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 配置说明

编辑 `backend/setting.yaml`：
- **django：** secret_key、debug 模式、allowed_hosts
- **database：** 数据库连接信息
- **ai：** 大模型 API Key、地址、模型名称
- **logging：** 日志级别和路径

## 开源协议

MIT License
