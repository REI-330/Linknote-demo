# LinkNote 代码规范

这份文档定义仓库里默认采用的命名、注释和模块边界规则，方便多人协作时保持代码风格一致。

## 命名

## Python

- 对外暴露的函数尽量使用完整单词，不要过度缩写
- 动作型函数优先使用动词开头，例如：
  - `load_app_config`
  - `run_note_analysis`
  - `collect_health_bootstrap`
- 纯数据辅助函数优先使用名词语义，例如：
  - `note_record_path`
  - `config_path`
  - `report_to_dict`

## TypeScript / React

- 路由级页面统一使用 `Page` 后缀
- 大型 UI 容器优先使用 `Panel`、`Viewer` 或 `Layout`
- 组件属性类型统一使用 `Props` 后缀
- API 标准化辅助逻辑尽量紧贴 `api.ts`

## 注释

注释应优先解释以下三类信息：

- 为什么存在某个兜底逻辑
- 为什么要划出某个模块边界
- 为什么某个不明显的实现选择是刻意为之

适合写注释的例子：

- 说明为什么启动脚本要清理旧的本地进程
- 说明为什么真实配置文件不能进 Git
- 说明为什么分析任务要把进度写进 `note.json`

不建议写只是在重复代码字面意思的注释。

## 模块边界

- `backend/app/config`：配置加载、规范化、持久化
- `backend/app/services`：业务编排与应用级逻辑
- `backend/app/downloaders`：来源相关抓取逻辑
- `backend/app/routers`：HTTP 接口契约
- `frontend/src/app`：应用壳层与跨页面状态编排
- `frontend/src/pages`：路由级页面与页面局部大型组件
- `frontend/src/api.ts`：前端 API 调用与返回结构标准化

## 建议评审清单

- 文件名是否和模块真实职责一致
- 对外暴露的命名是否足够明确、方便搜索
- 这次改动是否把本机路径、密钥或运行数据带进仓库
- 如果存在兜底逻辑，代码或文档里是否解释了原因
- 如果前后端都改了，接口结构是否仍然清晰易懂
