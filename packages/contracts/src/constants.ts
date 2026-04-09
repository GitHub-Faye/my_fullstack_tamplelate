/**
 * 业务常量定义
 * 
 * 前端 UI 依赖的稳定业务常量
 */

// ==================== 用户相关常量 ====================

/**
 * 用户状态
 */
export const UserStatus = {
  /** 激活 */
  ACTIVE: "active",
  /** 未激活 */
  INACTIVE: "inactive",
  /** 已禁用 */
  DISABLED: "disabled",
} as const;

export type UserStatusType = typeof UserStatus[keyof typeof UserStatus];

/**
 * 用户角色
 */
export const UserRole = {
  /** 普通用户 */
  USER: "user",
  /** 编辑者 */
  EDITOR: "editor",
  /** 管理员 */
  ADMIN: "admin",
  /** 超级管理员 */
  SUPERUSER: "superuser",
} as const;

export type UserRoleType = typeof UserRole[keyof typeof UserRole];

// ==================== 认证相关常量 ====================

/**
 * Token 类型
 */
export const TokenType = {
  /** Bearer Token */
  BEARER: "bearer",
} as const;

export type TokenTypeType = typeof TokenType[keyof typeof TokenType];

/**
 * 本地存储 Key
 */
export const StorageKeys = {
  /** Access Token */
  ACCESS_TOKEN: "access_token",
  /** Refresh Token */
  REFRESH_TOKEN: "refresh_token",
  /** 用户信息 */
  USER_INFO: "user_info",
  /** 主题设置 */
  THEME: "theme",
  /** 语言设置 */
  LOCALE: "locale",
} as const;

// ==================== 分页相关常量 ====================

/**
 * 分页选项
 */
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;

// ==================== 文件相关常量 ====================

/**
 * 文件类型
 */
export const FileType = {
  /** 图片 */
  IMAGE: "image",
  /** 文档 */
  DOCUMENT: "document",
  /** 视频 */
  VIDEO: "video",
  /** 音频 */
  AUDIO: "audio",
  /** 其他 */
  OTHER: "other",
} as const;

export type FileTypeType = typeof FileType[keyof typeof FileType];

/**
 * 图片 MIME 类型
 */
export const IMAGE_MIME_TYPES = [
  "image/jpeg",
  "image/png",
  "image/gif",
  "image/webp",
  "image/svg+xml",
] as const;

/**
 * 文档 MIME 类型
 */
export const DOCUMENT_MIME_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "text/plain",
] as const;

/**
 * 默认文件大小限制 (10MB)
 */
export const DEFAULT_FILE_SIZE_LIMIT = 10 * 1024 * 1024;

// ==================== 时间相关常量 ====================

/**
 * 日期格式
 */
export const DATE_FORMATS = {
  /** 标准日期时间 */
  DATETIME: "YYYY-MM-DD HH:mm:ss",
  /** 日期 */
  DATE: "YYYY-MM-DD",
  /** 时间 */
  TIME: "HH:mm:ss",
  /** ISO 格式 */
  ISO: "YYYY-MM-DDTHH:mm:ssZ",
} as const;

// ==================== HTTP 状态码分组 ====================

/**
 * HTTP 状态码分组
 */
export const HttpStatusGroups = {
  /** 成功 */
  SUCCESS: [200, 201, 204],
  /** 客户端错误 */
  CLIENT_ERROR: [400, 401, 403, 404, 409, 422, 429],
  /** 服务端错误 */
  SERVER_ERROR: [500, 502, 503, 504],
} as const;

/**
 * 检查状态码是否为成功
 */
export function isSuccessStatus(status: number): boolean {
  return status >= 200 && status < 300;
}

/**
 * 检查状态码是否为客户端错误
 */
export function isClientErrorStatus(status: number): boolean {
  return status >= 400 && status < 500;
}

/**
 * 检查状态码是否为服务端错误
 */
export function isServerErrorStatus(status: number): boolean {
  return status >= 500 && status < 600;
}
