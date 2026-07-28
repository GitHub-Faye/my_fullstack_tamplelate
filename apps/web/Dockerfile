# Stage 1: Build
FROM node:22-alpine AS builder
# 用淘宝镜像源安装 pnpm
RUN npm config set registry https://registry.npmmirror.com && \
    npm install -g pnpm@9

WORKDIR /app

# 复制根目录配置文件
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./

# 复制所有 workspace 包的 package.json（只装依赖时不复制源码，利用缓存）
COPY packages/sdk/package.json packages/sdk/
COPY packages/ui/package.json packages/ui/
COPY packages/contracts/package.json packages/contracts/
COPY packages/eslint-config/package.json packages/eslint-config/
COPY packages/typescript-config/package.json packages/typescript-config/
COPY apps/web/package.json apps/web/

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制所有 workspace 包源码
COPY packages/ packages/

# 先构建需要编译的 workspace 包
RUN pnpm --filter @repo/sdk build
RUN pnpm --filter @repo/contracts build

# 复制前端源码
COPY apps/web/ apps/web/

# 构建 Next.js（运行时注入后端地址）
ARG NEXT_PUBLIC_API_URL=http://82.157.96.215:8111
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN pnpm --filter web build

# Stage 2: Production runner
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 复制 standalone 产物
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

EXPOSE 3000
ENV PORT=3000
CMD ["node", "apps/web/server.js"]
