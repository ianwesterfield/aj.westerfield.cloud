#!/usr/bin/env python3
"""
React Development Training Data Generator
Target: ~250 examples for React, hooks, state management, Next.js patterns
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for React development.
You help with React components, hooks, state management, and modern React patterns."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

REACT_CLI_TASKS = [
    {
        "instruction": "Create new React project with Vite",
        "command": "npm create vite@latest my-app -- --template react-ts",
        "explanation": "Creates React + TypeScript project with Vite (faster than CRA)"
    },
    {
        "instruction": "Create Next.js project",
        "command": "npx create-next-app@latest my-app --typescript --tailwind --eslint --app --src-dir",
        "explanation": "Creates Next.js 14+ with App Router, TypeScript, Tailwind"
    },
    {
        "instruction": "Install React Query for data fetching",
        "command": "npm install @tanstack/react-query @tanstack/react-query-devtools",
        "explanation": "TanStack Query for server state management"
    },
    {
        "instruction": "Install Zustand for state management",
        "command": "npm install zustand",
        "explanation": "Lightweight state management alternative to Redux"
    },
    {
        "instruction": "Run React development server",
        "command": "npm run dev",
        "explanation": "Starts Vite/Next dev server with HMR"
    },
    {
        "instruction": "Run tests with Vitest",
        "command": "npm test -- --coverage",
        "explanation": "Runs tests with coverage report"
    },
    {
        "instruction": "Build for production",
        "command": "npm run build && npm run preview",
        "explanation": "Production build and preview locally"
    },
    {
        "instruction": "Analyze bundle size",
        "command": "npx vite-bundle-visualizer",
        "explanation": "Visualizes bundle composition"
    },
    {
        "instruction": "Add Storybook for component development",
        "command": "npx storybook@latest init",
        "explanation": "Initializes Storybook for isolated component dev"
    },
    {
        "instruction": "Type check without building",
        "command": "npx tsc --noEmit",
        "explanation": "Checks TypeScript types without compilation"
    },
    {
        "instruction": "Install Redux Toolkit",
        "command": "npm install @reduxjs/toolkit react-redux",
        "explanation": "Official recommended Redux setup"
    },
    {
        "instruction": "Install React Router",
        "command": "npm install react-router-dom",
        "explanation": "Client-side routing for React"
    },
    {
        "instruction": "Install Tailwind CSS with Vite",
        "command": "npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init -p",
        "explanation": "Sets up Tailwind CSS with PostCSS"
    },
    {
        "instruction": "Install testing libraries",
        "command": "npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest jsdom",
        "explanation": "Full testing setup with React Testing Library"
    },
    {
        "instruction": "Install React Hook Form",
        "command": "npm install react-hook-form @hookform/resolvers zod",
        "explanation": "Form handling with Zod validation"
    },
    {
        "instruction": "Install Framer Motion",
        "command": "npm install framer-motion",
        "explanation": "Animation library for React"
    },
    {
        "instruction": "Create React component",
        "command": "touch src/components/Button/Button.tsx src/components/Button/Button.test.tsx src/components/Button/index.ts",
        "explanation": "Creates component files with colocation"
    },
    {
        "instruction": "Run Storybook",
        "command": "npm run storybook",
        "explanation": "Starts Storybook dev server"
    },
    {
        "instruction": "Build Storybook static site",
        "command": "npm run build-storybook",
        "explanation": "Builds Storybook for deployment"
    },
    {
        "instruction": "Install shadcn/ui components",
        "command": "npx shadcn-ui@latest init && npx shadcn-ui@latest add button card dialog",
        "explanation": "Adds shadcn/ui component library"
    },
    {
        "instruction": "Install Radix UI primitives",
        "command": "npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tooltip",
        "explanation": "Headless UI primitives for accessibility"
    },
    {
        "instruction": "Lint and format code",
        "command": "npm run lint && npm run format",
        "explanation": "Runs ESLint and Prettier"
    },
    {
        "instruction": "Generate React component with Plop",
        "command": "npx plop component",
        "explanation": "Generates component from template"
    },
    {
        "instruction": "Update dependencies safely",
        "command": "npx npm-check-updates -u --target minor && npm install",
        "explanation": "Updates to latest minor versions"
    },
    {
        "instruction": "Check for React updates",
        "command": "npm outdated react react-dom @types/react @types/react-dom",
        "explanation": "Shows React version status"
    },
    {
        "instruction": "Install React Icons",
        "command": "npm install react-icons",
        "explanation": "Icon library with many icon sets"
    },
    {
        "instruction": "Install date library",
        "command": "npm install date-fns",
        "explanation": "Modern date utility library"
    },
    {
        "instruction": "Run E2E tests with Playwright",
        "command": "npx playwright test",
        "explanation": "Runs end-to-end tests"
    },
    {
        "instruction": "Install Playwright",
        "command": "npm init playwright@latest",
        "explanation": "Sets up Playwright E2E testing"
    },
    {
        "instruction": "Build Next.js production",
        "command": "npm run build && npm run start",
        "explanation": "Builds and starts Next.js in production mode"
    },
    {
        "instruction": "Export Next.js as static site",
        "command": "npm run build",
        "explanation": "With output: 'export' in next.config.js, generates static files"
    },
    {
        "instruction": "Install MSW for API mocking",
        "command": "npm install -D msw@latest && npx msw init public/",
        "explanation": "Mock Service Worker for API mocking in tests"
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "instruction": "Create React component with TypeScript and hooks",
        "language": "tsx",
        "code": """import { useState, useCallback, useMemo, useEffect } from 'react';

interface User {
  id: number;
  name: string;
  email: string;
}

interface UserListProps {
  initialUsers?: User[];
  onUserSelect?: (user: User) => void;
}

export function UserList({ initialUsers = [], onUserSelect }: UserListProps) {
  const [users, setUsers] = useState<User[]>(initialUsers);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Memoized filtered list
  const filteredUsers = useMemo(() => {
    const term = search.toLowerCase();
    return users.filter(user =>
      user.name.toLowerCase().includes(term) ||
      user.email.toLowerCase().includes(term)
    );
  }, [users, search]);

  // Stable callback reference
  const handleSelect = useCallback((user: User) => {
    onUserSelect?.(user);
  }, [onUserSelect]);

  // Fetch users on mount
  useEffect(() => {
    const controller = new AbortController();
    
    async function fetchUsers() {
      setLoading(true);
      setError(null);
      
      try {
        const res = await fetch('/api/users', { signal: controller.signal });
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        setUsers(data);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    }

    fetchUsers();
    
    return () => controller.abort();
  }, []);

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="user-list">
      <input
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search users..."
        aria-label="Search users"
      />
      
      {filteredUsers.length === 0 ? (
        <p>No users found</p>
      ) : (
        <ul role="list">
          {filteredUsers.map((user) => (
            <li key={user.id}>
              <button onClick={() => handleSelect(user)}>
                {user.name} - {user.email}
              </button>
            </li>
          ))}
        </ul>
      )}
      
      <p>Showing {filteredUsers.length} of {users.length} users</p>
    </div>
  );
}""",
        "explanation": "Component with TypeScript, all common hooks, abort controller cleanup"
    },
    {
        "instruction": "Create custom hook for data fetching",
        "language": "tsx",
        "code": """import { useState, useEffect, useCallback } from 'react';

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

interface UseFetchOptions {
  enabled?: boolean;
  refetchInterval?: number;
}

export function useFetch<T>(
  url: string,
  options: UseFetchOptions = {}
): UseFetchResult<T> {
  const { enabled = true, refetchInterval } = options;
  
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!enabled) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const json = await response.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [url, enabled]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Polling if refetchInterval set
  useEffect(() => {
    if (!refetchInterval || !enabled) return;
    
    const interval = setInterval(fetchData, refetchInterval);
    return () => clearInterval(interval);
  }, [fetchData, refetchInterval, enabled]);

  return { data, loading, error, refetch: fetchData };
}

// Usage
function UserProfile({ userId }: { userId: string }) {
  const { data: user, loading, error, refetch } = useFetch<User>(
    `/api/users/${userId}`,
    { enabled: !!userId }
  );

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!user) return null;

  return (
    <div>
      <h1>{user.name}</h1>
      <button onClick={refetch}>Refresh</button>
    </div>
  );
}""",
        "explanation": "Reusable custom hook with TypeScript generics, options, cleanup"
    },
    {
        "instruction": "Implement Zustand store with TypeScript",
        "language": "tsx",
        "code": """import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  
  // Actions
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      immer((set, get) => ({
        user: null,
        token: null,
        isAuthenticated: false,

        login: (user, token) => {
          set((state) => {
            state.user = user;
            state.token = token;
            state.isAuthenticated = true;
          });
        },

        logout: () => {
          set((state) => {
            state.user = null;
            state.token = null;
            state.isAuthenticated = false;
          });
        },

        updateUser: (updates) => {
          set((state) => {
            if (state.user) {
              Object.assign(state.user, updates);
            }
          });
        },
      })),
      {
        name: 'auth-storage',
        partialize: (state) => ({ token: state.token }), // Only persist token
      }
    ),
    { name: 'AuthStore' }
  )
);

// Selectors for optimized renders
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);

// Usage in component
function NavBar() {
  const user = useUser();
  const logout = useAuthStore((state) => state.logout);
  
  if (!user) return <LoginButton />;
  
  return (
    <nav>
      <span>Welcome, {user.name}</span>
      <button onClick={logout}>Logout</button>
    </nav>
  );
}""",
        "explanation": "Zustand with TypeScript, devtools, persistence, immer for immutable updates"
    },
    {
        "instruction": "Create React Query data fetching setup",
        "language": "tsx",
        "code": """import { 
  useQuery, 
  useMutation, 
  useQueryClient,
  QueryClient,
  QueryClientProvider
} from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// API functions
const api = {
  getUsers: async (): Promise<User[]> => {
    const res = await fetch('/api/users');
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
  },
  
  getUser: async (id: string): Promise<User> => {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) throw new Error('User not found');
    return res.json();
  },
  
  createUser: async (data: CreateUserDTO): Promise<User> => {
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create user');
    return res.json();
  },
};

// Custom hooks wrapping React Query
export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: api.getUsers,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useUser(id: string) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: () => api.getUser(id),
    enabled: !!id, // Only fetch when id exists
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.createUser,
    onSuccess: (newUser) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['users'] });
      
      // Or optimistically update cache
      // queryClient.setQueryData(['users'], (old: User[]) => [...old, newUser]);
    },
    onError: (error) => {
      console.error('Create user failed:', error);
    },
  });
}

// Provider setup
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

// Usage in component
function UserList() {
  const { data: users, isLoading, error } = useUsers();
  const createUser = useCreateUser();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <>
      <ul>
        {users?.map(user => <li key={user.id}>{user.name}</li>)}
      </ul>
      <button 
        onClick={() => createUser.mutate({ name: 'New User', email: 'new@example.com' })}
        disabled={createUser.isPending}
      >
        {createUser.isPending ? 'Creating...' : 'Add User'}
      </button>
    </>
  );
}""",
        "explanation": "React Query setup with custom hooks, mutations, cache invalidation"
    },
    {
        "instruction": "Create Next.js Server Component with data fetching",
        "language": "tsx",
        "code": """// app/users/page.tsx - Server Component (default in App Router)
import { Suspense } from 'react';
import { UserList } from './user-list';
import { UserListSkeleton } from './skeleton';

// This is an async Server Component
export default async function UsersPage() {
  return (
    <div className="container">
      <h1>Users</h1>
      <Suspense fallback={<UserListSkeleton />}>
        <UserList />
      </Suspense>
    </div>
  );
}

// app/users/user-list.tsx - Server Component fetching data
async function getUsers() {
  const res = await fetch('https://api.example.com/users', {
    next: { revalidate: 60 }, // ISR: revalidate every 60 seconds
  });
  
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json() as Promise<User[]>;
}

export async function UserList() {
  const users = await getUsers();
  
  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>
          <a href={`/users/${user.id}`}>{user.name}</a>
        </li>
      ))}
    </ul>
  );
}

// app/users/[id]/page.tsx - Dynamic route with params
interface PageProps {
  params: { id: string };
}

export default async function UserPage({ params }: PageProps) {
  const user = await getUser(params.id);
  
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
      <UserActions userId={user.id} /> {/* Client Component */}
    </div>
  );
}

// Generate static params for static generation
export async function generateStaticParams() {
  const users = await getUsers();
  return users.map((user) => ({ id: user.id.toString() }));
}

// app/users/[id]/user-actions.tsx - Client Component for interactivity
'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function UserActions({ userId }: { userId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleDelete() {
    setLoading(true);
    await fetch(`/api/users/${userId}`, { method: 'DELETE' });
    router.push('/users');
    router.refresh(); // Revalidate server data
  }

  return (
    <button onClick={handleDelete} disabled={loading}>
      {loading ? 'Deleting...' : 'Delete User'}
    </button>
  );
}""",
        "explanation": "Next.js 14 App Router with Server/Client Components, ISR, dynamic routes"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up React project with best practices",
        "steps": [
            "Create project: npm create vite@latest -- --template react-ts",
            "Install dev dependencies: eslint, prettier, husky, lint-staged",
            "Configure ESLint with react-hooks and typescript rules",
            "Set up Prettier with .prettierrc",
            "Configure path aliases in tsconfig and vite.config",
            "Set up folder structure: components/, hooks/, services/, types/",
            "Install testing: vitest, @testing-library/react, msw",
            "Configure vitest.config.ts with jsdom environment",
            "Set up MSW for API mocking in tests",
            "Add Tailwind CSS or CSS-in-JS solution",
            "Set up Storybook for component development",
            "Configure GitHub Actions for CI",
            "Add pre-commit hooks with husky",
            "Create README with setup instructions"
        ]
    },
    {
        "instruction": "Implement authentication in React application",
        "steps": [
            "Choose auth strategy (JWT, session, OAuth)",
            "Create AuthContext and AuthProvider",
            "Implement useAuth hook exposing state and actions",
            "Create login/register forms with validation",
            "Set up protected route wrapper component",
            "Implement token storage (memory for access, httpOnly cookie for refresh)",
            "Create API client with auth interceptor",
            "Handle token refresh flow automatically",
            "Add loading state during auth check",
            "Implement logout clearing all state",
            "Handle 401 responses globally",
            "Add role-based access control",
            "Test auth flow with MSW mocks",
            "Secure against XSS and CSRF"
        ]
    },
    {
        "instruction": "Optimize React application performance",
        "steps": [
            "Audit with React DevTools Profiler",
            "Add React.memo() to expensive pure components",
            "Use useMemo for expensive computations",
            "Use useCallback for callback props",
            "Implement virtualization for long lists (react-window)",
            "Code split with lazy() and Suspense",
            "Optimize images with next/image or similar",
            "Implement skeleton loading states",
            "Use React Query for server state caching",
            "Debounce/throttle expensive operations",
            "Avoid creating objects/arrays in render",
            "Profile bundle with webpack-bundle-analyzer",
            "Enable production build optimizations",
            "Monitor Core Web Vitals in production"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What are the rules of React hooks?",
        "answer": "Two rules: 1) Only call hooks at top level - not in loops, conditions, or nested functions. Ensures same order every render. 2) Only call hooks from React functions - function components or custom hooks, not regular JS functions. Why: React tracks hooks by call order. Breaking rules causes bugs. ESLint plugin eslint-plugin-react-hooks enforces automatically. Custom hooks must start with 'use' prefix."
    },
    {
        "question": "When should I use useState vs useReducer?",
        "answer": "useState: simple state, primitive values, independent updates. useReducer: complex state logic, multiple related values, state transitions depend on previous state. useReducer benefits: centralized logic, easier testing, better for complex updates. Pattern: if you have multiple setStates that always update together, consider useReducer. For very complex state: consider external state manager (Zustand, Redux)."
    },
    {
        "question": "What is the difference between useMemo and useCallback?",
        "answer": "useMemo: memoizes computed value, returns cached result. useCallback: memoizes function reference, returns cached function. useCallback(fn, deps) = useMemo(() => fn, deps). Use useMemo for expensive calculations. Use useCallback for stable callback references (passing to memoized children, dependencies of other hooks). Both help prevent unnecessary re-renders but add overhead - don't over-optimize. Profile first."
    },
    {
        "question": "How does React's reconciliation work?",
        "answer": "React compares virtual DOM trees to determine minimal DOM updates. Key algorithm: different element types → rebuild tree, same type → update attributes, recurse children. Keys help React track list items - use stable, unique IDs, not array indices. Without keys, React can't efficiently reorder. React 18 concurrent rendering can interrupt/prioritize updates. Understanding reconciliation helps write performant components."
    },
    {
        "question": "What is the useEffect hook for?",
        "answer": "useEffect runs side effects after render: data fetching, subscriptions, DOM manipulation. Syntax: useEffect(() => { effect(); return cleanup; }, [deps]). Empty deps [] = mount only. No deps = every render. With deps = when deps change. Cleanup runs before next effect and on unmount. Common uses: fetch data, set up listeners, sync with external systems. In Strict Mode, effects run twice in dev to catch bugs."
    },
    {
        "question": "What are controlled vs uncontrolled components?",
        "answer": "Controlled: React state is source of truth. value={state} + onChange={setState}. Full control, can validate/transform. Uncontrolled: DOM is source of truth. Use refs to read values: ref={inputRef}. Less code, useful for simple forms. Default values via defaultValue. Recommendation: prefer controlled for complex forms with validation. Use uncontrolled for simple forms or integrating non-React code."
    },
    {
        "question": "What is React Context and when to use it?",
        "answer": "Context provides data to component tree without prop drilling. Create: createContext(default). Provide: <Context.Provider value={...}>. Consume: useContext(Context). Good for: theme, auth, i18n, user preferences. Bad for: frequently changing data (causes re-renders). All consumers re-render when context changes. For frequent updates: split contexts, use memoization, or consider state library."
    },
    {
        "question": "What is the key prop in React?",
        "answer": "key helps React identify which items changed in lists. Must be unique among siblings, stable across renders. Use data IDs, not array indices (indices break on reorder/insert). Without keys: potential bugs, lost state, poor performance. React uses keys for reconciliation - same key means same component instance. Keys on fragments: <Fragment key={id}>. Never generate keys randomly during render."
    },
    {
        "question": "How do I handle forms in React?",
        "answer": "Options: controlled inputs, React Hook Form, Formik. Controlled: state per field, onChange handlers. React Hook Form: register inputs, less re-renders, great validation. Formik: similar, more features, heavier. For simple forms: controlled is fine. For complex forms: React Hook Form with Zod/Yup validation. Handle submission with onSubmit, prevent default, validate, then submit."
    },
    {
        "question": "What is React.memo?",
        "answer": "React.memo is a higher-order component that memoizes functional components. Prevents re-render if props haven't changed. Shallow comparison by default - for deep comparison pass compare function. Use when: component renders often with same props, renders are expensive. Don't use: cheap components, props change frequently. memo + useCallback for callback props. Profile before optimizing."
    },
    {
        "question": "What is JSX?",
        "answer": "JSX is syntax extension for JavaScript that looks like HTML. Compiled to React.createElement() calls. Not a template - full JavaScript power. Differences from HTML: className not class, camelCase attributes, self-closing tags required, expressions in {braces}. Can embed any JavaScript expression. Returns single root element (or Fragment). JSX prevents XSS - values are escaped by default."
    },
    {
        "question": "What are fragments in React?",
        "answer": "Fragments let you return multiple elements without wrapper div. Syntax: <Fragment> or shorthand <>. With keys: <Fragment key={id}> (can't use shorthand). Why: avoids extra DOM nodes, preserves semantics (lists, tables). Common in: list items returning multiple elements, table rows. Shorthand <></> is cleaner but can't have attributes."
    },
    {
        "question": "What is prop drilling and how to avoid it?",
        "answer": "Prop drilling: passing props through many layers just to reach deeply nested component. Problems: verbose, tight coupling, hard to refactor. Solutions: React Context for truly global data, component composition (render props, children), state management libraries for complex cases. Before Context: try restructuring - lift state, colocate state, compose components differently."
    },
    {
        "question": "What is the children prop?",
        "answer": "children is a special prop containing elements between opening/closing tags. <Card>{content}</Card> - content is props.children. Use for: composition, wrapper components, layout components. Can be: elements, strings, numbers, arrays, functions (render props). Type in TS: React.ReactNode (accepts anything renderable) or specific type. Children enables flexible, reusable component APIs."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "What are React Server Components?",
        "answer": "Server Components render on server, send HTML + serialized data (not JS bundle) to client. Benefits: smaller bundles, direct database/API access, better SEO. Can't: use hooks, browser APIs, event handlers. Use 'use client' directive for Client Components. Pattern: Server Component fetches data, passes to Client Component for interactivity. In Next.js App Router: components are Server by default. Mental model: Server for data, Client for interaction."
    },
    {
        "question": "How do I handle state management in large React apps?",
        "answer": "Layers: local state (useState), shared UI state (Context/Zustand), server state (React Query/SWR). Avoid putting server data in Redux. React Query handles caching, refetching, loading states. For complex client state: Zustand (simple), Redux Toolkit (large teams, time-travel), Jotai (atomic). Context for: theme, auth, localization - not frequently changing data. Key: right tool for each type of state."
    },
    {
        "question": "What is Suspense and how does it work?",
        "answer": "Suspense lets components wait for something before rendering, showing fallback. Used with: React.lazy() for code splitting, data fetching in Server Components, future: data fetching in Client Components. When child throws promise, Suspense catches and shows fallback until promise resolves. Streaming with Suspense: send HTML progressively. Error boundaries catch errors, Suspense catches loading. Combine for complete loading/error handling."
    },
    {
        "question": "What are the best testing practices for React?",
        "answer": "Testing Library philosophy: test behavior, not implementation. Queries: getByRole (preferred), getByText, getByTestId (last resort). User-event over fireEvent. Test: user interactions, async operations, error states. Mock: API calls (MSW), external services. Don't test: implementation details, library internals. Structure: Arrange-Act-Assert. Integration tests more valuable than unit tests for components. Snapshot tests: use sparingly, for stable UI."
    },
    {
        "question": "What is React Query and when should I use it?",
        "answer": "React Query (TanStack Query) is a server state management library. Features: caching, background refetching, stale-while-revalidate, pagination, infinite scroll, optimistic updates. Use for: API data, any async state. Benefits over useEffect+useState: automatic caching, deduplication, refetch on focus/reconnect. Query keys for cache identity. Mutations for write operations. DevTools for debugging. Use for any data from server."
    },
    {
        "question": "How does error boundary work in React?",
        "answer": "Error boundaries are class components that catch JavaScript errors in child component tree. Use componentDidCatch(error, errorInfo) for logging and getDerivedStateFromError for fallback UI. Cannot catch: event handlers (use try/catch), async code, server-side rendering, errors in boundary itself. Wrap different app sections in separate boundaries. With React Query: combine with error boundaries for comprehensive error handling. React 18: no hooks equivalent yet."
    },
    {
        "question": "What are render props and when to use them?",
        "answer": "Render props: passing function as children or prop that receives data and returns JSX. Pattern: <DataFetcher>{(data) => <Display data={data} />}</DataFetcher>. Use for: sharing stateful logic between components. Largely replaced by hooks in modern React, but still useful for: existing libraries, some composition patterns. Compare: HOCs wrap, render props inject, hooks compose. Hooks are preferred in new code."
    },
    {
        "question": "How do I optimize React performance?",
        "answer": "Measure first with React DevTools Profiler. Common optimizations: React.memo for pure components, useMemo for expensive computations, useCallback for stable callbacks, virtualization for long lists (react-window), code splitting with lazy/Suspense, avoid inline objects/functions in JSX, proper key usage. Don't optimize prematurely - profile first. Most apps don't need heavy optimization with modern React."
    },
    {
        "question": "What is Next.js App Router vs Pages Router?",
        "answer": "Pages Router: file-based routing in /pages, SSR with getServerSideProps, SSG with getStaticProps. App Router: file-based in /app, React Server Components by default, async components for data, layouts/loading/error files. App Router is newer, uses latest React features. Migration: can use both simultaneously. App Router: more flexible, better streaming, but different mental model. New projects: prefer App Router."
    },
    {
        "question": "How does useRef work and when to use it?",
        "answer": "useRef returns mutable object {current: value} persisting across renders. Use for: DOM references, storing mutable values without triggering re-render, storing previous values, instance variables in functional components. For DOM: <input ref={ref} /> then ref.current is the element. Mutations don't cause re-render. Common pattern: track previous value with useEffect updating ref. Don't overuse - prefer state when UI should update."
    },
    {
        "question": "What is Concurrent React?",
        "answer": "Concurrent rendering in React 18 enables interruptible rendering. Features: useTransition for non-urgent updates, useDeferredValue for deferred values, Suspense for streaming SSR, automatic batching. Benefits: responsive UI during heavy updates, progressive loading. startTransition wraps low-priority updates. Example: search input (urgent) vs results list (can defer). Opt-in via createRoot. Enables Suspense for data fetching."
    },
    {
        "question": "How do I handle authentication in React?",
        "answer": "Pattern: AuthContext + useAuth hook. Store: access token in memory (not localStorage - XSS risk), refresh token in httpOnly cookie. Flow: check auth on app load, redirect if needed, attach token to API calls, handle refresh automatically, clear on logout. Protected routes: wrapper component checking auth. With Next.js: middleware for server-side protection. Libraries: next-auth, clerk, auth0. Never trust client-side only auth."
    },
    {
        "question": "What are compound components in React?",
        "answer": "Compound components are related components that work together sharing implicit state. Pattern: <Menu><Menu.Item>A</Menu.Item><Menu.Item>B</Menu.Item></Menu>. Parent provides context, children consume. Examples: Radix UI, Headless UI. Benefits: flexible API, customizable structure, proper semantics. Implementation: Context for shared state, cloneElement or Context.Provider. Alternative to prop drilling in component libraries."
    },
    {
        "question": "How does SSR differ from SSG in Next.js?",
        "answer": "SSR (Server-Side Rendering): renders on every request, always fresh, slower TTFB. Use getServerSideProps in Pages Router, async Server Components in App Router. SSG (Static Site Generation): renders at build time, fastest, served from CDN. Use getStaticProps + getStaticPaths. ISR (Incremental): SSG with revalidation - best of both. App Router: fetch with {revalidate: N} for ISR. Choose based on: data freshness needs, performance requirements, build time constraints."
    },
    # === EXPANDED ADVANCED CONCEPTS ===
    {
        "question": "What is useImperativeHandle and when should I use it?",
        "answer": "useImperativeHandle customizes the instance value exposed to parent when using ref. Used with forwardRef to expose custom methods. Pattern: useImperativeHandle(ref, () => ({ focus: () => inputRef.current.focus() }), [dependencies]). Use sparingly - breaks encapsulation. Good for: exposing imperative methods like focus(), scrollTo(), play(). Prefer declarative patterns when possible. Required for some library integrations."
    },
    {
        "question": "How do I implement infinite scroll in React?",
        "answer": "Two approaches: 1) Intersection Observer: observe sentinel element at bottom, load more when visible. 2) React Query useInfiniteQuery: built-in pagination, getNextPageParam, hasNextPage. Libraries: react-virtualized for large lists. Pattern: keep rendered items limited with virtualization for performance. Implement: IntersectionObserver callback triggers fetchNextPage. Don't forget loading states and error handling. Consider UX - show loading indicator, handle end of data."
    },
    {
        "question": "What is code splitting and how to implement it?",
        "answer": "Code splitting divides bundle into smaller chunks loaded on demand. React.lazy() + Suspense: const Component = lazy(() => import('./Component')). Route-based splitting in Next.js/React Router is automatic. Component-level: wrap heavy components. Dynamic imports for conditional features. Benefits: faster initial load, load only what's needed. Preload hints: /* webpackPrefetch: true */. Analyze with webpack-bundle-analyzer. Don't over-split - has overhead."
    },
    {
        "question": "How does React handle events differently from DOM events?",
        "answer": "React uses SyntheticEvents wrapping native events for cross-browser consistency. Differences: camelCase naming (onClick not onclick), pass function not string, return false doesn't prevent default (use e.preventDefault()). Event pooling removed in React 17. Event delegation: React attaches handlers at root, not individual elements. For native events: use useEffect with addEventListener. Capture phase: onClickCapture. Passive events for scroll performance."
    },
    {
        "question": "What are optimistic updates and how to implement them?",
        "answer": "Optimistic updates show success state before server confirms, then rollback on error. React Query: useMutation with onMutate (update cache), onError (rollback), onSettled (refetch). Manual pattern: save previous state, update optimistically, revert on catch. Benefits: snappy UX, perceived performance. Risks: must handle rollback gracefully. Good for: likes, toggles, quick actions. Bad for: complex operations, critical data. Always show error state on failure."
    },
    {
        "question": "What is the useSyncExternalStore hook?",
        "answer": "useSyncExternalStore is for subscribing to external stores (Redux, Zustand, browser APIs). Guarantees tearing-free reads in concurrent mode. Parameters: subscribe function, getSnapshot function, optional getServerSnapshot. Used internally by Redux, Zustand. For custom stores: implement subscribe that returns unsubscribe, getSnapshot that returns immutable state. Replaces useSubscription. Required for external state in concurrent React."
    },
    {
        "question": "How do I handle internationalization (i18n) in React?",
        "answer": "Libraries: react-intl, react-i18next, next-intl (for Next.js). Pattern: Provider wraps app, useTranslation hook in components. Store translations in JSON files per locale. Features: pluralization, date/number formatting, interpolation. Next.js has built-in i18n routing. Consider: loading translations, SSR/SSG compatibility, type safety. react-i18next with TypeScript: generate types from translations. ICU message format for complex pluralization."
    },
    {
        "question": "What is React's Strict Mode?",
        "answer": "StrictMode is a development tool that highlights potential problems. Double-invokes: functions passed to useState, useReducer, useMemo, constructor, render, getDerivedStateFromProps. Also runs effects twice to find cleanup bugs. In React 18: may unmount/remount components. Only runs in development. Wrap root component: <StrictMode><App/></StrictMode>. Catches: side effects in render, deprecated APIs, missing cleanup. Keep it on - reveals bugs early."
    },
    {
        "question": "How do I implement drag and drop in React?",
        "answer": "Libraries: @dnd-kit (modern, accessible), react-beautiful-dnd (Atlassian), react-dnd (flexible). Native: HTML5 drag events + useRef. @dnd-kit: DndContext provider, useSortable/useDraggable hooks, keyboard accessible. Considerations: touch support, accessibility, performance with many items. Pattern: DndContext > SortableContext > draggable items. Handle reordering in onDragEnd callback. Virtual lists for large sets."
    },
    {
        "question": "What are portals in React?",
        "answer": "createPortal renders children into DOM node outside parent hierarchy. Use: ReactDOM.createPortal(children, domNode). Common for: modals, tooltips, toasts - elements that need to break out of overflow:hidden. Events still bubble through React tree (not DOM tree). Create target element in document body or designated container. Cleanup: remove portal content on unmount. Combine with Suspense/Error boundaries that wrap portal content."
    },
    {
        "question": "How do I debounce/throttle in React?",
        "answer": "Debounce: delay execution until pause in calls (search input). Throttle: limit execution rate (scroll handlers). With hooks: useCallback + lodash debounce, BUT wrap in useRef to persist. Better: use-debounce package. Pattern: const debouncedSearch = useDebouncedCallback((val) => search(val), 300). useDeferredValue is React's built-in for deferring expensive updates. Don't create new debounced function each render - memoize."
    },
    {
        "question": "What is React's useId hook?",
        "answer": "useId generates unique IDs stable across server and client renders. Introduced in React 18 for SSR hydration safety. Use: const id = useId(); <label htmlFor={id}>. Don't use for keys - not meant for lists. Each call generates different ID. Prefix format: :R1:, :R2:, etc. Perfect for: form labels, aria-describedby, any element needing unique ID. Replaces UUID generation that caused hydration mismatches."
    },
    {
        "question": "How do I handle file uploads in React?",
        "answer": "Pattern: <input type='file' onChange={handleFile} /> access files via e.target.files. FormData for multipart upload: formData.append('file', file). Show preview: URL.createObjectURL(file). Progress: XMLHttpRequest with onprogress or fetch with ReadableStream. Drag-drop: react-dropzone library. Validation: check file.type, file.size before upload. Chunked upload for large files. Clean up object URLs to prevent memory leaks."
    },
    {
        "question": "What is the use() hook in React 19?",
        "answer": "use() is a new hook that unwraps promises and context. For promises: const data = use(promise) - works inside conditionals unlike other hooks. For context: use(MyContext) alternative to useContext. Throws on pending/error (needs Suspense/ErrorBoundary). Enables reading data in render without useEffect. Works with async Server Components. Can be called conditionally. Simplifies data fetching patterns. Currently in React 19 canary."
    },
]

# =============================================================================
# ERROR SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "Too many re-renders. React limits the number of renders",
        "error_type": "infinite_loop",
        "response": {
            "status": "critical_bug",
            "cause": "State update triggers render which triggers state update",
            "common_mistakes": [
                "Calling setState in render: onClick={setCount(count+1)} instead of onClick={() => setCount(count+1)}",
                "useEffect without proper dependencies",
                "Object/array in dependency array (creates new reference each render)"
            ],
            "solutions": [
                "Wrap in callback: onClick={() => handler()}",
                "Check useEffect dependencies",
                "Use useMemo/useCallback for object/function dependencies",
                "Use functional update: setCount(c => c+1)"
            ]
        }
    },
    {
        "instruction": "Cannot read property of undefined in useEffect",
        "error_type": "async_timing",
        "response": {
            "status": "common_issue",
            "cause": "Data not loaded yet when effect runs or component unmounts before async completes",
            "solutions": [
                "Check if data exists before accessing: data?.property",
                "Add loading state and guard rendering",
                "Use abort controller for cleanup",
                "Check mounted state before setState"
            ],
            "pattern": "useEffect(() => { let mounted = true; fetch().then(d => { if(mounted) setData(d) }); return () => { mounted = false } }, [])"
        }
    },
    {
        "instruction": "Objects are not valid as a React child",
        "error_type": "render_error",
        "response": {
            "status": "fixable",
            "cause": "Trying to render object/array directly in JSX",
            "examples": [
                "Rendering Date object: use date.toLocaleDateString()",
                "Rendering object: use JSON.stringify() or access properties",
                "Rendering array of objects: use .map() to render each"
            ],
            "solution": "Convert to string or map to valid JSX elements"
        }
    },
    {
        "instruction": "Can't perform a React state update on an unmounted component",
        "error_type": "memory_leak",
        "response": {
            "status": "warning",
            "cause": "Async operation completes after component unmounted",
            "solutions": [
                "Use AbortController for fetch requests",
                "Track mounted state in useEffect cleanup",
                "Use React Query/SWR which handles this automatically",
                "Cancel subscriptions in cleanup function"
            ],
            "pattern": "const controller = new AbortController(); fetch(url, { signal: controller.signal }); return () => controller.abort();"
        }
    },
    {
        "instruction": "Each child in a list should have a unique key prop",
        "error_type": "key_warning",
        "response": {
            "status": "performance_issue",
            "cause": "React needs keys to efficiently update lists",
            "solutions": [
                "Add key prop with unique, stable ID: key={item.id}",
                "Never use array index as key (breaks on reorder)",
                "Generate unique IDs if data lacks them",
                "Keys must be unique among siblings only"
            ],
            "anti_pattern": "key={Math.random()} - creates new key every render, defeats purpose"
        }
    },
    {
        "instruction": "Maximum update depth exceeded",
        "error_type": "infinite_loop",
        "response": {
            "status": "critical_bug",
            "cause": "Infinite loop of state updates, often in useEffect",
            "common_causes": [
                "useEffect updates state that triggers itself",
                "Missing dependency causing constant re-run",
                "Object comparison always failing (new reference)"
            ],
            "solutions": [
                "Check useEffect dependencies carefully",
                "Use functional updates for derived state",
                "Memoize objects/arrays in dependencies",
                "Consider if effect is necessary"
            ]
        }
    },
    {
        "instruction": "Invalid hook call. Hooks can only be called inside function component",
        "error_type": "hook_rules_violation",
        "response": {
            "status": "code_error",
            "common_causes": [
                "Calling hook from regular function (not component)",
                "Calling hook conditionally or in loop",
                "Multiple React versions in bundle",
                "Mismatched react and react-dom versions"
            ],
            "solutions": [
                "Move hook call to component top level",
                "Create custom hook if sharing logic",
                "Check for duplicate React installations: npm ls react",
                "Ensure consistent React versions across packages"
            ]
        }
    },
    {
        "instruction": "Cannot find module or its type declarations",
        "error_type": "import_error",
        "response": {
            "status": "fixable",
            "common_causes": [
                "Package not installed",
                "Missing @types package",
                "Incorrect import path",
                "TypeScript path alias not configured"
            ],
            "solutions": [
                "Install package: npm install package-name",
                "Install types: npm install -D @types/package-name",
                "Check import path matches file location",
                "Configure paths in tsconfig.json"
            ]
        }
    },
    {
        "instruction": "useEffect dependency array warning",
        "error_type": "eslint_warning",
        "response": {
            "status": "should_fix",
            "cause": "ESLint react-hooks/exhaustive-deps rule detecting missing dependencies",
            "solutions": [
                "Add missing dependencies to array",
                "Wrap functions in useCallback",
                "Move constant objects outside component",
                "If intentional: // eslint-disable-next-line (document why)"
            ],
            "warning": "Don't disable without understanding - can cause stale closure bugs"
        }
    },
    {
        "instruction": "Hydration failed because server-rendered HTML didn't match client",
        "error_type": "hydration_error",
        "response": {
            "status": "ssr_issue",
            "cause": "Server and client rendered different content",
            "common_causes": [
                "Using window/document during SSR",
                "Date/time differences",
                "Random values generating different output",
                "Browser extension modifying DOM"
            ],
            "solutions": [
                "Use useEffect for client-only code",
                "Add suppressHydrationWarning for intentional differences",
                "Use dynamic import with ssr: false",
                "Ensure same data on server and client"
            ]
        }
    },
    {
        "instruction": "Module not found: Error: Can't resolve 'fs'",
        "error_type": "bundler_error",
        "response": {
            "status": "environment_issue",
            "cause": "Trying to use Node.js-only module in browser bundle",
            "solutions": [
                "Move code to server-side (API route, getServerSideProps)",
                "Add browser field in package.json to stub module",
                "Use dynamic import for server-only code",
                "In Next.js: webpack config with fallback: { fs: false }"
            ]
        }
    },
    {
        "instruction": "React component not updating when prop changes",
        "error_type": "rendering_issue",
        "response": {
            "status": "needs_investigation",
            "common_causes": [
                "Mutating state instead of creating new object",
                "Parent not re-rendering (memo blocking update)",
                "Object reference not changing",
                "Key prop causing component to persist incorrectly"
            ],
            "solutions": [
                "Always return new object/array: [...arr, newItem]",
                "Check memo/useMemo dependencies",
                "Use React DevTools to trace updates",
                "Verify state update is actually happening"
            ]
        }
    },
    {
        "instruction": "Text content does not match server-rendered HTML",
        "error_type": "hydration_error",
        "response": {
            "status": "ssr_mismatch",
            "cause": "Text differs between server and client render",
            "common_cases": [
                "Using new Date() or Date.now()",
                "Math.random() in render",
                "Locale-specific formatting",
                "useId() without suppressHydrationWarning"
            ],
            "solutions": [
                "Use consistent data source",
                "Move dynamic content to useEffect/useState",
                "Use suppressHydrationWarning attribute",
                "Pass timestamp from server as prop"
            ]
        }
    },
    {
        "instruction": "Rendered more hooks than during the previous render",
        "error_type": "hook_rules_violation",
        "response": {
            "status": "critical_bug",
            "cause": "Hook called conditionally - different number each render",
            "solutions": [
                "Move hooks before any conditional returns",
                "Don't call hooks inside if statements",
                "Don't call hooks inside loops",
                "Ensure all hooks run every render"
            ],
            "correct_pattern": "Call hooks at top, use their values conditionally"
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_command",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_code_response(language: str, code: str, explanation: str) -> str:
    return json.dumps({
        "action": "provide_code",
        "language": language,
        "code": code,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_command_response(task["command"], task["explanation"])
    } for task in REACT_CLI_TASKS]

def generate_code_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": ex["instruction"],
        "response": format_code_response(ex["language"], ex["code"], ex["explanation"])
    } for ex in CODE_EXAMPLES]

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    all_concepts = BASIC_CONCEPTS + ADVANCED_CONCEPTS
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in all_concepts]

def generate_error_examples() -> List[Dict]:
    examples = []
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    return examples

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating React Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} CLI examples")
    
    code_examples = generate_code_examples()
    all_examples.extend(code_examples)
    print(f"Generated {len(code_examples)} code examples")
    
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"Generated {len(planning_examples)} planning examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "react.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
