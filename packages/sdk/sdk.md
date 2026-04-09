# 前后端共同理解业务语义
# sdk 和contracts共同组成 前后端共享的“业务契约层“

sdk为hey api 和其插件{
        '@hey-api/typescript',
      '@hey-api/sdk',
      'zod',
      '@hey-api/client-fetch',
      '@tanstack/react-query',          // ← can often be just the string
}
从 OpenAPI 自动生成的接口标准