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
| Testing | Vitest + @testing-library/react + MSW |

## Project Structure

```
apps/web/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth route group
│   │   ├── layout.tsx            # Auth layout (centered, minimal)
│   │   ├── login/
│   │   │   └── page.tsx          # Login page
│   │   └── signup/
│   │       └── page.tsx          # Registration page
│   ├── (dashboard)/              # Dashboard route group
│   │   ├── layout.tsx            # Dashboard layout with sidebar
│   │   ├── dashboard/
│   │   │   ├── page.tsx          # Dashboard home/overview
│   │   │   ├── admin/
│   │   │   │   ├── page.tsx      # User management (admin only)
│   │   │   │   └── users/
│   │   │   │       ├── new/
│   │   │   │       │   └── page.tsx  # Create new user
│   │   │   │       └── [id]/
│   │   │   │           └── edit/
│   │   │   │               └── page.tsx  # Edit user
│   │   │   ├── items/
│   │   │   │   ├── page.tsx      # Items list
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx  # Create new item
│   │   │   │   └── [id]/
│   │   │   │       └── edit/
│   │   │   │           └── page.tsx  # Edit item
│   │   │   └── settings/
│   │   │       └── page.tsx      # User settings (profile, password)
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
│       ├── checkbox.tsx
│       ├── dialog.tsx
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
├── features/                     # Feature-based modules
│   ├── item/                     # Item management feature
│   │   ├── api/
│   │   │   ├── queries.ts        # TanStack Query hooks
│   │   │   └── queries.test.ts   # Query tests
│   │   ├── components/
│   │   │   ├── ItemForm.tsx      # Create/Edit item form
│   │   │   ├── ItemForm.test.tsx # Form tests
│   │   │   ├── ItemTable.tsx     # Items list table
│   │   │   └── ItemTable.test.tsx # Table tests
│   │   ├── schemas.ts            # Zod validation schemas
│   │   ├── schemas.test.ts       # Schema tests
│   │   └── index.ts              # Feature exports
│   └── user/                     # User management feature
│       ├── api/
│       │   ├── queries.ts        # TanStack Query hooks
│       │   └── queries.test.ts   # Query tests
│       ├── components/
│       │   ├── DashboardLayout.tsx   # Dashboard layout with sidebar
│       │   ├── UserForm.tsx      # Create/Edit user form
│       │   ├── UserForm.test.tsx # Form tests
│       │   ├── UserTable.tsx     # Users list table
│       │   └── UserTable.test.tsx # Table tests
│       ├── schemas.ts            # Zod validation schemas
│       ├── schemas.test.ts       # Schema tests
│       └── index.ts              # Feature exports
├── src/
│   ├── lib/
│   │   ├── api-sdk.ts            # SDK client configuration
│   │   └── utils.ts              # Utility functions (cn)
│   ├── stores/
│   │   └── auth.ts               # Auth store (Zustand)
│   └── providers.tsx             # App providers (QueryClient)
├── test/                         # Test infrastructure
│   ├── mocks/
│   │   ├── handlers.ts           # MSW API mock handlers
│   │   └── server.ts             # MSW server setup
│   ├── setup.ts                  # Test setup and configuration
│   └── utils.tsx                 # Test utilities and helpers
├── public/                       # Static assets
├── components.json               # shadcn/ui config
├── middleware.ts                 # Next.js middleware (auth protection)
├── next.config.js                # Next.js config
├── package.json
├── postcss.config.mjs
├── tailwind.config.ts
├── tsconfig.json
└── vitest.config.ts              # Vitest configuration
```

## Route Structure

### Public Routes (No Auth Required)
- `/login` - Login page
- `/signup` - Registration page

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
- Cookie-based token for SSR/middleware compatibility
- Automatic token attachment to API requests
- Login, signup flows
- Middleware protection for dashboard routes

### Dashboard Layout
- Responsive sidebar navigation
- Collapsible on mobile (sheet component)
- User menu with avatar and dropdown
- Admin-only navigation items
- Items management navigation

### Data Fetching
- TanStack Query for server state
- Automatic caching and refetching
- Loading and error states
- Optimistic updates
- Query key factory pattern

### Forms
- React Hook Form for form management
- Zod for validation
- shadcn/ui form components
- Toast notifications for feedback
- Reusable form components for create/edit

### UI Components
All shadcn/ui components are in `components/ui/`:
- Form inputs (Input, Textarea, Checkbox)
- Layout (Card, Sheet, Dialog)
- Feedback (Toast via Sonner)
- Navigation (Button, Dropdown Menu)
- Data display (Table, Badge, Avatar, Skeleton)

## Feature-Based Architecture

The project uses a feature-based folder structure:

```
features/
├── item/                         # Item management feature
│   ├── api/                      # API layer (TanStack Query hooks)
│   ├── components/               # Feature-specific components
│   ├── schemas.ts                # Validation schemas
│   └── index.ts                  # Public exports
└── user/                         # User management feature
    ├── api/
    ├── components/
    ├── schemas.ts
    └── index.ts
```

Each feature is self-contained with its own:
- API hooks for data fetching
- Components for UI
- Schemas for validation
- Tests for quality assurance

## API Integration

The app uses the `@repo/sdk` package generated from the backend OpenAPI spec:

```typescript
// Example usage
import { useItems, useCreateItem } from '@/features/item/api/queries';

// Get items
const { data, isLoading } = useItems(0, 10);

// Create item
const createMutation = useCreateItem();
createMutation.mutate({ title: 'New Item', description: 'Description' });
```

## State Management

### Auth Store (Zustand)
```typescript
// src/stores/auth.ts
- user: UserPublic | null
- token: string | null
- isAuthenticated: boolean
- setUser(user)
- setToken(token)
- logout()
```

### Server State (TanStack Query)
Query keys follow a factory pattern:
- Items list: `['items', 'list', { skip, limit }]`
- Single item: `['items', 'detail', id]`
- Users list: `['users', 'list', { skip, limit }]`
- Single user: `['users', 'detail', id]`
- Current user: `['users', 'me']`

## Testing

The project uses Vitest with @testing-library/react and MSW for testing:

### Test Structure
```
test/
├── mocks/
│   ├── handlers.ts           # API mock handlers
│   └── server.ts             # MSW server setup
├── setup.ts                  # Test configuration
└── utils.tsx                 # Test utilities
```

### Running Tests
```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run tests with coverage
pnpm test:coverage
```

### Test Types
- **Unit Tests**: Schema validation, utility functions
- **Component Tests**: Form rendering, user interactions
- **Integration Tests**: API hooks with mocked responses

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

### Test
```bash
pnpm test
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
- vitest
- @testing-library/react
- @testing-library/jest-dom
- @testing-library/user-event
- msw
- jsdom

## Notes

- The SDK package (`@repo/sdk`) must be built before the web app
- All API calls go through the generated SDK client
- Forms use controlled components with React Hook Form
- Toast notifications use Sonner for user feedback
- The dashboard layout is responsive and works on mobile
- Admin routes are protected by checking `user.is_superuser`
- Tests use MSW to mock API responses at the network level
- Query keys use a factory pattern for consistency
