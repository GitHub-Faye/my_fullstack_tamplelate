/**
 * 跨包契约一致性测试
 *
 * 守护约定：packages/contracts 是 apps/api/app/core/{errors,scopes}.py 的镜像。
 * 任何一边修改字符串集合而忘记同步另一边，本测试都会失败。
 *
 * 同步要求：
 * - ErrorCode 枚举字符串集合逐字相等
 * - ERROR_STATUS_MAP 状态码逐字相等
 * - DEFAULT_ERROR_MESSAGES key 集合逐字相等
 * - UserScope / RoleScope 字符串集合逐字相等
 * - BUILTIN_ROLES 集合逐字相等
 * - DEFAULT_ROLE_SCOPES 每个预置角色的 scope 集合逐字相等
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { DEFAULT_ROLE_SCOPES, UserScope, RoleScope, BUILTIN_ROLES } from "../src/scopes";
import { ErrorCode, ERROR_STATUS_MAP, DEFAULT_ERROR_MESSAGES } from "../src/errors";

// 后端 Python 源文件绝对路径
const API_DIR = resolve(__dirname, "../../../apps/api/app/core");
const ERRORS_PY = readFileSync(`${API_DIR}/errors.py`, "utf-8");
const SCOPES_PY = readFileSync(`${API_DIR}/scopes.py`, "utf-8");

/**
 * 提取 Python 源中 enum/str-enum 的字符串值。
 * 例：USER_NOT_FOUND = "USER_NOT_FOUND" → "USER_NOT_FOUND"
 */
function extractEnumValues(source: string, className: string): string[] {
  const startRe = new RegExp(`class\\s+${className}\\s*\\([^)]*\\)\\s*:`);
  const start = source.search(startRe);
  if (start < 0) return [];
  const bodyStart = start + source.slice(start).match(startRe)![0].length;
  const nextClass = source.indexOf("\nclass ", bodyStart);
  const body = source.slice(bodyStart, nextClass < 0 ? source.length : nextClass);
  const valueRe = /=\s*"([^"]+)"/g;
  const values: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = valueRe.exec(body)) !== null) {
    values.push(m[1]);
  }
  return values;
}

/** 提取 Python dict 源码（用于 ERROR_STATUS_MAP 校验） */
function extractDict(source: string, varName: string): string {
  const re = new RegExp(
    `^${varName}\\s*:[^=]*=\\s*\\{([\\s\\S]*?)^\\}`,
    "m"
  );
  const match = source.match(re);
  return match ? match[1] : "";
}

/** 提取 Python dict 中 `ErrorCode.XXX:` 的 key 集合 */
function extractErrorCodeKeys(source: string, varName: string): string[] {
  const dictBody = extractDict(source, varName);
  const keys: string[] = [];
  const re = /ErrorCode\.(\w+):/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(dictBody)) !== null) {
    keys.push(m[1]);
  }
  return keys;
}

describe("errors.py ↔ errors.ts 镜像", () => {
  it("ErrorCode 枚举字符串集合逐字相等", () => {
    const py = new Set(extractEnumValues(ERRORS_PY, "ErrorCode"));
    const ts = new Set(Object.values(ErrorCode));
    expect([...ts].sort()).toEqual([...py].sort());
  });

  it("ERROR_STATUS_MAP key 集合逐字相等", () => {
    const pyKeys = new Set(extractErrorCodeKeys(ERRORS_PY, "ERROR_STATUS_MAP"));
    const tsKeys = new Set(Object.keys(ERROR_STATUS_MAP));
    expect([...tsKeys].sort()).toEqual([...pyKeys].sort());
  });

  it("DEFAULT_ERROR_MESSAGES key 集合逐字相等", () => {
    const pyKeys = new Set(
      extractErrorCodeKeys(ERRORS_PY, "DEFAULT_ERROR_MESSAGES")
    );
    const tsKeys = new Set(Object.keys(DEFAULT_ERROR_MESSAGES));
    expect([...tsKeys].sort()).toEqual([...pyKeys].sort());
  });

  it("Python ERROR_STATUS_MAP 解析得到的状态码与 TS 一致", () => {
    // 提取 Python 字典形式：ErrorCode.X: status.HTTP_400_BAD_REQUEST,
    const dictBody = extractDict(ERRORS_PY, "ERROR_STATUS_MAP");
    // 状态码名 → 数字映射
    const codeMap: Record<string, number> = {
      HTTP_400_BAD_REQUEST: 400,
      HTTP_401_UNAUTHORIZED: 401,
      HTTP_403_FORBIDDEN: 403,
      HTTP_404_NOT_FOUND: 404,
      HTTP_409_CONFLICT: 409,
      HTTP_422_UNPROCESSABLE_CONTENT: 422,
      HTTP_422_UNPROCESSABLE_ENTITY: 422,
      HTTP_429_TOO_MANY_REQUESTS: 429,
      HTTP_500_INTERNAL_SERVER_ERROR: 500,
    };
    const pyMap = new Map<string, number>();
    const lineRe = /ErrorCode\.(\w+):\s*status\.(\w+),/g;
    let m: RegExpExecArray | null;
    while ((m = lineRe.exec(dictBody)) !== null) {
      const code = codeMap[m[2]];
      if (code === undefined) {
        throw new Error(`未知 status 常量 ${m[2]}，请同步 codeMap`);
      }
      pyMap.set(m[1], code);
    }
    for (const [code, status] of pyMap.entries()) {
      expect(ERROR_STATUS_MAP[code as ErrorCode]).toBe(status);
    }
  });
});

describe("scopes.py ↔ scopes.ts 镜像", () => {
  it("UserScope 字符串集合逐字相等", () => {
    const py = new Set(extractEnumValues(SCOPES_PY, "UserScope"));
    const ts = new Set(Object.values(UserScope));
    expect([...ts].sort()).toEqual([...py].sort());
  });

  it("RoleScope 字符串集合逐字相等", () => {
    const py = new Set(extractEnumValues(SCOPES_PY, "RoleScope"));
    const ts = new Set(Object.values(RoleScope));
    expect([...ts].sort()).toEqual([...py].sort());
  });

  it("BUILTIN_ROLES 集合逐字相等", () => {
    const pyMatch = SCOPES_PY.match(/BUILTIN_ROLES\s*=\s*\(([^)]+)\)/);
    expect(pyMatch).not.toBeNull();
    const pyRoles = new Set(
      (pyMatch![1].match(/"([^"]+)"/g) || []).map((s) => s.replace(/"/g, ""))
    );
    expect(new Set(BUILTIN_ROLES)).toEqual(pyRoles);
  });

  it("DEFAULT_ROLE_SCOPES 三个预置角色 keys 完全覆盖", () => {
    const pyMatch = SCOPES_PY.match(/DEFAULT_ROLE_SCOPES\s*=\s*\{([\s\S]*?)\n\}/);
    expect(pyMatch).not.toBeNull();
    const pyKeys = new Set<string>();
    const keyRe = /"(\w+)":\s*\[/g;
    let m: RegExpExecArray | null;
    while ((m = keyRe.exec(pyMatch![1])) !== null) {
      pyKeys.add(m[1]);
    }
    const tsKeys = new Set(Object.keys(DEFAULT_ROLE_SCOPES));
    expect([...tsKeys].sort()).toEqual([...pyKeys].sort());
  });
});
