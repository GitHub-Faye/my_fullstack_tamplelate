"""统一分页工具。"""


def total_pages(*, count: int, page_size: int) -> int:
    """计算分页总页数，空结果保持返回 0。"""
    return (count + page_size - 1) // page_size if count > 0 else 0


def paginated_fields(*, count: int, page: int, page_size: int) -> dict[str, int]:
    """返回统一分页元数据，供各领域响应模型复用。"""
    return {
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(count=count, page_size=page_size),
    }
