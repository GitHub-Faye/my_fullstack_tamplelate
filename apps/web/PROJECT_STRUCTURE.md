# Web Frontend Project Structure

## Overview

This is a Next.js 16 frontend application built with React 19, TypeScript, Tailwind CSS 4.x, and shadcn/ui components. It uses TanStack Query for server state management and Zustand for client state.

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Next.js 16 (App Router) |
| React | React 19 (with Compiler) |
| Language | TypeScript 5.9 |
| Styling | Tailwind CSS 4.x |
| UI Components | shadcn/ui |
| Forms | React Hook Form + Zod |
| Server State | TanStack Query v5 |
| Client State | Zustand |
| Notifications | Sonner |
| API Client | @hey-api/client-fetch |
| Icons | Lucide React |

## Project Structure

```
apps/web/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth route group
│   │   ├── layout.tsx            # Auth layout (centered, minimal)
│   │   ├── login/
│   │   │   └── page.tsx          # Login page
│   │   ├── signup/
│   │   │   └── page.tsx          # Registration page
│   │   ├── recover-password/
│   │   │   └── page.tsx          # Password recovery request
│   │   └── reset-password/
│   │       ├── page.tsx          # Reset password wrapper
│   │       └── ResetPasswordForm.tsx  # Reset password form
│   ├── (dashboard)/              # Dashboard route group
│   │   ├── layout.tsx            # Dashboard layout with sidebar
│   │   ├── page.tsx              # Dashboard home/overview
│   │   ├── admin/
│   │   │   ├── page.tsx          # User management (admin only)
│   │   │   └── users/
│   │   │       ├── new/
│   │   │       │   └── page.tsx  # Create new user
│   │   │       └── [id]/
│   │   │           └── edit/
│   │   │               └── page.tsx  # Edit user
│   │   ├── items/
│   │   │   ├── page.tsx          # Items list
│   │   │   ├── new/
│   │   │   │   └── page.tsx      # Create new item
│   │   │   └── [id]/
│   │   │       └── edit/
│   │   │           └── page.tsx  # Edit item
│   │   └── settings/
│   │       └── page.tsx          # User settings (profile, password)
│   ├── layout.tsx                # Root layout with providers
│   ├── globals.css               # Global styles
│   └── page.tsx                  # Landing page (redirects to dashboard)
├── components/
│   └── ui/                       # shadcn/ui components
│       ├── alert.tsx
│       ├── avatar.tsx
│       ├── badge.tsx
│       ├── button.tsx
│       ├── card.tsx
│       ├── checkbox.tsx          # Added for forms
│       ├── dialog.tsx            # Added for confirmations
│       ├── dropdown-menu.tsx
│       ├── form.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── separator.tsx
│       ├── sheet.tsx
│       ├── skeleton.tsx
│       ├── sonner.tsx
│       ├── table.tsx
│       └── textarea.tsx
├── features/
│   └── auth/
│       ├── api/
│       │   └── login.ts          # Login API functions
│       ├── components/
│       │   └── LoginForm.tsx     # Login form component
│       ├── hooks/
│       │   └── useLogin.ts       # Login mutation hook
│       └── schemas.ts            # Auth form schemas
├── src/
│   ├── lib/
│   │   ├── api-sdk.ts            # SDK client configuration
│   │   └── utils.ts              # Utility functions (cn)
│   ├── stores/
│   │   └── auth.ts               # Auth store (Zustand)
│   └── providers.tsx             # App providers (QueryClient)
├── public/                       # Static assets
├── components.json               # shadcn/ui config
├── next.config.js                # Next.js config
├── package.json
├── postcss.config.mjs
├── tailwind.config.ts
└── tsconfig.json
```

## Route Structure

### Public Routes (No Auth Required)
- `/login` - Login page
- `/signup` - Registration page
- `/recover-password` - Password recovery
- `/reset-password` - Password reset (requires token)

### Protected Routes (Requires Auth)
- `/dashboard` - Dashboard overview
- `/dashboard/items` - Items list
- `/dashboard/items/new` - Create item
- `/dashboard/items/[id]/edit` - Edit item
- `/dashboard/settings` - User settings
- `/dashboard/admin` - User management (admin only)
- `/dashboard/admin/users/new` - Create user (admin only)
- `/dashboard/admin/users/[id]/edit` - Edit user (admin only)

## Key Features

### Authentication
- JWT token-based authentication
- Token stored in localStorage via Zustand persist
- Automatic token attachment to API requests
- Login, signup, password recovery flows

### Dashboard Layout
- Responsive sidebar navigation
- Collapsible on mobile (sheet component)
- User menu with avatar and dropdown
- Admin-only navigation items

### Data Fetching
- TanStack Query for server state
- Automatic caching and refetching
- Loading and error states
- Optimistic updates

### Forms
- React Hook Form for form management
- Zod for validation
- shadcn/ui form components
- Toast notifications for feedback

### UI Components
All shadcn/ui components are in `components/ui/`:
- Form inputs (Input, Textarea, Checkbox)
- Layout (Card, Sheet, Dialog)
- Feedback (Toast via Sonner)
- Navigation (Button, Dropdown Menu)
- Data display (Table, Badge, Avatar)

## API Integration

The app uses the `@repo/sdk` package generated from the backend OpenAPI spec:

```typescript
// Example usage
import { readItemsV1ItemsItemsGet, createItemV1ItemsItemsPost } from '@repo/sdk';

// Get items
const { data } = useQuery({
  queryKey: ['items'],
  queryFn: async () => {
    const response = await readItemsV1ItemsItemsGet();
    return response.data;
  },
});

// Create item
const mutation = useMutation({
  mutationFn: async (data: ItemCreate) => {
    const response = await createItemV1ItemsItemsPost({ body: data });
    return response.data;
  },
});
```

## State Management

### Auth Store (Zustand)
```typescript
// src/stores/auth.ts
- user: UserPublic | null
- token: string | null
- setUser(user)
- setToken(token)
- logout()
```

### Server State (TanStack Query)
- Items list: `['items']`
- Single item: `['item', id]`
- Users list: `['users']`
- Single user: `['user', id]`
- Current user: `['currentUser']`

## Development

### Install Dependencies
```bash
pnpm install
```

### Run Development Server
```bash
pnpm dev
```

### Build for Production
```bash
pnpm build
```

### Type Check
```bash
pnpm check-types
```

### Lint
```bash
pnpm lint
```

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Dependencies

### Production
- next
- react, react-dom
- @tanstack/react-query
- @tanstack/react-query-devtools
- zustand
- react-hook-form
- @hookform/resolvers
- zod
- sonner
- lucide-react
- class-variance-authority
- clsx, tailwind-merge
- @radix-ui/* (various components)

### Development
- typescript
- @types/node, @types/react, @types/react-dom
- tailwindcss
- @tailwindcss/postcss
- postcss
- autoprefixer
- eslint

## Notes

- The SDK package (`@repo/sdk`) must be built before the web app
- All API calls go through the generated SDK client
- Forms use controlled components with React Hook Form
- Toast notifications use Sonner for user feedback
- The dashboard layout is responsive and works on mobile
- Admin routes are protected by checking `user.is_superuser`
