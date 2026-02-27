# 三层架构目录

## 目录映射

- 前端层（Presentation）: `frond-end/`
- 后端层（Backend）: `backend/`
- 基础设施层（Infrastructure）: `infrastructure/`
  - 数据库脚本: `infrastructure/database/schema.sql`
  - Redis 与部署可继续放在 `docker-compose.yml` 中管理

## 分层说明

数据库属于后端基础设施，不与前后端并列服务。当前工程已调整为：

1. 前端负责页面展示和交互（微信小程序）
2. 后端负责 API、业务逻辑、定时任务
3. 基础设施负责 PostgreSQL/Redis/容器编排与数据库脚本
