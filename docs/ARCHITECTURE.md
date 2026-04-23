# LinkNote 架构说明

## 产品形态

- 输入来源：
  - 微信文件传输助手链接采集
  - 剪贴板链接采集
  - 手动粘贴 Bilibili 链接
- 主要导航：
  - 日报页
  - 单条笔记详情页
- 通知方式：
  - Windows 通知可直接打开当前日报页

## 后端边界

### `config`

负责运行时配置、默认值、路径展开与工作区目录创建。

### `ingest`

只负责原始输入采集。

- `clipboard.py`：读取当前剪贴板文本
- `wechat.py`：复制微信数据库快照并提取候选链接文本
- `wechat_refresh.py`：在需要时刷新微信导出数据
- `store.py`：把采集到的原始文本写入按日期分组的 inbox 文件

### `downloaders`

- `bilibili.py`：负责 Bilibili 媒体获取、字幕获取、BV 规范化、cookies 兜底

### `analysis`

- 提示词构造
- OpenAI Compatible 生成
- 基于 transcript 的笔记生成
- 由 Markdown 派生思维导图

### `notes`

- 笔记记录持久化
- 日报组装
- 重分析版本堆叠
- 保留策略清理

### `daily`

- 定时任务
- 手动运行
- Windows 完成通知
- 启动诊断与健康检查

## 前端边界

- `app`：应用壳层、路由、布局
- 当前应用壳层包含：
  - 日报页
  - 笔记工作台
  - 设置页
  - 健康检查与引导信息

UI 设计应保持 LinkNote 自己的产品语言：以日报为主入口、以单条工作台为核心处理界面，并保留本地应用风格，足够简单、清晰、可维护。
