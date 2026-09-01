/**
 * Vitest 全局测试环境初始化
 *
 * 为所有 web 测试提供：
 * - jest-dom 匹配器（toBeInTheDocument 等）
 * - DOM 清理（每个用例后自动 cleanup，避免泄漏）
 * - 类库级环境模拟（matchMedia / ResizeObserver）
 *
 * 约定：此文件被 vitest.config.ts 的 setupFiles 引用，任何公共 stub
 * 都应加在这里，而不是散落在用例里。
 */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// 每个用例结束后卸载已渲染组件，防止 DOM 泄漏
afterEach(() => {
  cleanup();
});

// ---- 浏览器 API stub（jsdom 缺失项）----

// matchMedia：next-themes / 媒体查询组件依赖
if (!window.matchMedia) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

// ResizeObserver：Radix UI 组件依赖
if (!window.ResizeObserver) {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  Object.defineProperty(window, "ResizeObserver", {
    writable: true,
    value: ResizeObserverStub,
  });
}

// scrollTo：部分交互用例需要
if (!window.scrollTo) {
  Object.defineProperty(window, "scrollTo", {
    writable: true,
    value: vi.fn(),
  });
}