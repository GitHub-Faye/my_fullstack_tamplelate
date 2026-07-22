# 02 — 后端：角色 CRUD API

**What to build:** 管理员角色管理页面需要查看角色列表、新增角色、修改角色权限、删除角色。当前后端只有角色模型和用户角色关联，没有公开的角色管理 API。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] 角色 Schema：RoleCreate、RoleUpdate、RolePublic（含 id、name、权限字符、scopes 列表、状态、创建时间）
- [ ] 角色 CRUD 路由：`GET/POST /v1/admin/roles`、`GET/PUT/DELETE /v1/admin/roles/{role_id}`
- [ ] 创建角色时关联 scopes，更新时替换 scopes
- [ ] 操作审计日志
- [ ] 后端测试通过