## 📋 apps/web Blog 前端页面开发计划（已确认）

### 架构决策 ✅

| 决策点 | 结论 |
|--------|------|
| 博客路由组 | `app/(blog)/` 独立公开路由组 |
| 首页跳转 | 保持现有逻辑不变（登录→dashboard，未登录→login），博客独立 `/blog` 访问 |
| 视觉样式 | 复用现有 shadcn/ui 体系 + Tailwind CSS |

---

### 📁 完整目录结构（28 个新建文件）

```
apps/web/
├── features/blog/                          ← 新建 Blog feature (17 文件)
│   ├── index.ts                            # barrel export
│   ├── schemas/
│   │   ├── index.ts
│   │   └── post.ts                         # Zod: PostCreate/Update, CommentCreate
│   ├── api/
│   │   ├── index.ts
│   │   ├── client/
│   │   │   ├── index.ts
│   │   │   └── queries.ts                  # 15 React Query hooks
│   │   └── server/
│   │       ├── index.ts
│   │       └── queries.ts                  # 5 server-side fetch
│   ├── client/
│   │   ├── index.ts
│   │   ├── BlogLayout.tsx                  # 公开博客布局
│   │   ├── Sidebar.tsx                     # 最近评论 + 分类
│   │   ├── PostCard.tsx                    # 文章卡片
│   │   ├── PostList.tsx                    # 分页文章列表
│   │   ├── PostDetail.tsx                  # 文章详情 + 评论区
│   │   ├── PostEditor.tsx                  # 新建/编辑复用
│   │   ├── CommentList.tsx                 # 评论列表
│   │   └── CommentForm.tsx                 # 评论提交
│   └── server/
│       └── index.ts
│
├── app/(blog)/                             ← 新建公开博客路由组 (5 文件)
│   ├── layout.tsx                          # BlogLayout wrap
│   ├── page.tsx                            # 首页（特色 + 最新列表）
│   ├── archives/page.tsx                   # 归档页
│   ├── category/[slug]/page.tsx            # 分类筛选页
│   └── posts/[slug]/page.tsx               # 文章详情页
│
└── app/(dashboard)/dashboard/blog/         ← 新建后台管理路由 (3 文件)
    ├── page.tsx                            # 后台文章列表
    ├── new/page.tsx                        # 新建文章
    └── [id]/edit/page.tsx                  # 编辑文章
```

---

### 🔗 页面 ↔ SDK 函数映射

| 页面 | SDK 函数 | Hook 名称 |
|------|---------|----------|
| `(blog)/page.tsx` | `listPostsV1BlogPostsGet` + `listCategoriesV1BlogCategoriesGet` | `usePosts()` / `useCategories()` |
| `archives/page.tsx` | `getArchivesV1BlogPostsArchivesGet` | `useArchives()` |
| `category/[slug]/page.tsx` | `listCategoryPostsV1BlogCategoriesSlugPostsGet` | `useCategoryPosts(slug)` |
| `posts/[slug]/page.tsx` | `getPostDetailV1BlogPostsSlugGet` + `listCommentsV1BlogPostsSlugCommentsGet` | `usePostDetail(slug)` / `useComments(slug)` |
| `dashboard/blog/page.tsx` | `adminListPostsV1BlogPostsAdminListGet` | `useAdminPosts()` |
| `dashboard/blog/new/page.tsx` | `createCategoryV1BlogCategoriesPost` / `createPostV1BlogPostsPost` | `useCreateCategory()` / `useCreatePost()` |
| `dashboard/blog/[id]/edit/page.tsx` | `getPostDetailV1BlogPostsSlugGet` + `updatePostV1BlogPostsPostIdPatch` + `deletePostV1BlogPostsPostIdDelete` | `usePostDetail()` / `useUpdatePost()` / `useDeletePost()` |
| `Sidebar` | `getRecentCommentsV1BlogCommentsRecentGet` + `listCategoriesV1BlogCategoriesGet` | `useRecentComments()` / `useCategories()` |
| `CommentForm` | `createCommentV1BlogPostsSlugCommentsPost` / `deleteCommentV1BlogCommentsCommentIdDelete` | `useCreateComment()` / `useDeleteComment()` |

---

### 📐 数据流架构

```
┌──────────────────────────────────────────────────────────┐
│                    apps/web                              │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────┐ │
│  │  (blog)     │   │  (dashboard) │   │  features/    │ │
│  │  公开路由    │──▶│  后台路由     │──▶│  blog/client  │ │
│  │  page.tsx   │   │  page.tsx    │   │  PostCard.tsx │ │
│  └──────┬──────┘   └──────┬───────┘   └───────┬───────┘ │
│         │                 │                   │         │
│         ▼                 ▼                   ▼         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  features/blog/api/client/queries.ts              │   │
│  │  usePosts() / usePostDetail() / useCreatePost()  │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  @repo/sdk  (packages/sdk)                       │   │
│  │  listPostsV1BlogPostsGet() / ...                 │   │
│  │  PostPublic / PostDetailPublic / ...             │   │
│  └──────────────────────┬───────────────────────────┘   │
└─────────────────────────┼───────────────────────────────┘
                          │ HTTP
                          ▼
┌──────────────────────────────────────────────────────────┐
│  apps/api  → /v1/blog/posts, /v1/blog/categories, ...   │
└──────────────────────────────────────────────────────────┘
```

---

### ⚡ 执行步骤（10 步，按依赖顺序）

| # | 步骤 | 文件数 | 说明 |
|---|------|--------|------|
| 1 | `schemas/post.ts` + `schemas/index.ts` | 2 | Zod 校验 schema |
| 2 | `api/client/queries.ts` + `api/client/index.ts` | 2 | 全部 React Query hooks |
| 3 | `api/server/queries.ts` + `api/server/index.ts` | 2 | Server-side fetch |
| 4 | `client/*.tsx` (8 组件) + `client/index.ts` | 9 | 所有客户端组件 |
| 5 | `server/index.ts` | 1 | 服务端组件导出 |
| 6 | `features/blog/index.ts` + `api/index.ts` | 2 | Barrel exports |
| 7 | `app/(blog)/` 下 5 个路由文件 | 5 | 公开页面 |
| 8 | `app/(dashboard)/dashboard/blog/` 下 3 个路由文件 | 3 | 后台页面 |
| 9 | 修改 `components/navbar.tsx` | 1 | 导航栏新增 Blog 入口 |
| 10 | 修改 `components/providers.tsx`（如需要） | 1 | 确保 SDK client 对公开路由也可用 |

**总计：约 28 个新建文件 + 2 个修改文件**

---

> 💡 **可随时切换到 Code 模式执行上述步骤。** 是否现在开始？