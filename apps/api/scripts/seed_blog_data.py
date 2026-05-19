"""
Blog 域种子数据脚本

将预设的分类和文章数据导入数据库，便于前端联调。
用法：
    cd apps/api
    python -m scripts.seed_blog_data

依赖：需要先有已注册的用户（通过 API 或脚本创建）。
"""

import asyncio
import uuid
from datetime import datetime, timezone

from app.core.database import async_session_factory
from app.core.models import BlogCategory, BlogPost


# ========== 预定义分类 ==========
CATEGORIES = [
    {"name": "周刊", "slug": "weekly"},
    {"name": "随笔", "slug": "essay"},
    {"name": "档案", "slug": "archive"},
]

# ========== 预定义文章 ==========
POSTS = [
    {
        "slug": "weekly-issue-1",
        "title": "科技爱好者周刊（第 1 期）：互联网的黄金时代",
        "excerpt": "互联网的黄金时代已经过去了吗？本期周刊探讨了这个问题。",
        "body": "## 互联网的黄金时代\n\n互联网的黄金时代已经过去了吗？\n\n这是一个值得思考的问题。在 90 年代和 21 世纪初，互联网充满了可能性和创新。\n\n但现在，互联网似乎被几个巨头所垄断。\n\n不过，我相信 Web3 和去中心化技术会带来新的机遇。",
        "category_slug": "weekly",
        "is_published": True,
    },
    {
        "slug": "weekly-issue-2",
        "title": "科技爱好者周刊（第 2 期）：程序员的中年危机",
        "excerpt": "程序员到了 35 岁该怎么办？本期周刊探讨了程序员的职业发展路径。",
        "body": "## 程序员的中年危机\n\n在中国，程序员 35 岁中年危机是一个热门话题。\n\n但我觉得这不是年龄的问题，而是技能更新的问题。\n\n持续学习，保持好奇心，这才是程序员的核心竞争力。",
        "category_slug": "weekly",
        "is_published": True,
    },
    {
        "slug": "weekly-issue-3",
        "title": "科技爱好者周刊（第 3 期）：AI 时代的编程",
        "excerpt": "AI 会取代程序员吗？本期周刊讨论了 AI 对编程行业的影响。",
        "body": "## AI 时代的编程\n\nGitHub Copilot 和 ChatGPT 的出现，让很多人担心程序员会被取代。\n\n但我觉得 AI 是一个强大的工具，而不是威胁。\n\n程序员应该学会利用 AI 提高效率，专注于更高层次的设计和决策。",
        "category_slug": "weekly",
        "is_published": True,
    },
    {
        "slug": "essay-think-about-software",
        "title": "关于软件开发的几点思考",
        "excerpt": "软件开发不仅仅是写代码，更是一种思维方式。",
        "body": "## 关于软件开发的几点思考\n\n### 1. 代码是负债\n\n每一行代码都是维护成本。好的代码应该简洁、清晰、易于理解。\n\n### 2. 测试是投资\n\n写测试看起来费时间，但从长远来看，它可以节省大量的调试时间。\n\n### 3. 文档是资产\n\n好的文档可以降低团队沟通成本，提高开发效率。",
        "category_slug": "essay",
        "is_published": True,
    },
    {
        "slug": "essay-remote-work",
        "title": "远程工作的利与弊",
        "excerpt": "疫情之后，远程工作成了常态，但它真的适合所有人吗？",
        "body": "## 远程工作的利与弊\n\n### 优点\n\n- 省去通勤时间\n- 更灵活的时间安排\n- 可以居住在成本更低的地方\n\n### 缺点\n\n- 社交隔离\n- 工作与生活的界限模糊\n- 协作效率可能降低\n\n总的来说，远程工作是一种趋势，但需要根据个人和团队的情况来调整。",
        "category_slug": "essay",
        "is_published": True,
    },
    {
        "slug": "essay-writing-good-code",
        "title": "写好代码的几个原则",
        "excerpt": "什么样的代码才是好代码？这篇文章分享了一些个人经验。",
        "body": "## 写好代码的几个原则\n\n### KISS 原则\n\nKeep It Simple, Stupid - 保持简单。\n\n### DRY 原则\n\nDon't Repeat Yourself - 不要重复自己。\n\n### YAGNI 原则\n\nYou Ain't Gonna Need It - 不要过度设计。\n\n### 单一职责\n\n每个函数、每个类应该只做一件事。",
        "category_slug": "essay",
        "is_published": True,
    },
    {
        "slug": "archive-hacker-news-2024",
        "title": "Hacker News 2024 年度最佳文章汇总",
        "excerpt": "整理了 2024 年 Hacker News 上最受欢迎的 50 篇文章。",
        "body": "## Hacker News 2024 年度最佳文章\n\n### 编程相关\n\n1. 如何成为一名优秀的开源维护者\n2. 为什么你应该使用 Rust\n3. TypeScript 5.0 的新特性\n\n### 创业相关\n\n4. 从 0 到 1：一个 SaaS 产品的诞生\n5. 独立开发者的生存指南\n\n（完整列表请查看原文）",
        "category_slug": "archive",
        "is_published": True,
    },
    {
        "slug": "archive-fullstack-guide",
        "title": "全栈开发入门指南（2024 版）",
        "excerpt": "一份完整的全栈开发学习路线图。",
        "body": "## 全栈开发入门指南\n\n### 前端\n\n- HTML/CSS/JavaScript 基础\n- React 或 Vue\n- Next.js 或 Nuxt.js\n\n### 后端\n\n- Python/FastAPI 或 Node.js/Express\n- 数据库：PostgreSQL\n- ORM：SQLAlchemy 或 Prisma\n\n### DevOps\n\n- Docker\n- CI/CD\n- 云服务（AWS/Vercel）",
        "category_slug": "archive",
        "is_published": True,
    },
]


async def seed() -> None:
    """执行种子数据导入"""
    async with async_session_factory() as session:
        # 1. 查找第一个已注册用户作为默认作者
        from sqlalchemy import select
        from app.core.models import User

        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            print("❌ 未找到任何用户，请先通过 API 或脚本创建用户！")
            return

        print(f"✅ 使用用户: {user.username} ({user.email})")

        # 2. 导入分类
        cat_map: dict[str, uuid.UUID] = {}
        for cat_data in CATEGORIES:
            existing = await session.execute(
                select(BlogCategory).where(BlogCategory.slug == cat_data["slug"])
            )
            existing = existing.scalar_one_or_none()
            if not existing:
                cat = BlogCategory(**cat_data)
                session.add(cat)
                await session.flush()
                cat_map[cat.slug] = cat.id
                print(f"   ➕ 创建分类: {cat.name}")
            else:
                cat_map[existing.slug] = existing.id
                print(f"   ⏭️ 分类已存在: {existing.name}")

        # 3. 导入文章
        now = datetime.now(timezone.utc)
        imported = 0
        for i, post_data in enumerate(POSTS):
            existing = await session.execute(
                select(BlogPost).where(BlogPost.slug == post_data["slug"])
            )
            existing = existing.scalar_one_or_none()
            if existing:
                print(f"   ⏭️ 文章已存在: {post_data['title']}")
                continue

            category_slug = post_data.pop("category_slug")
            post = BlogPost(
                **post_data,
                category_id=cat_map.get(category_slug),
                author_id=user.id,
                published_at=now if post_data["is_published"] else None,
                created_at=now,
                updated_at=now,
            )
            session.add(post)
            imported += 1
            print(f"   ➕ 创建文章: {post.title}")

        await session.commit()
        print(f"\n🎉 种子数据导入完成！共创建 {len(CATEGORIES)} 个分类, {imported} 篇文章。")


if __name__ == "__main__":
    asyncio.run(seed())