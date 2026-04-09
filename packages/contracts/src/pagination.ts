/**
 * 统一分页协议
 * 
 * 与后端 apps/api/app/core/schemas.py 保持同步
 */

/**
 * 分页响应结构
 */
export interface PaginatedResponse<T> {
  /** 数据列表 */
  data: T[];
  /** 总记录数 */
  count: number;
  /** 当前页码 (从 1 开始) */
  page?: number;
  /** 每页大小 */
  page_size?: number;
  /** 总页数 */
  total_pages?: number;
}

/**
 * 分页查询参数
 */
export interface PaginationParams {
  /** 页码，从 1 开始 */
  page: number;
  /** 每页数量，默认 20，最大 100 */
  page_size: number;
}

/**
 * 默认分页参数
 */
export const DEFAULT_PAGINATION: PaginationParams = {
  page: 1,
  page_size: 20,
};

/**
 * 最大每页数量
 */
export const MAX_PAGE_SIZE = 100;

/**
 * 分页参数验证
 */
export function validatePagination(params: Partial<PaginationParams>): PaginationParams {
  let page = params.page ?? DEFAULT_PAGINATION.page;
  let page_size = params.page_size ?? DEFAULT_PAGINATION.page_size;

  // 确保 page 至少为 1
  if (page < 1) {
    page = 1;
  }

  // 限制 page_size 范围
  if (page_size < 1) {
    page_size = 1;
  } else if (page_size > MAX_PAGE_SIZE) {
    page_size = MAX_PAGE_SIZE;
  }

  return { page, page_size };
}

/**
 * 计算 offset
 */
export function calculateOffset(page: number, pageSize: number): number {
  return (page - 1) * pageSize;
}

/**
 * 计算总页数
 */
export function calculateTotalPages(totalCount: number, pageSize: number): number {
  return Math.ceil(totalCount / pageSize);
}

/**
 * 构建分页响应
 */
export function buildPaginatedResponse<T>(
  data: T[],
  totalCount: number,
  page: number,
  pageSize: number
): PaginatedResponse<T> {
  return {
    data,
    count: totalCount,
    page,
    page_size: pageSize,
    total_pages: calculateTotalPages(totalCount, pageSize),
  };
}

/**
 * 通用消息响应
 */
export interface MessageResponse {
  message: string;
}

/**
 * 批量操作结果
 */
export interface BulkOperationResult {
  /** 成功数量 */
  success_count: number;
  /** 失败数量 */
  failed_count: number;
  /** 错误详情列表 */
  errors?: Array<{
    id?: string;
    message: string;
  }>;
}
