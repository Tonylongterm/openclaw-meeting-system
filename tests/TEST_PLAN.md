# 自动化测试计划

## 目标
覆盖三类高风险逻辑，阻断首页跳转错误、登录态串页、未授权访问会议资源等低级回归。

## 覆盖范围
1. 路由入口
   - `GET /` 首页按钮路由正确。
   - “登录”必须跳转到 `/app?auth=login`。
   - “开始使用/立即开始”必须跳转到 `/app?auth=register`。
2. 前端状态切换
   - `/app?auth=login` 默认展示登录态。
   - `/app?auth=register` 默认展示注册态。
   - 未登录时仅显示 `auth-shell`，已登录后才显示 `app-shell`。
   - 创建会议 Modal 必须位于已登录视图容器内，且带鉴权标记。
3. API 鉴权
   - `/api/auth/me`、`/api/meetings`、`/api/meetings/<id>`、`/api/meetings/<id>/start` 未带 token 时返回 `401`。
   - SSE `/api/meetings/<id>/stream` 未带 token 时返回 `401`。
   - 非会议 owner 访问会议详情或 SSE 时返回 `403`。
4. 会议状态切换
   - 注册、登录、创建会议、列出会议、查看详情链路正常。
   - 未设置主持人时启动会议返回 `400`。
   - Agent 加入并设置主持人后，启动会议返回 `200`，会议进入运行态。

## 执行方式
- 脚本：`python3 tests/qa_check.py`
- 运行环境：本地 Flask `test_client`，直接导入 `server.py`，不依赖外部网络。

## 放行标准
- 所有断言通过。
- 脚本最终输出 `QA checks passed.`。
