# 18 — 增强功能: 任务附件管理

**What to build:** 任务附件上传、查看、删除功能。

**Blocked by:** 02 — Prefactor: 创建任务管理基础模型

**Status:** ready-for-agent

- [ ] 后端：实现 Attachment API（POST /tasks/{id}/attachments, GET /tasks/{id}/attachments, DELETE /attachments/{id}）
- [ ] 后端：文件存储到本地目录（配置上传路径）
- [ ] 后端：权限控制（PM 上传任务附件，工程师查看）
- [ ] 前端：任务详情页附件上传区域
- [ ] 前端：附件列表展示（文件名、大小、上传者）
- [ ] 前端：附件预览（图片/PDF）
- [ ] 前端：附件删除功能
- [ ] 测试：API 集成测试