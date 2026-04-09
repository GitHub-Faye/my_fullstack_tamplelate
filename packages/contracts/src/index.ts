/**
 * @repo/contracts - 前后端共享业务契约层
 *
 * 此包包含不适合/无法从 OpenAPI 自动生成的业务语义契约：
 * - 错误码 (ErrorCode)
 * - 权限 Scope
 * - 分页协议
 * - 业务常量
 *
 * 与 @repo/sdk 共同组成完整的"业务契约层"
 * - @repo/sdk: OpenAPI 自动生成的接口契约
 * - @repo/contracts: 手动维护的业务语义契约
 */

// 错误码
export * from './errors.js';

// 权限 Scope
export * from './scopes.js';

// 分页协议
export * from './pagination.js';

// 业务常量
export * from './constants.js';
