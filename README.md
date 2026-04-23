# LinkNote

LinkNote 是一个本地优先的内容整理与笔记自动化项目。它可以从微信文件传输助手、剪贴板或手动输入中收集 Bilibili 链接，并生成日报与单条视频笔记工作台。

当前项目面向小团队协作开发，技术栈包括：

- FastAPI 后端
- React + Vite 前端
- 本地工作区持久化
- Windows 启动脚本
- OpenAI Compatible 模型接入
- Bilibili 字幕 / 音频 / 视频处理

## 功能概览

- 从以下来源采集 Bilibili 链接：
  - 微信文件传输助手
  - 剪贴板
  - 手动输入
- 生成当日日报页
- 为单条视频生成结构化笔记
- 支持失败后重试与多版本笔记
- 展示原文转录与引用片段
- 根据 Markdown 生成 Markmap 思维导图
- 支持围绕当前笔记继续 AI 问答
- 支持本地定时整理任务

## 运行要求

- Windows 10/11
- Python 3.12+
- Node.js 20+
- npm
- 建议安装 `ffmpeg`
- 至少配置一个可用的模型提供商 API Key

公开视频在平台自带字幕可用时，可能不需要 cookies；受限视频通常需要 `cookies.txt` 或浏览器 cookies fallback。

## 快速开始

克隆仓库后运行：

```powershell
cd linknote
.\scripts\bootstrap.cmd
.\scripts\start-app.cmd
```

打包模式启动后，访问：

```text
http://127.0.0.1:8765/
```

如果需要前端热更新开发模式，运行：

```powershell
cd linknote
.\scripts\start-dev.cmd
```

开发前端地址：

```text
http://127.0.0.1:3015/
```

## 首次配置

进入应用的 `设置` 页面后，至少确认这些内容：

- 微信 `chatlog` 根目录
- 分析用模型提供商与模型
- API Key 或 API Key 对应的环境变量
- 可选的 Bilibili `cookies.txt` 路径
- 可选的音频转写方式与模型

运行时配置默认保存在：

```text
workspace/runtime/linknote.json
```

这个文件不会进入 Git，因为其中可能包含本机路径、密钥和个人运行配置。

## 仓库结构

```text
linknote/
  backend/                 FastAPI 后端
  frontend/                React + Vite 前端
  scripts/                 Windows 启动与构建脚本
  docs/                    架构与协作文档
  workspace/               本地运行数据目录，已被 Git 忽略
  linknote.example.json    示例配置文件
```

## 后端结构

```text
backend/app/
  analysis/        分析提示词与模型调用流程
  config/          配置结构、默认值与路径处理
  downloaders/     Bilibili 字幕 / 音频 / 视频获取
  ingest/          微信、剪贴板等输入采集
  models/          媒体、笔记、日报等数据结构
  routers/         FastAPI 路由接口
  services/        业务编排与持久化
  transcription/   音频转写适配层
```

## 前端结构

```text
frontend/src/
  api.ts           后端 API 调用与返回值标准化
  app/             应用壳层与跨页面共享组件
  layouts/         页面布局组件
  pages/           路由级页面与页面局部组件
  types.ts         前端共享类型
```

## 协作文档

- `CONTRIBUTING.md`：分支、PR、评审协作约定
- `docs/CODE_GUIDE.md`：命名、注释与模块边界约定
- `docs/ARCHITECTURE.md`：系统架构概览
- `docs/LINKNOTE_MIGRATION_PLAN.md`：早期迁移背景与范围决策
- `docs/LINKNOTE_PROJECT_BOOK.md`：更完整的项目说明与实现分析

## 常用命令

安装依赖并构建前端：

```powershell
.\scripts\bootstrap.cmd
```

启动打包模式本地应用：

```powershell
.\scripts\start-app.cmd
```

启动前后端开发模式：

```powershell
.\scripts\start-dev.cmd
```

仅启动后端：

```powershell
cd backend
python -m app.run_local
```

仅启动前端：

```powershell
cd frontend
npm install
npm run dev
```

构建前端：

```powershell
cd frontend
npm run build
```

## 运行数据约定

以下内容不要提交到仓库：

- `workspace/`
- `linknote.json`
- `cookies.txt`
- API Key
- 微信数据库或聊天导出数据
- 下载的音频 / 视频
- 生成后的笔记结果
- 本地浏览器测试目录

如需共享配置示例，请使用：

- `linknote.example.json`
- `backend/.env.example`

## 常见问题

- `前端依赖缺失`：运行 `.\scripts\bootstrap.cmd`
- `后端依赖缺失`：运行 `cd backend; python -m pip install -e .`
- `没有可用模型提供商`：先在设置页启用一个 provider
- `API Key 缺失`：在设置中填写，或配置对应环境变量
- `Bilibili cookies required`：设置 `cookies.txt` 或启用浏览器 cookies fallback
- `微信数据目录不可用`：在设置中修正 `chatlog` 路径
- `长视频长时间分析中`：本地音频转写可能比较耗 CPU，界面会显示当前阶段

## 许可证

MIT
