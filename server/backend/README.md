# SLKY 本地后端

该目录是 `SLKY_wx` 自带的 FastAPI 后端，提供基地列表、关键词和省份筛选、基地详情、首页推荐、地图、智能咨询、收藏、预约和浏览记录接口。

数据使用同目录的 `forest_wellness_local.db`（SQLite），上传资源位于 `uploads/`。

## 启动

在项目根目录运行 `npm run dev`，会同时启动本后端（`http://127.0.0.1:8001`）和前端。首次启动会自动创建后端虚拟环境并安装依赖。

仅启动后端可运行 `npm run backend`。

接口文档：`http://127.0.0.1:8001/docs`。
