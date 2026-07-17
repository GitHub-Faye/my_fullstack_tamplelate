/**
 * 业务错误码定义
 *
 * 与后端 apps/api/app/core/errors.py 保持同步
 * 格式: DOMAIN_ACTION_DETAIL
 */

export enum ErrorCode {
  // ==================== 认证相关错误 (AUTH) ====================
  AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS",
  AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN",
  AUTH_EXPIRED_TOKEN = "AUTH_EXPIRED_TOKEN",
  AUTH_INACTIVE_USER = "AUTH_INACTIVE_USER",
  AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS",
  AUTH_MISSING_SCOPE = "AUTH_MISSING_SCOPE",

  // ==================== 用户相关错误 (USER) ====================
  USER_NOT_FOUND = "USER_NOT_FOUND",
  USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS",
  USER_EMAIL_ALREADY_EXISTS = "USER_EMAIL_ALREADY_EXISTS",
  USER_INVALID_PASSWORD = "USER_INVALID_PASSWORD",
  USER_PASSWORD_SAME_AS_OLD = "USER_PASSWORD_SAME_AS_OLD",
  USER_CANNOT_DELETE_SELF = "USER_CANNOT_DELETE_SELF",
  USER_CANNOT_DELETE_SUPERUSER = "USER_CANNOT_DELETE_SUPERUSER",
  USER_ROLE_MISMATCH = "USER_ROLE_MISMATCH",

  // ==================== 物品相关错误 (ITEM) ====================
  ITEM_NOT_FOUND = "ITEM_NOT_FOUND",
  ITEM_NOT_OWNER = "ITEM_NOT_OWNER",

  // ==================== 任务相关错误 (TASK) ====================
  TASK_NOT_FOUND = "TASK_NOT_FOUND",
  TASK_ALREADY_BIDDING = "TASK_ALREADY_BIDDING",
  TASK_NOT_BIDDING = "TASK_NOT_BIDDING",
  TASK_ALREADY_ASSIGNED = "TASK_ALREADY_ASSIGNED",
  TASK_NOT_ASSIGNED_TO_USER = "TASK_NOT_ASSIGNED_TO_USER",
  TASK_INVALID_STATUS_TRANSITION = "TASK_INVALID_STATUS_TRANSITION",
  TASK_BIDDING_WINDOW_CLOSED = "TASK_BIDDING_WINDOW_CLOSED",

  // ==================== 竞价相关错误 (BID) ====================
  BID_NOT_FOUND = "BID_NOT_FOUND",
  BID_ALREADY_EXISTS = "BID_ALREADY_EXISTS",
  BID_CANNOT_UPDATE = "BID_CANNOT_UPDATE",
  BID_WINDOW_CLOSED = "BID_WINDOW_CLOSED",

  // ==================== 日报相关错误 (REPORT) ====================
  REPORT_NOT_FOUND = "REPORT_NOT_FOUND",
  REPORT_ALREADY_SUBMITTED = "REPORT_ALREADY_SUBMITTED",
  REPORT_CANNOT_MODIFY = "REPORT_CANNOT_MODIFY",

  // ==================== 星点相关错误 (STARPOINT) ====================
  STARPOINT_INSUFFICIENT = "STARPOINT_INSUFFICIENT",

  // ==================== 工资相关错误 (SALARY) ====================
  SALARY_PARAM_NOT_SET = "SALARY_PARAM_NOT_SET",

  // ==================== 系统错误 (SYSTEM) ====================
  SYSTEM_INTERNAL_ERROR = "SYSTEM_INTERNAL_ERROR",
  SYSTEM_VALIDATION_ERROR = "SYSTEM_VALIDATION_ERROR",
  SYSTEM_RATE_LIMIT = "SYSTEM_RATE_LIMIT",
}

/**
 * HTTP 状态码映射
 */
export const ERROR_STATUS_MAP: Record<ErrorCode, number> = {
  // 400 Bad Request
  [ErrorCode.AUTH_INVALID_CREDENTIALS]: 400,
  [ErrorCode.AUTH_INVALID_TOKEN]: 400,
  [ErrorCode.AUTH_INACTIVE_USER]: 400,
  [ErrorCode.USER_INVALID_PASSWORD]: 400,
  [ErrorCode.USER_PASSWORD_SAME_AS_OLD]: 400,
  [ErrorCode.SYSTEM_VALIDATION_ERROR]: 400,
  [ErrorCode.TASK_ALREADY_BIDDING]: 400,
  [ErrorCode.TASK_NOT_BIDDING]: 400,
  [ErrorCode.TASK_ALREADY_ASSIGNED]: 400,
  [ErrorCode.TASK_INVALID_STATUS_TRANSITION]: 400,
  [ErrorCode.TASK_BIDDING_WINDOW_CLOSED]: 400,
  [ErrorCode.BID_ALREADY_EXISTS]: 400,
  [ErrorCode.BID_CANNOT_UPDATE]: 400,
  [ErrorCode.BID_WINDOW_CLOSED]: 400,
  [ErrorCode.REPORT_ALREADY_SUBMITTED]: 400,
  [ErrorCode.REPORT_CANNOT_MODIFY]: 400,

  // 401 Unauthorized
  [ErrorCode.AUTH_EXPIRED_TOKEN]: 401,

  // 403 Forbidden
  [ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS]: 403,
  [ErrorCode.AUTH_MISSING_SCOPE]: 403,
  [ErrorCode.USER_CANNOT_DELETE_SELF]: 403,
  [ErrorCode.USER_CANNOT_DELETE_SUPERUSER]: 403,
  [ErrorCode.USER_ROLE_MISMATCH]: 403,
  [ErrorCode.ITEM_NOT_OWNER]: 403,
  [ErrorCode.TASK_NOT_ASSIGNED_TO_USER]: 403,

  // 404 Not Found
  [ErrorCode.USER_NOT_FOUND]: 404,
  [ErrorCode.ITEM_NOT_FOUND]: 404,
  [ErrorCode.TASK_NOT_FOUND]: 404,
  [ErrorCode.BID_NOT_FOUND]: 404,
  [ErrorCode.REPORT_NOT_FOUND]: 404,

  // 409 Conflict
  [ErrorCode.USER_ALREADY_EXISTS]: 409,
  [ErrorCode.USER_EMAIL_ALREADY_EXISTS]: 409,

  // 422 Unprocessable Entity
  [ErrorCode.SALARY_PARAM_NOT_SET]: 422,
  [ErrorCode.STARPOINT_INSUFFICIENT]: 422,

  // 429 Too Many Requests
  [ErrorCode.SYSTEM_RATE_LIMIT]: 429,

  // 500 Internal Server Error
  [ErrorCode.SYSTEM_INTERNAL_ERROR]: 500,
};

/**
 * 默认错误消息
 */
export const DEFAULT_ERROR_MESSAGES: Record<ErrorCode, string> = {
  [ErrorCode.AUTH_INVALID_CREDENTIALS]: "Incorrect email or password",
  [ErrorCode.AUTH_INVALID_TOKEN]: "Invalid token",
  [ErrorCode.AUTH_EXPIRED_TOKEN]: "Token has expired",
  [ErrorCode.AUTH_INACTIVE_USER]: "Inactive user",
  [ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS]: "The user doesn't have enough privileges",
  [ErrorCode.AUTH_MISSING_SCOPE]: "Missing required scope",

  [ErrorCode.USER_NOT_FOUND]: "User not found",
  [ErrorCode.USER_ALREADY_EXISTS]: "User already exists",
  [ErrorCode.USER_EMAIL_ALREADY_EXISTS]: "User with this email already exists",
  [ErrorCode.USER_INVALID_PASSWORD]: "Incorrect password",
  [ErrorCode.USER_PASSWORD_SAME_AS_OLD]: "New password cannot be the same as the current one",
  [ErrorCode.USER_CANNOT_DELETE_SELF]: "Super users are not allowed to delete themselves",
  [ErrorCode.USER_CANNOT_DELETE_SUPERUSER]: "Cannot delete superuser",
  [ErrorCode.USER_ROLE_MISMATCH]: "User role mismatch",

  [ErrorCode.ITEM_NOT_FOUND]: "Item not found",
  [ErrorCode.ITEM_NOT_OWNER]: "Not enough permissions to access this item",

  [ErrorCode.TASK_NOT_FOUND]: "Task not found",
  [ErrorCode.TASK_ALREADY_BIDDING]: "Task is already in bidding",
  [ErrorCode.TASK_NOT_BIDDING]: "Task is not in bidding status",
  [ErrorCode.TASK_ALREADY_ASSIGNED]: "Task is already assigned",
  [ErrorCode.TASK_NOT_ASSIGNED_TO_USER]: "Task is not assigned to this user",
  [ErrorCode.TASK_INVALID_STATUS_TRANSITION]: "Invalid task status transition",
  [ErrorCode.TASK_BIDDING_WINDOW_CLOSED]: "Bidding window has closed",

  [ErrorCode.BID_NOT_FOUND]: "Bid not found",
  [ErrorCode.BID_ALREADY_EXISTS]: "Bid already exists for this task",
  [ErrorCode.BID_CANNOT_UPDATE]: "Cannot update bid",
  [ErrorCode.BID_WINDOW_CLOSED]: "Bidding window has closed",

  [ErrorCode.REPORT_NOT_FOUND]: "Daily report not found",
  [ErrorCode.REPORT_ALREADY_SUBMITTED]: "Daily report already submitted",
  [ErrorCode.REPORT_CANNOT_MODIFY]: "Cannot modify daily report",

  [ErrorCode.STARPOINT_INSUFFICIENT]: "Insufficient starpoint balance",

  [ErrorCode.SALARY_PARAM_NOT_SET]: "Salary parameter not set",

  [ErrorCode.SYSTEM_INTERNAL_ERROR]: "Internal server error",
  [ErrorCode.SYSTEM_VALIDATION_ERROR]: "Validation error",
  [ErrorCode.SYSTEM_RATE_LIMIT]: "Too many requests",
};

/**
 * 错误响应结构
 */
export interface ErrorResponse {
  detail: string | ErrorDetail[];
  code?: ErrorCode;
  data?: Record<string, unknown>;
}

/**
 * 错误详情
 */
export interface ErrorDetail {
  loc?: string[];
  msg: string;
  type?: string;
}

/**
 * 业务异常类
 */
export class BusinessError extends Error {
  public readonly code: ErrorCode;
  public readonly statusCode: number;
  public readonly data?: Record<string, unknown>;

  constructor(
    code: ErrorCode,
    message?: string,
    data?: Record<string, unknown>
  ) {
    const defaultMessage = DEFAULT_ERROR_MESSAGES[code];
    super(message || defaultMessage);

    this.code = code;
    this.statusCode = ERROR_STATUS_MAP[code] || 500;
    this.data = data;

    // 确保 instanceof 正常工作
    Object.setPrototypeOf(this, BusinessError.prototype);
  }

  /**
   * 转换为 JSON 格式
   */
  toJSON(): ErrorResponse {
    const result: ErrorResponse = {
      detail: this.message,
      code: this.code,
    };
    if (this.data) {
      result.data = this.data;
    }
    return result;
  }
}

/**
 * 判断是否为认证错误
 */
export function isAuthError(code: ErrorCode): boolean {
  return code.startsWith("AUTH_");
}

/**
 * 判断是否为用户错误
 */
export function isUserError(code: ErrorCode): boolean {
  return code.startsWith("USER_");
}

/**
 * 判断是否为物品错误
 */
export function isItemError(code: ErrorCode): boolean {
  return code.startsWith("ITEM_");
}

/**
 * 判断是否为任务错误
 */
export function isTaskError(code: ErrorCode): boolean {
  return code.startsWith("TASK_");
}

/**
 * 判断是否为竞价错误
 */
export function isBidError(code: ErrorCode): boolean {
  return code.startsWith("BID_");
}

/**
 * 判断是否为日报错误
 */
export function isReportError(code: ErrorCode): boolean {
  return code.startsWith("REPORT_");
}

/**
 * 判断是否为系统错误
 */
export function isSystemError(code: ErrorCode): boolean {
  return code.startsWith("SYSTEM_");
}
