  ---                                                                                           
  Blog 域开发计划 
                                                                                                
  一、前端业务映射（来自 ruanyifeng-clone-quest 9 个路由 + lib/posts.ts 数据模型）
  ┌───────────────────────────┬─────────────────────────┬───────────────────────────┐
  │         前端页面          │        业务能力         │         后端模块          │
  ├───────────────────────────┼─────────────────────────┼───────────────────────────┤
  │ index.tsx 首页            │ 首屏特色 + 最新文章列表 │ posts（list）             │
  ├───────────────────────────┼─────────────────────────┼───────────────────────────┤
  │ archives.tsx 归档         │ 按年月聚合所有文章      │ posts（archives 视图）    │
  ├───────────────────────────┼─────────────────────────┼───────────────────────────┤
  │ category.$name.tsx 分类   │ 按分类筛选              │ categories + posts        │
  ├───────────────────────────┼─────────────────────────┼───────────────────────────┤
  │ posts.$slug.tsx 文章详情  │ 文章正文 + 评论         │ posts（detail）+ comments │
  ├───────────────────────────┼─────────────────────────┼───────────────────────────┤
  │ admin.index.tsx 后台列表  │ 文章管理列表            │ posts（admin list）       │
  ├───────────────────────────┼─────────────────────────┼───────────────────────────┤
  │ admin.new.tsx 新建        │ 写作                    │ posts（create）           │
  ├───────────────────────────┼─────────────────────────┼───────────────────────────┤
  │ admin.edit.$slug.tsx 编辑 │ 修改/删除               │ posts（update/delete）    │
  ├───────────────────────────┼─────────────────────────┼───────────────────────────┤
  │ login.tsx / admin.tsx     │ 鉴权                    │ ✅ user 域已完成          │
  └───────────────────────────┴─────────────────────────┴───────────────────────────┘
  侧栏 Sidebar 还会用到「最近评论」聚合，归到 comments 模块。

  二、与现有项目结构的一致性约束

  按 domains/user 的模板，blog 采用子路由目录形式（业务比 item 复杂）：

  app/domains/blog/
  ├── __init__.py
  ├── schemas.py              # Post/Category/Comment 全部 DTO
  ├── repository.py           # 所有 CRUD（模块级 async 函数）
  ├── exceptions.py           # 留空或自定义业务异常
  └── router/
      ├── __init__.py         # 导出 posts_router / categories_router / comments_router
      ├── posts.py            # 文章 CRUD + 归档 + 分类筛选
      ├── categories.py       # 分类 CRUD
      └── comments.py         # 评论 CRUD

  必须遵循的既有约定（与 user 域一致）：
  - ORM：SQLModel + async SQLAlchemy；表模型集中放 app/core/models.py
  - 主键：uuid.UUID；时间戳用 get_datetime_utc()
  - Repository：模块级 async def，关键字参数（*, session, ...），分页返回 Tuple[list[T], int]
  - DTO：XxxBase / XxxCreate / XxxUpdate / XxxPublic / XxxsPublic(PaginatedResponse[XxxPublic])
  - 异常：用 BusinessException + ErrorCode 枚举，新增 raise_blog_*_not_found() 辅助函数
  - 鉴权：复用 CurrentUser / SessionDep / get_current_active_superuser
  - 权限：在 app/core/scopes.py 新增 BlogScope，写入 DEFAULT_ROLE_SCOPES
  - 路由注册：在 app/api/v1/api.py 加入 /blog/posts、/blog/categories、/blog/comments
  - 迁移：用 Alembic 生成 revision

  三、数据模型（添加到 app/core/models.py）

  class BlogCategory(SQLModel, table=True):
      id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
      name: str = Field(unique=True, index=True, max_length=50)   # 周刊/随笔/档案
      slug: str = Field(unique=True, index=True, max_length=50)
      created_at: datetime | None = Field(default_factory=get_datetime_utc, ...)
      posts: List["BlogPost"] = Relationship(back_populates="category")

  class BlogPost(SQLModel, table=True):
      id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
      slug: str = Field(unique=True, index=True, max_length=255)
      title: str = Field(max_length=255)
      excerpt: str | None = Field(default=None, max_length=500)
      body: str                                                    #
  文章正文（前端是段落数组，存为 markdown/JSON 文本）
      category_id: uuid.UUID | None = Field(foreign_key="blogcategory.id", ondelete="SET NULL")
      author_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
      is_published: bool = Field(default=False, index=True)
      published_at: datetime | None = Field(default=None, index=True)
      created_at: datetime | None = Field(default_factory=get_datetime_utc, ...)
      updated_at: datetime | None = Field(default_factory=get_datetime_utc, ...)
      category: Optional["BlogCategory"] = Relationship(back_populates="posts")
      author: Optional["User"] = Relationship(back_populates="blog_posts")
      comments: List["BlogComment"] = Relationship(back_populates="post", cascade_delete=True)

  class BlogComment(SQLModel, table=True):
      id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
      post_id: uuid.UUID = Field(foreign_key="blogpost.id", ondelete="CASCADE", index=True)
      author_id: uuid.UUID | None = Field(foreign_key="user.id", ondelete="SET NULL")  #
  允许匿名
      author_name: str = Field(max_length=80)                       # 兼容匿名用户名
      content: str
      created_at: datetime | None = Field(default_factory=get_datetime_utc, index=True)
      post: Optional["BlogPost"] = Relationship(back_populates="comments")

  同时给 User 加 blog_posts: List["BlogPost"] = Relationship(back_populates="author",
  cascade_delete=True)。

  四、API 端点设计（前缀 /v1/blog）

  Posts（公开 + 后台双视图）
  Method: GET
  Path: /v1/blog/posts
  鉴权: 公开
  用途: 列表（分页、category、q 过滤；仅返回 is_published=true）
  ────────────────────────────────────────
  Method: GET
  Path: /v1/blog/posts/{slug}
  鉴权: 公开
  用途: 详情
  ────────────────────────────────────────
  Method: GET
  Path: /v1/blog/posts/archives
  鉴权: 公开
  用途: 归档：按年/月聚合返回 [{year, month, posts:[{slug,title,date}]}]
  ────────────────────────────────────────
  Method: POST
  Path: /v1/blog/posts
  鉴权: BlogScope.CREATE
  用途: 新建
  ────────────────────────────────────────
  Method: PATCH
  Path: /v1/blog/posts/{post_id}
  鉴权: author 或 BlogScope.ADMIN
  用途: 更新
  ────────────────────────────────────────
  Method: DELETE
  Path: /v1/blog/posts/{post_id}
  鉴权: author 或 BlogScope.ADMIN
  用途: 删除
  ────────────────────────────────────────
  Method: GET
  Path: /v1/blog/posts/admin/list
  鉴权: BlogScope.UPDATE
  用途: 后台列表（含未发布）
  Categories
  ┌────────┬──────────────────────────────────┬─────────────────┬────────────────────┐
  │ Method │               Path               │      鉴权       │        用途        │
  ├────────┼──────────────────────────────────┼─────────────────┼────────────────────┤
  │ GET    │ /v1/blog/categories              │ 公开            │ 全量分类 + 文章数  │
  ├────────┼──────────────────────────────────┼─────────────────┼────────────────────┤
  │ GET    │ /v1/blog/categories/{slug}/posts │ 公开            │ 分类下文章（分页） │
  ├────────┼──────────────────────────────────┼─────────────────┼────────────────────┤
  │ POST   │ /v1/blog/categories              │ BlogScope.ADMIN │ 创建               │
  ├────────┼──────────────────────────────────┼─────────────────┼────────────────────┤
  │ PATCH  │ /v1/blog/categories/{id}         │ BlogScope.ADMIN │ 更新               │
  ├────────┼──────────────────────────────────┼─────────────────┼────────────────────┤
  │ DELETE │ /v1/blog/categories/{id}         │ BlogScope.ADMIN │ 删除               │
  └────────┴──────────────────────────────────┴─────────────────┴────────────────────┘
  Comments
  Method: GET
  Path: /v1/blog/posts/{slug}/comments
  鉴权: 公开
  用途: 评论列表（分页）
  ────────────────────────────────────────
  Method: POST
  Path: /v1/blog/posts/{slug}/comments
  鉴权: 公开（限流）或登录用户
  用途: 提交评论
  ────────────────────────────────────────
  Method: DELETE
  Path: /v1/blog/comments/{id}
  鉴权: author 或 BlogScope.ADMIN
  用途: 删除
  ────────────────────────────────────────
  Method: GET
  Path: /v1/blog/comments/recent
  鉴权: 公开
  用途: 侧栏最近评论（limit 默认 8）
  五、Schemas 设计（schemas.py）

  - CategoryBase / CategoryCreate / CategoryUpdate / CategoryPublic / CategoriesPublic
    - CategoryPublic 多一个 post_count: int
  - PostBase / PostCreate / PostUpdate / PostPublic / PostsPublic
    - PostPublic 内嵌 category: CategoryPublic | None、author_name: str、comments_count: int
    - PostDetailPublic：在 PostPublic 基础上携带 body
  - CommentBase / CommentCreate / CommentPublic / CommentsPublic
  - ArchiveEntry { year, month, posts: list[ArchivePostBrief] } / ArchiveResponse
  - RecentCommentPublic { id, author_name, post_slug, post_title, created_at }

  六、Repository 关键查询要点

  - get_posts：is_published=True 默认，可选 category_slug JOIN，order_by(published_at
  desc)，返回 (items, total)
  - get_post_by_slug：用 selectinload(category) 预加载，避免 N+1
  - list_archives：一次性 select(post.slug, post.title, post.published_at) + 按年月在 Python
  端聚合（PG 也可用 date_trunc）
  - count_posts_by_category：group_by(category_id) 一次拿全部计数
  - list_recent_comments：order_by(created_at desc).limit(n)，selectinload(post)
  - 写操作遵循 model_validate → add/commit/refresh；更新用
  sqlmodel_update(model_dump(exclude_unset=True))

  七、错误码（追加到 app/core/errors.py）

  BLOG_POST_NOT_FOUND
  BLOG_POST_SLUG_TAKEN
  BLOG_CATEGORY_NOT_FOUND
  BLOG_CATEGORY_SLUG_TAKEN
  BLOG_COMMENT_NOT_FOUND
  BLOG_FORBIDDEN_NOT_AUTHOR

  并提供 raise_blog_post_not_found() 等辅助函数，与 user 域风格一致。

  八、权限（追加到 app/core/scopes.py）

  class BlogScope(str, Enum):
      READ   = "blog:read"      # 默认对所有人开放，多数读接口无需校验
      CREATE = "blog:create"
      UPDATE = "blog:update"
      DELETE = "blog:delete"
      ADMIN  = "blog:admin"

  DEFAULT_ROLE_SCOPES：editor 拥有 CREATE/UPDATE，admin 拥有 ADMIN。

  九、路由注册（修改 app/api/v1/api.py）

  from app.domains.blog.router import posts_router, categories_router, comments_router

  router.include_router(posts_router,      prefix="/blog/posts",      tags=["blog-posts"])
  router.include_router(categories_router, prefix="/blog/categories", tags=["blog-categories"])
  router.include_router(comments_router,   prefix="/blog",            tags=["blog-comments"])

  十、开发任务拆分（建议执行顺序）

  1. 模型层：在 core/models.py 加 BlogCategory / BlogPost / BlogComment，给 User 加反向关系
  2. 错误码 & 权限：扩 core/errors.py、core/scopes.py
  3. 迁移：alembic revision --autogenerate -m "add blog domain" → alembic upgrade head
  4. schemas.py：补齐全部 DTO
  5. repository.py：实现 categories → posts → comments → archives 五组函数
  6. router/categories.py：先做最简单的分类 CRUD（无外键依赖）
  7. router/posts.py：实现公开列表/详情、归档、admin 列表、author 校验依赖
  8. router/comments.py：实现评论列表/创建/删除、recent 接口
  9. router/init.py：导出三个 router
  10. api/v1/api.py：注册路由
  11. 种子数据：写一个一次性脚本把 ruanyifeng-clone-quest/src/lib/posts.ts 中的 8 条数据 + 3
  个分类导入数据库（便于前端联调）
  12. 测试：参考 user 域测试风格，覆盖 CRUD、权限、归档聚合、slug 冲突

  十一、需要确认的几个决策点

  - 评论是否允许匿名？前端 recentComments 里 name 直接显示，无 user_id，倾向于「允许匿名 + 必填
  author_name」。不允许匿名，用户增加username 属性
  - 正文存储格式：前端是 body: string[]（段落数组），后端建议存为 markdown
  字符串，由前端按段落解析；或者直接存 JSON 数组（sa_column=Column(JSONB)）。建议 markdown
  字符串，简单通用。 使用 markdown
  - 是否需要草稿/发布工作流：已在模型加入 is_published +
  published_at，足以支撑后台「保存为草稿」。  需要
  - 是否做 RBAC 还是 superuser 简化：参考 user 域既有两套机制，blog 推荐用 scope-based（便于将来 
   editor 角色），简单场景用 get_current_active_superuser 也可。

  确认这些点后即可按"任务拆分"逐步落地。