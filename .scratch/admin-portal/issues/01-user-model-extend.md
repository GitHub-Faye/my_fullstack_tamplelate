# 01 — 后端：User 模型扩展 + 管理员删除用户 API

**What to build:** 管理员账号管理页面需要展示手机号、部门、入职日期、在岗状态等字段，当前 User 模型缺少这些字段。同时管理员需要能删除用户账号，当前缺少管理员删除接口。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] User 模型新增 `phone`、`department`、`hire_date`、`employment_status` 字段
- [ ] 数据库迁移（新增列）
- [ ] UserAdminCreate/UserAdminUpdate 补充对应字段
- [ ] UserAdminDetail 响应返回新字段
- [ ] 新增 `DELETE /v1/admin/users/{user_id}` 管理员删除用户 API
- [ ] 后端测试通过