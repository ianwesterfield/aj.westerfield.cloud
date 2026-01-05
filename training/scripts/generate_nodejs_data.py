#!/usr/bin/env python3
"""
Node.js Development Training Data Generator
Target: ~200 examples for Node.js, Express, npm, backend JavaScript
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for Node.js development.
You help with Node.js, Express, npm/yarn, async patterns, and backend JavaScript."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

NODE_TASKS = [
    {
        "instruction": "Initialize new Node.js project",
        "command": "npm init -y && npm pkg set type=\"module\"",
        "explanation": "Creates package.json with ES modules enabled"
    },
    {
        "instruction": "Install production dependencies",
        "command": "npm install express dotenv cors helmet",
        "explanation": "Installs common API dependencies"
    },
    {
        "instruction": "Install development dependencies",
        "command": "npm install -D typescript @types/node @types/express tsx nodemon",
        "explanation": "Installs TypeScript tooling for Node.js"
    },
    {
        "instruction": "Run Node.js with watch mode",
        "command": "node --watch src/index.js",
        "explanation": "Built-in watch mode (Node 18+)"
    },
    {
        "instruction": "Run TypeScript directly with tsx",
        "command": "tsx watch src/index.ts",
        "explanation": "tsx provides fast TypeScript execution with watch"
    },
    {
        "instruction": "Check for outdated packages",
        "command": "npm outdated",
        "explanation": "Shows current, wanted, and latest versions"
    },
    {
        "instruction": "Update all dependencies",
        "command": "npm update && npm audit fix",
        "explanation": "Updates to latest within semver range and fixes vulnerabilities"
    },
    {
        "instruction": "Run npm scripts in parallel",
        "command": "npm-run-all --parallel lint test build",
        "explanation": "Runs multiple scripts concurrently"
    },
    {
        "instruction": "Debug Node.js application",
        "command": "node --inspect-brk src/index.js",
        "explanation": "Starts with debugger paused at first line"
    },
    {
        "instruction": "Profile Node.js performance",
        "command": "node --prof src/index.js && node --prof-process isolate-*.log > profile.txt",
        "explanation": "CPU profiling for performance analysis"
    },
    {
        "instruction": "Install package globally",
        "command": "npm install -g nodemon",
        "explanation": "Installs package available system-wide"
    },
    {
        "instruction": "Initialize TypeScript project",
        "command": "npx tsc --init",
        "explanation": "Creates tsconfig.json with default settings"
    },
    {
        "instruction": "Run specific npm script",
        "command": "npm run build",
        "explanation": "Executes script defined in package.json"
    },
    {
        "instruction": "Install exact package version",
        "command": "npm install express@4.18.2 --save-exact",
        "explanation": "Installs specific version without caret"
    },
    {
        "instruction": "Uninstall package",
        "command": "npm uninstall lodash",
        "explanation": "Removes package and updates package.json"
    },
    {
        "instruction": "List installed packages",
        "command": "npm list --depth=0",
        "explanation": "Shows top-level dependencies only"
    },
    {
        "instruction": "View package info",
        "command": "npm view express versions",
        "explanation": "Shows available versions of package"
    },
    {
        "instruction": "Check for security vulnerabilities",
        "command": "npm audit",
        "explanation": "Scans dependencies for known vulnerabilities"
    },
    {
        "instruction": "Fix security vulnerabilities automatically",
        "command": "npm audit fix --force",
        "explanation": "Attempts to fix vulnerabilities, may include breaking changes"
    },
    {
        "instruction": "Clean npm cache",
        "command": "npm cache clean --force",
        "explanation": "Clears npm's cache directory"
    },
    {
        "instruction": "Reinstall all packages",
        "command": "rm -rf node_modules package-lock.json && npm install",
        "explanation": "Fresh install of all dependencies"
    },
    {
        "instruction": "Link local package for development",
        "command": "npm link ../my-local-package",
        "explanation": "Creates symlink to local package"
    },
    {
        "instruction": "Run with environment variables",
        "command": "NODE_ENV=production node src/index.js",
        "explanation": "Sets environment variable for process"
    },
    {
        "instruction": "Run with increased memory limit",
        "command": "node --max-old-space-size=4096 src/index.js",
        "explanation": "Increases V8 heap memory to 4GB"
    },
    {
        "instruction": "Run tests with Jest",
        "command": "npx jest --coverage --watchAll=false",
        "explanation": "Runs Jest tests with coverage report"
    },
    {
        "instruction": "Run tests with Vitest",
        "command": "npx vitest run --coverage",
        "explanation": "Runs Vitest tests with coverage"
    },
    {
        "instruction": "Initialize Prisma ORM",
        "command": "npx prisma init",
        "explanation": "Sets up Prisma with schema file"
    },
    {
        "instruction": "Generate Prisma client",
        "command": "npx prisma generate",
        "explanation": "Generates type-safe database client"
    },
    {
        "instruction": "Run Prisma migrations",
        "command": "npx prisma migrate dev --name init",
        "explanation": "Creates and applies database migration"
    },
    {
        "instruction": "Open Prisma Studio",
        "command": "npx prisma studio",
        "explanation": "Opens database GUI in browser"
    },
    {
        "instruction": "Create package with pnpm",
        "command": "pnpm init && pnpm add express",
        "explanation": "Uses pnpm for faster, disk-efficient installs"
    },
    {
        "instruction": "Use yarn instead of npm",
        "command": "yarn init -y && yarn add express",
        "explanation": "Alternative package manager with caching"
    },
    {
        "instruction": "Check Node.js version",
        "command": "node --version",
        "explanation": "Shows installed Node.js version"
    },
    {
        "instruction": "Use specific Node version with nvm",
        "command": "nvm use 20 && nvm alias default 20",
        "explanation": "Switches to Node 20 and sets as default"
    },
    {
        "instruction": "Run REPL",
        "command": "node",
        "explanation": "Opens interactive Node.js shell"
    },
    {
        "instruction": "Execute inline code",
        "command": "node -e \"console.log(process.versions)\"",
        "explanation": "Runs JavaScript from command line"
    },
    {
        "instruction": "Print JSON from command",
        "command": "node -p \"JSON.stringify({a:1,b:2}, null, 2)\"",
        "explanation": "Evaluates and prints expression"
    },
    {
        "instruction": "Generate lockfile only",
        "command": "npm install --package-lock-only",
        "explanation": "Updates package-lock.json without installing"
    },
    {
        "instruction": "Install from package-lock.json",
        "command": "npm ci",
        "explanation": "Clean install from lockfile, faster for CI"
    },
    {
        "instruction": "Publish package to npm",
        "command": "npm publish --access public",
        "explanation": "Publishes package to npm registry"
    },
    {
        "instruction": "Login to npm",
        "command": "npm login",
        "explanation": "Authenticates with npm registry"
    },
    {
        "instruction": "Set npm registry",
        "command": "npm config set registry https://registry.npmjs.org/",
        "explanation": "Configures package registry URL"
    },
    {
        "instruction": "Run with experimental features",
        "command": "node --experimental-modules --experimental-json-modules src/index.js",
        "explanation": "Enables experimental Node.js features"
    },
    {
        "instruction": "Enable source maps for debugging",
        "command": "node --enable-source-maps src/index.js",
        "explanation": "Shows original TypeScript lines in errors"
    },
    {
        "instruction": "Benchmark with autocannon",
        "command": "npx autocannon -c 100 -d 30 http://localhost:3000/api",
        "explanation": "HTTP load testing tool"
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "instruction": "Create Express server with middleware",
        "language": "typescript",
        "code": """import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import 'dotenv/config';

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
  credentials: true
}));

// Body parsing
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path} ${res.statusCode} ${duration}ms`);
  });
  next();
});

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/api/users', async (req, res, next) => {
  try {
    const users = await getUsers();
    res.json({ data: users });
  } catch (error) {
    next(error);
  }
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error(err.stack);
  res.status(500).json({
    error: process.env.NODE_ENV === 'production' 
      ? 'Internal server error' 
      : err.message
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

async function getUsers() {
  // Database query here
  return [{ id: 1, name: 'Alice' }];
}""",
        "explanation": "Production-ready Express setup with security, logging, error handling"
    },
    {
        "instruction": "Implement async error handling wrapper",
        "language": "typescript",
        "code": """import { Request, Response, NextFunction, RequestHandler } from 'express';

// Async wrapper - catches async errors automatically
export const asyncHandler = (
  fn: (req: Request, res: Response, next: NextFunction) => Promise<any>
): RequestHandler => {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

// Custom error class with status code
export class AppError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public code?: string
  ) {
    super(message);
    this.name = 'AppError';
    Error.captureStackTrace(this, this.constructor);
  }

  static badRequest(message: string, code?: string) {
    return new AppError(400, message, code);
  }

  static unauthorized(message = 'Unauthorized') {
    return new AppError(401, message, 'UNAUTHORIZED');
  }

  static notFound(resource = 'Resource') {
    return new AppError(404, `${resource} not found`, 'NOT_FOUND');
  }
}

// Usage example
app.get('/api/users/:id', asyncHandler(async (req, res) => {
  const user = await findUser(req.params.id);
  if (!user) {
    throw AppError.notFound('User');
  }
  res.json({ data: user });
}));

// Enhanced error handler
app.use((err: Error | AppError, req: Request, res: Response, next: NextFunction) => {
  const statusCode = err instanceof AppError ? err.statusCode : 500;
  const code = err instanceof AppError ? err.code : 'INTERNAL_ERROR';
  
  console.error(`[${code}] ${err.message}`, err.stack);
  
  res.status(statusCode).json({
    error: {
      message: err.message,
      code,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    }
  });
});""",
        "explanation": "Async wrapper eliminates try/catch in routes, custom error class"
    },
    {
        "instruction": "Create connection pool and database utilities",
        "language": "typescript",
        "code": """import { Pool, PoolClient } from 'pg';

// Connection pool singleton
const pool = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20, // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.on('error', (err) => {
  console.error('Unexpected pool error', err);
});

// Query helper with proper typing
export async function query<T = any>(
  text: string,
  params?: any[]
): Promise<T[]> {
  const start = Date.now();
  const result = await pool.query(text, params);
  const duration = Date.now() - start;
  
  if (duration > 100) {
    console.warn(`Slow query (${duration}ms): ${text}`);
  }
  
  return result.rows;
}

// Transaction helper
export async function withTransaction<T>(
  callback: (client: PoolClient) => Promise<T>
): Promise<T> {
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

// Usage
const users = await query<User>('SELECT * FROM users WHERE active = $1', [true]);

const result = await withTransaction(async (client) => {
  await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [100, fromId]);
  await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [100, toId]);
  return { success: true };
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Closing pool...');
  await pool.end();
  process.exit(0);
});""",
        "explanation": "PostgreSQL pool with transactions, slow query logging, graceful shutdown"
    },
    {
        "instruction": "Implement rate limiting middleware",
        "language": "typescript",
        "code": """import { Request, Response, NextFunction } from 'express';
import { createClient } from 'redis';

const redis = createClient({ url: process.env.REDIS_URL });
redis.connect();

interface RateLimitOptions {
  windowMs: number;      // Time window in ms
  maxRequests: number;   // Max requests per window
  keyPrefix?: string;    // Redis key prefix
  keyGenerator?: (req: Request) => string;
}

export function rateLimit(options: RateLimitOptions) {
  const {
    windowMs,
    maxRequests,
    keyPrefix = 'ratelimit:',
    keyGenerator = (req) => req.ip || 'unknown'
  } = options;

  return async (req: Request, res: Response, next: NextFunction) => {
    const key = keyPrefix + keyGenerator(req);
    
    try {
      const multi = redis.multi();
      multi.incr(key);
      multi.pExpire(key, windowMs, 'NX'); // Only set if not exists
      const results = await multi.exec();
      
      const requestCount = results[0] as number;
      const remaining = Math.max(0, maxRequests - requestCount);
      
      // Set rate limit headers
      res.setHeader('X-RateLimit-Limit', maxRequests);
      res.setHeader('X-RateLimit-Remaining', remaining);
      res.setHeader('X-RateLimit-Reset', Date.now() + windowMs);
      
      if (requestCount > maxRequests) {
        res.status(429).json({
          error: 'Too many requests',
          retryAfter: Math.ceil(windowMs / 1000)
        });
        return;
      }
      
      next();
    } catch (error) {
      // Fail open - allow request if Redis is down
      console.error('Rate limit error:', error);
      next();
    }
  };
}

// Usage
app.use('/api/', rateLimit({
  windowMs: 60 * 1000,  // 1 minute
  maxRequests: 100,
}));

// Stricter limit for auth endpoints
app.use('/api/auth/', rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  maxRequests: 5,
  keyPrefix: 'ratelimit:auth:',
}));""",
        "explanation": "Redis-backed rate limiter with sliding window"
    },
    {
        "instruction": "Create background job queue with Bull",
        "language": "typescript",
        "code": """import Queue, { Job } from 'bull';

// Create queue
const emailQueue = new Queue<EmailJobData>('email', {
  redis: process.env.REDIS_URL,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000
    },
    removeOnComplete: 100,
    removeOnFail: 1000
  }
});

interface EmailJobData {
  to: string;
  subject: string;
  template: string;
  variables: Record<string, string>;
}

// Process jobs
emailQueue.process(async (job: Job<EmailJobData>) => {
  const { to, subject, template, variables } = job.data;
  
  job.progress(10);
  const html = await renderTemplate(template, variables);
  
  job.progress(50);
  await sendEmail({ to, subject, html });
  
  job.progress(100);
  return { sent: true, to };
});

// Event handlers
emailQueue.on('completed', (job, result) => {
  console.log(`Email job ${job.id} completed:`, result);
});

emailQueue.on('failed', (job, error) => {
  console.error(`Email job ${job?.id} failed:`, error.message);
  // Alert on repeated failures
  if (job && job.attemptsMade >= 3) {
    alertOps(`Email delivery failing: ${job.data.to}`);
  }
});

// Add job from route
app.post('/api/users', asyncHandler(async (req, res) => {
  const user = await createUser(req.body);
  
  // Queue welcome email
  await emailQueue.add({
    to: user.email,
    subject: 'Welcome!',
    template: 'welcome',
    variables: { name: user.name }
  }, {
    priority: 1,  // Higher priority
    delay: 1000   // Delay 1 second
  });
  
  res.status(201).json({ data: user });
}));

// Scheduled/recurring jobs
emailQueue.add(
  { to: 'reports@company.com', subject: 'Daily Report', template: 'daily-report', variables: {} },
  { repeat: { cron: '0 9 * * *' } }  // Every day at 9 AM
);

// Graceful shutdown
process.on('SIGTERM', async () => {
  await emailQueue.close();
  process.exit(0);
});""",
        "explanation": "Bull queue for background jobs with retries, scheduling, events"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up Node.js project with TypeScript and testing",
        "steps": [
            "npm init -y",
            "Install TypeScript: npm i -D typescript @types/node tsx",
            "Create tsconfig.json with strict mode",
            "Set up source directory structure: src/, tests/",
            "Install testing: npm i -D vitest @vitest/coverage-v8",
            "Configure vitest.config.ts",
            "Install linting: npm i -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin",
            "Create .eslintrc.cjs with recommended rules",
            "Install prettier: npm i -D prettier eslint-config-prettier",
            "Create .prettierrc",
            "Add npm scripts: dev, build, test, lint, format",
            "Set up husky + lint-staged for pre-commit hooks",
            "Create GitHub Actions CI workflow",
            "Add .gitignore, .env.example, README.md"
        ]
    },
    {
        "instruction": "Implement authentication system in Express",
        "steps": [
            "Install: bcrypt, jsonwebtoken, express-validator",
            "Create User model with hashed password storage",
            "Implement password hashing in user creation",
            "Create /auth/register endpoint with validation",
            "Create /auth/login endpoint returning JWT",
            "Implement JWT middleware for protected routes",
            "Create /auth/me endpoint for current user",
            "Add refresh token rotation flow",
            "Implement /auth/logout (token blacklist or DB)",
            "Add password reset flow with email",
            "Set up rate limiting on auth endpoints",
            "Add input validation with express-validator",
            "Write integration tests for auth flow",
            "Document API with examples"
        ]
    },
    {
        "instruction": "Deploy Node.js application to production",
        "steps": [
            "Audit dependencies: npm audit",
            "Ensure all secrets in environment variables",
            "Add NODE_ENV checks for production behavior",
            "Configure production logging (structured JSON)",
            "Create Dockerfile with multi-stage build",
            "Set up health check endpoint",
            "Configure graceful shutdown (SIGTERM handling)",
            "Set up PM2 or cluster mode for multi-core",
            "Configure reverse proxy (nginx) with SSL",
            "Set up rate limiting at nginx level",
            "Configure monitoring (Prometheus metrics)",
            "Set up error tracking (Sentry)",
            "Create deployment pipeline (GitHub Actions)",
            "Document deployment process and rollback"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is the event loop in Node.js?",
        "answer": "Event loop is Node's mechanism for non-blocking I/O. Single-threaded but handles thousands of concurrent operations. Phases: timers (setTimeout), pending callbacks, idle, poll (I/O), check (setImmediate), close callbacks. Async operations go to thread pool (libuv) or OS. When complete, callbacks queued. Don't block the loop with CPU-intensive work - use worker threads or child processes. process.nextTick() runs before next phase, setImmediate after current phase. Understanding the event loop is key to Node.js performance."
    },
    {
        "question": "What is the difference between CommonJS and ES Modules?",
        "answer": "CommonJS: require()/module.exports, synchronous, Node original. ES Modules: import/export, asynchronous, JavaScript standard. ESM benefits: static analysis, tree shaking, top-level await. Enable ESM: 'type': 'module' in package.json or .mjs extension. Can't require() in ESM, but can import() CJS. For new projects, prefer ESM. Migration: change requires to imports gradually. Some packages still CJS-only - use dynamic import(). Node 16+ has good ESM support."
    },
    {
        "question": "How do I handle environment variables in Node.js?",
        "answer": "Use dotenv for loading .env files: require('dotenv').config() or import 'dotenv/config'. Access via process.env.VAR_NAME. Never commit .env to git - use .env.example as template. Validate required vars at startup. For type safety: parse and validate (zod, env-schema). Different .env per environment: .env.development, .env.production. In production, set real env vars (not .env files). Use secrets manager for sensitive values. Consider convict or envalid for validation."
    },
    {
        "question": "What is npm vs yarn vs pnpm?",
        "answer": "npm: Node's default package manager, comes with Node. yarn: Facebook's alternative, faster historically, workspaces support. pnpm: Fastest, uses hard links to save disk space, strict about dependencies. All use package.json. Lock files: package-lock.json (npm), yarn.lock (yarn), pnpm-lock.yaml (pnpm). For most projects, any works. pnpm best for monorepos (saves disk). yarn/pnpm have better workspace support. Stick to one per project. Commands mostly similar: install, add, remove."
    },
    {
        "question": "What is Express.js middleware?",
        "answer": "Middleware are functions that run during request-response cycle: (req, res, next) => {}. Call next() to pass to next middleware. Order matters - runs top to bottom. Types: application-level (app.use), router-level (router.use), error-handling (4 params), built-in (express.json()), third-party (cors, helmet). Use for: logging, auth, parsing, validation, error handling. Error middleware catches errors: (err, req, res, next). Don't call next() = response ends there."
    },
    {
        "question": "How does require() caching work?",
        "answer": "Node.js caches modules after first require(). Same path returns same cached export. Benefits: singleton pattern works, better performance. Cache by resolved path - same file, different paths = different cache entries. Clear cache: delete require.cache[require.resolve('./module')]. Circular dependencies work because cache returns partial export. ESM also caches. This is why module-level state persists. For fresh imports in tests, mock or clear cache."
    },
    {
        "question": "What is package.json and how does it work?",
        "answer": "package.json defines project metadata, dependencies, scripts. Key fields: name, version, main (entry point), scripts (npm commands), dependencies (runtime), devDependencies (build/test only). Scripts: npm run scriptname, special: start, test, build. Versioning: ^1.2.3 (minor updates), ~1.2.3 (patch only), 1.2.3 (exact). peerDependencies for plugins. engines specifies Node version. exports for ESM entry points. bin for CLI tools. repository, license, author for publishing."
    },
    {
        "question": "What is the difference between dependencies and devDependencies?",
        "answer": "dependencies: needed to run application - installed in production. devDependencies: only for development - TypeScript, testing frameworks, build tools. npm install --production skips devDependencies. For libraries: dependencies included for users, devDependencies not. Common mistake: putting build tool outputs in dependencies. Type definitions (@types/*): usually devDependencies unless you export types. peerDependencies: for plugins requiring specific version of host."
    },
    {
        "question": "How do callbacks work in Node.js?",
        "answer": "Traditional async pattern: function(args, callback). Callback signature: (error, result) => {}. Error-first: always check if (error). Node core uses callbacks. Problems: callback hell (nesting), error handling scattered, hard to read. Modern alternatives: Promises (then/catch), async/await. util.promisify() converts callback functions to Promises. Most libraries now support Promises. For new code, prefer async/await. Understand callbacks for legacy code and some core APIs."
    },
    {
        "question": "What is process.nextTick vs setImmediate?",
        "answer": "Both schedule callbacks, different timing. process.nextTick: runs before continuing event loop, before any I/O. setImmediate: runs after I/O callbacks, in check phase. nextTick has higher priority. Recursive nextTick can starve I/O. Use setImmediate for yielding to event loop. Use nextTick for: ensuring callback runs after current operation but before I/O. Generally prefer setImmediate - safer for I/O. In practice, often doesn't matter for application code."
    },
    {
        "question": "How do I debug Node.js applications?",
        "answer": "Options: console.log (simple), debugger statement + node inspect (CLI), --inspect flag + Chrome DevTools (recommended). Launch: node --inspect app.js or --inspect-brk (break on first line). Chrome: chrome://inspect. VS Code: launch.json with attach/launch configs. Debugging features: breakpoints, step through, watch expressions, call stack. For production: use logging (winston, pino) + error tracking (Sentry). Remote debugging: --inspect=0.0.0.0:9229 (careful with security)."
    },
    {
        "question": "What is the Buffer class in Node.js?",
        "answer": "Buffer handles binary data in Node.js. JavaScript strings are UTF-16, Buffers are raw bytes. Create: Buffer.from('string'), Buffer.alloc(size). Use for: file I/O, network protocols, crypto, binary parsing. Convert: buf.toString('utf8'), buf.toJSON(). Compare: buf.compare(), buf.equals(). Slice: buf.subarray() (shared memory). Buffers are typed arrays (Uint8Array). Be careful: Buffer.allocUnsafe() faster but contains old data. Use Buffer.alloc() for sensitive data."
    },
    # === EXPANDED BASIC CONCEPTS ===
    {
        "question": "How do I read and write files in Node.js?",
        "answer": "fs module handles file operations. Sync methods: fs.readFileSync(), fs.writeFileSync() - block event loop. Async methods: fs.readFile(), fs.writeFile() with callbacks. Promise API: fs.promises.readFile(). Use async for production. Read: fs.readFile('file.txt', 'utf8'). Write: fs.writeFile('file.txt', data). Append: fs.appendFile(). Check existence: fs.existsSync() or fs.access(). For large files, use streams: fs.createReadStream(). Always handle errors. Use path.join() for cross-platform paths."
    },
    {
        "question": "What is the path module in Node.js?",
        "answer": "path module handles file path operations cross-platform. path.join(): joins segments with correct separator. path.resolve(): creates absolute path. path.dirname(): directory portion. path.basename(): filename portion. path.extname(): file extension. path.parse(): breaks path into object. path.relative(): relative path between two. Always use path module instead of string concatenation for portability. Windows uses backslashes, Unix forward slashes - path handles this. Import: const path = require('path') or import path from 'path'."
    },
    {
        "question": "How do I make HTTP requests in Node.js?",
        "answer": "Built-in: http.request() (http module) - low level, callback based. Better options: fetch (Node 18+, native), axios (popular, promises, interceptors), node-fetch (polyfill), got (modern, typed). Axios example: const { data } = await axios.get(url). Native fetch: const res = await fetch(url); const data = await res.json(). For APIs, axios or fetch preferred. Set timeouts, handle errors. For many requests, use connection pooling. Behind proxy: set http_proxy env var or agent option."
    },
    {
        "question": "What is the process object in Node.js?",
        "answer": "process is global object with process info and control. process.env: environment variables. process.argv: command line arguments. process.cwd(): current working directory. process.pid: process ID. process.exit(code): terminate process. process.on('signal'): handle signals. process.nextTick(): schedule callback. process.memoryUsage(): memory stats. process.hrtime(): high-resolution time. process.stdin/stdout/stderr: standard streams. Use for CLI tools, graceful shutdown, environment config. Don't exit(1) without cleanup."
    },
    {
        "question": "How do I create a simple HTTP server in Node.js?",
        "answer": "Native: const http = require('http'); http.createServer((req, res) => { res.writeHead(200); res.end('Hello'); }).listen(3000). Express (easier): const app = express(); app.get('/', (req, res) => res.send('Hello')); app.listen(3000). Fastify (fast): fastify.get('/', async () => 'Hello'); fastify.listen({ port: 3000 }). Handle requests based on req.url and req.method. Parse JSON body with express.json() middleware. For production, use express/fastify with proper error handling, not raw http."
    },
    {
        "question": "What is package-lock.json and why is it important?",
        "answer": "package-lock.json records exact versions of all dependencies, including nested ones. Ensures reproducible installs - same versions on all machines. Auto-generated by npm install. Always commit to git. Without it: different installs may get different versions (semantic versioning allows ranges). npm ci uses lock file strictly - fails if mismatch with package.json. Don't manually edit. Regenerate: delete and npm install. Prevents 'works on my machine' issues. yarn.lock and pnpm-lock.yaml serve same purpose."
    },
    {
        "question": "How do I handle JSON in Node.js?",
        "answer": "Parse JSON string: JSON.parse(jsonString). Stringify object: JSON.stringify(obj). With formatting: JSON.stringify(obj, null, 2). Read JSON file: JSON.parse(fs.readFileSync('file.json', 'utf8')) or require('./file.json'). Write JSON: fs.writeFileSync('file.json', JSON.stringify(data, null, 2)). Handle parsing errors with try/catch. For HTTP: res.json() in Express. Request parsing: express.json() middleware. Large JSON: use streaming parsers like JSONStream. Dates don't serialize - use reviver/replacer functions."
    },
    {
        "question": "What are npm scripts and how do I use them?",
        "answer": "npm scripts are commands defined in package.json scripts field. Run with: npm run scriptname. Special scripts: start, test, build run without 'run'. Pre/post hooks: pretest runs before test. Chain commands: 'npm run build && npm run deploy'. Cross-platform: use cross-env for env vars. Pass args: npm run test -- --watch. Common scripts: start (run app), test (run tests), build (compile), dev (development mode), lint (linting). Access package.json vars: $npm_package_version. Scripts can run any CLI command."
    },
    {
        "question": "How do I use async/await in Node.js?",
        "answer": "async/await is syntactic sugar for Promises. Mark function async: async function getData(). Use await to pause until Promise resolves: const data = await fetchData(). Only works inside async function (or top-level in ESM). Error handling: try/catch around await, or .catch() on async function call. Parallel execution: await Promise.all([p1, p2]). Sequential: for await loop. async functions always return Promises. Don't forget to await - common bug is forgetting await. Avoid await in loops when parallelism is possible."
    },
    {
        "question": "What is the util module in Node.js?",
        "answer": "util module has utility functions. util.promisify(): convert callback function to Promise-based. util.inspect(): stringify objects for debugging with depth control. util.format(): printf-style string formatting. util.types: type checking functions (isPromise, isDate, etc.). util.deprecate(): mark function as deprecated. util.callbackify(): convert Promise function to callback-style. util.inherits(): prototype inheritance (use classes instead). util.TextDecoder/TextEncoder: string encoding. Very useful for callback-to-Promise migration."
    },
    {
        "question": "How do I parse command line arguments in Node.js?",
        "answer": "Raw access: process.argv (array, first two are node and script path). Manual parsing: process.argv.slice(2). Libraries: yargs (full featured, subcommands), commander (popular, typed), minimist (simple). yargs example: const argv = yargs.option('port', { type: 'number' }).parse(). Commander: program.option('-p, --port <number>').parse(). Node 18+: util.parseArgs() built-in for simple cases. Handle --help, validation, defaults. For complex CLIs, use yargs or commander. For simple scripts, minimist or manual."
    },
    {
        "question": "What is the crypto module in Node.js?",
        "answer": "crypto provides cryptographic functions. Hash: crypto.createHash('sha256').update(data).digest('hex'). HMAC: crypto.createHmac('sha256', key).update(data).digest('hex'). Random bytes: crypto.randomBytes(32). UUID: crypto.randomUUID(). Encryption: crypto.createCipheriv(). Compare safely: crypto.timingSafeEqual(). Password hashing: use bcrypt or argon2 instead of raw crypto. For web tokens: use jsonwebtoken library. crypto uses OpenSSL under hood. Be careful with cryptography - easy to misuse. Use established libraries for security-critical code."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "How do I handle memory leaks in Node.js?",
        "answer": "Common causes: unclosed connections, growing arrays/maps, event listener accumulation, closures holding references. Detection: --inspect with Chrome DevTools heap snapshots, process.memoryUsage(), clinic.js. Prevention: always clean up (removeListener, clearInterval, close connections), use weak references for caches (WeakMap), limit in-memory caching, stream large data. Monitoring: track RSS over time, alert on growth. Process managers can restart on threshold. Test with load tests and memory profiling."
    },
    {
        "question": "What are Node.js streams and when to use them?",
        "answer": "Streams process data in chunks, not all at once. Types: Readable, Writable, Duplex, Transform. Use for: large files (don't load 1GB in memory), HTTP responses, real-time data. fs.createReadStream() instead of fs.readFile(). Pipe: readable.pipe(transform).pipe(writable). Backpressure handled automatically with pipe. async iterators: for await (const chunk of stream). stream/promises has promise-based API. Key for memory-efficient processing. Modern: use pipeline() for proper error handling."
    },
    {
        "question": "How do I use Worker Threads?",
        "answer": "Worker threads for CPU-intensive tasks without blocking event loop. import { Worker, parentPort } from 'worker_threads'. Main thread creates Worker, sends messages. Worker computes, posts result back. Share data with SharedArrayBuffer for performance. Use worker pools (piscina, workerpool) for reuse. Good for: image processing, compression, crypto, parsing. Don't overuse - thread creation has overhead. Alternative: child_process for isolation, or offload to microservice. Profile first - often I/O bound not CPU bound."
    },
    {
        "question": "What is the best way to structure a large Node.js application?",
        "answer": "Common patterns: layered (controllers → services → repositories), feature-based (user/, order/ each with own layers), clean architecture. Key principles: separate concerns, dependency injection, configuration management. Directory structure: src/routes or src/controllers, src/services, src/models or src/repositories, src/middleware, src/utils. Use barrel exports (index.ts). Config in src/config. Tests mirror src structure. For monorepos: Turborepo or Nx. Avoid deep nesting. Document conventions in README."
    },
    {
        "question": "How does clustering work in Node.js?",
        "answer": "Cluster module spawns multiple Node.js processes sharing same port. Master process manages workers. Each worker is separate V8 instance with own memory. Use for: utilizing multi-core CPUs, better reliability (worker crash doesn't kill app). Primary: cluster.fork() creates workers. Workers: handle requests independently. IPC for communication. PM2 handles clustering automatically. Sticky sessions needed for WebSocket/sessions. For stateless APIs: works great. Alternative: container orchestration scales horizontally."
    },
    {
        "question": "What is the difference between child_process and worker_threads?",
        "answer": "child_process: spawns separate OS process, full isolation, higher overhead, can run any program. worker_threads: shares process, lighter overhead, shares memory (SharedArrayBuffer), Node.js only. Use child_process: running external programs, complete isolation needed, different Node versions. Use worker_threads: CPU-intensive JavaScript, when sharing data is beneficial. Both have IPC messaging. Worker threads are newer, prefer for JS computation. child_process.exec for shell commands, spawn for streaming output."
    },
    {
        "question": "How do I implement graceful shutdown in Node.js?",
        "answer": "Handle SIGTERM/SIGINT: process.on('SIGTERM', async () => {}). Steps: 1) Stop accepting new requests, 2) Wait for in-flight requests to complete, 3) Close database connections, 4) Close other resources, 5) process.exit(0). HTTP: server.close() stops new connections. Set timeout to force exit if graceful fails. Log shutdown progress. Kubernetes sends SIGTERM then SIGKILL after grace period. Test shutdown path - common source of bugs. Libraries: terminus, lightship."
    },
    {
        "question": "What is connection pooling and why is it important?",
        "answer": "Connection pooling reuses database connections instead of creating new ones per request. Benefits: faster responses (no connection overhead), predictable resource usage, prevents connection exhaustion. Implement: most drivers support (pg.Pool, mongoose, ioredis). Configure: pool size based on DB limits and concurrent requests. Monitor: track pool metrics. Release connections: use try/finally or pools that auto-release. Size: start with 10-20, tune based on load. Too many connections = memory issues, too few = queuing."
    },
    {
        "question": "How do I handle errors properly in Express?",
        "answer": "Sync errors: thrown in route, Express catches. Async errors: must call next(error) or use express-async-errors. Error middleware: (err, req, res, next) with 4 params. Place after routes. Structure: operational errors (expected, 4xx) vs programmer errors (bugs, 5xx). Log errors with stack traces. Return safe error response (no sensitive info). Custom AppError class with statusCode. Centralized error handling for consistency. In production: generic messages to users, detailed logs for debugging."
    },
    {
        "question": "What is event-driven architecture in Node.js?",
        "answer": "Node core uses EventEmitter. Pattern: emit events, listeners react. Decouples producers from consumers. Use for: internal communication, plugin systems, pub/sub patterns. Create: class MyEmitter extends EventEmitter. Emit: emitter.emit('event', data). Listen: emitter.on('event', handler). Once: emitter.once() for one-time. Error: always handle 'error' event or process crashes. Max listeners warning: emitter.setMaxListeners(). Memory: remove listeners when done. Alternative for cross-service: message queues."
    },
    {
        "question": "How do I secure a Node.js application?",
        "answer": "Layer 1 - Dependencies: npm audit, Snyk, keep updated. Layer 2 - Input: validate everything (zod, joi), parameterized queries, sanitize HTML. Layer 3 - HTTP: helmet.js (security headers), CORS config, rate limiting, HTTPS only. Layer 4 - Auth: bcrypt for passwords, JWT with short expiry, httpOnly cookies. Layer 5 - Secrets: env vars, never in code, rotate regularly. Layer 6 - Monitoring: log security events, detect anomalies. OWASP Top 10 as checklist. Security audits for critical apps."
    },
    {
        "question": "What is the N+1 query problem and how to solve it in Node.js?",
        "answer": "N+1: fetching N items then making N more queries for related data. Example: fetch users, then fetch posts for each user separately. Identify: look for queries in loops. Solutions: JOIN queries, eager loading (Prisma: include, Sequelize: include). For GraphQL: DataLoader batches and caches requests within request. Prisma: use include for relations. Sequelize: include option with eager loading. Monitor: log slow queries, count queries per request. Critical for performance at scale."
    },
    # === EXPANDED ADVANCED CONCEPTS ===
    {
        "question": "How do I implement rate limiting in Node.js?",
        "answer": "Prevent abuse by limiting requests per time window. express-rate-limit: simple setup for Express. Strategies: fixed window, sliding window, token bucket. Store: in-memory (single instance), Redis (distributed). Configuration: windowMs, max requests, message. Key by: IP, user ID, API key. Separate limits for different endpoints (auth stricter). Headers: X-RateLimit-Remaining, X-RateLimit-Reset. Handle limit exceeded gracefully (429 status). For APIs: per-key limits. Consider DDoS protection at infrastructure level (Cloudflare, AWS WAF)."
    },
    {
        "question": "What is the best logging strategy for Node.js?",
        "answer": "Use structured logging: pino (fastest), winston (flexible), bunyan. JSON format for parsing. Log levels: error, warn, info, debug. Include: timestamp, request ID, user ID, context. Don't log sensitive data (passwords, tokens). Correlation IDs trace requests across services. In production: centralize logs (ELK, CloudWatch, Datadog). Performance: pino is async, minimal overhead. Child loggers for context. Rotate logs by size/time. Log errors with stack traces. Development: pretty print, production: JSON."
    },
    {
        "question": "How do I test Node.js applications effectively?",
        "answer": "Testing pyramid: unit (fast, many), integration (medium), e2e (slow, few). Frameworks: Jest (popular, all-in-one), Vitest (fast, ESM), Mocha+Chai. Unit tests: mock dependencies, test functions in isolation. Integration: test API endpoints with supertest. E2E: test full flows. Coverage: aim for 80%+, cover edge cases. Mocking: jest.mock(), sinon. Database: use test DB or in-memory (SQLite). CI: run on every PR. TDD for complex logic. Test error paths, not just happy paths."
    },
    {
        "question": "What are best practices for Node.js REST API design?",
        "answer": "Use proper HTTP methods: GET (read), POST (create), PUT/PATCH (update), DELETE. Resource naming: nouns, plural (/users, /posts). Status codes: 200 (OK), 201 (created), 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error). Versioning: /api/v1/. Pagination: limit/offset or cursor-based. Filtering: query params (?status=active). Sorting: ?sort=created_at:desc. Validation: validate input at controller level. Documentation: OpenAPI/Swagger. HATEOAS for discoverability."
    },
    {
        "question": "How do I handle database migrations in Node.js?",
        "answer": "Migrations track database schema changes over time. Tools: Prisma Migrate, Knex migrations, Sequelize migrations, node-pg-migrate. Each migration: up (apply) and down (revert). Version control migrations. Run in order. Never edit applied migrations - create new ones. In CI/CD: migrate before deploy. For rollback: down migration. Separate data migrations from schema. Test migrations on staging first. For Prisma: prisma migrate dev (development), prisma migrate deploy (production). Lock prevents concurrent migrations."
    },
    {
        "question": "What is dependency injection in Node.js?",
        "answer": "DI decouples components by injecting dependencies instead of creating them. Benefits: testable (inject mocks), flexible (swap implementations), explicit dependencies. Patterns: constructor injection, property injection, factory functions. Libraries: awilix, tsyringe, InversifyJS (with decorators). Simple approach: pass dependencies as constructor params. Container: registers and resolves dependencies. Scopes: singleton, transient, request-scoped. NestJS has built-in DI. For testing: inject test doubles. Reduces tight coupling between modules."
    },
    {
        "question": "How do I implement authentication with JWT?",
        "answer": "JWT: JSON Web Token for stateless auth. Flow: login → server creates JWT → client stores → sends in Authorization header → server verifies. Structure: header.payload.signature. Use jsonwebtoken library. Sign: jwt.sign(payload, secret, { expiresIn: '1h' }). Verify: jwt.verify(token, secret). Store in httpOnly cookie (XSS safe) or localStorage (easier but less secure). Refresh tokens for long sessions. Short access token expiry (15min-1hr). Blacklist for logout if needed. Never store sensitive data in payload (it's just base64)."
    },
    {
        "question": "What is caching and how do I implement it in Node.js?",
        "answer": "Caching stores computed results for faster retrieval. Levels: in-memory (node-cache, LRU), Redis (distributed), HTTP cache (ETags, Cache-Control). Cache-aside pattern: check cache → miss → compute → store → return. Set TTL appropriately. Cache invalidation is hard - use time-based expiry for simplicity. For APIs: cache GET requests. Redis: ioredis client, supports pub/sub for invalidation. Memory cache: fast but per-process. Consider cache stampede - use locking. Don't cache user-specific data without proper keys."
    },
    {
        "question": "How do I handle file uploads in Node.js?",
        "answer": "Multer middleware for Express handles multipart/form-data. Configuration: dest (folder), limits (size), fileFilter (type). Store to disk or memory. For cloud: stream directly to S3/GCS with multer-s3. Validate: file type (mime type + extension), size limits. Security: random filenames, don't execute uploads, virus scan if needed. For large files: chunked upload, resumable. Progress: track upload progress client-side. Cleanup: delete failed uploads. Return file URL/ID after upload. Consider CDN for serving files."
    },
    {
        "question": "What are WebSockets and how do I use them in Node.js?",
        "answer": "WebSocket: persistent bidirectional connection. Use for: real-time features, chat, live updates, games. Libraries: ws (raw), Socket.IO (features: rooms, fallbacks, reconnection). ws: const wss = new WebSocket.Server({ port: 8080 }); wss.on('connection', ws => {}). Socket.IO: io.on('connection', socket => {}). Rooms for grouping connections. Handle disconnections gracefully. Scale with Redis adapter (Socket.IO) or sticky sessions. Authentication: verify on connection. Keep-alive: ping/pong. Don't use for: simple request/response (use HTTP)."
    },
    {
        "question": "How do I implement background jobs in Node.js?",
        "answer": "For async tasks: email sending, image processing, reports. Libraries: Bull (Redis-based), Agenda (MongoDB), BullMQ (modern Bull). Queue: add jobs, workers process. Features: retries, delays, cron scheduling, priorities. Bull example: queue.add('email', data); queue.process('email', async job => {}). Separate worker process for reliability. Monitor: Bull Board UI. Handle failures: dead letter queue. For simple cases: node-schedule for cron. At scale: dedicated job services. Don't block main process with long tasks."
    },
    {
        "question": "What is PM2 and how do I use it?",
        "answer": "PM2 is production process manager for Node.js. Features: clustering, auto-restart, load balancing, zero-downtime reload. Start: pm2 start app.js -i max (cluster mode, all CPUs). Ecosystem file: ecosystem.config.js for configuration. Commands: pm2 list, pm2 logs, pm2 monit, pm2 reload. Startup: pm2 startup, pm2 save. Metrics: pm2 plus for monitoring dashboard. Zero-downtime: pm2 reload app. Memory limit: max_memory_restart option. Log rotation: pm2 install pm2-logrotate. Alternative: systemd for simple cases."
    },
]

# =============================================================================
# ERROR SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "UnhandledPromiseRejection crashing Node.js",
        "error_type": "async_error",
        "response": {
            "status": "critical",
            "cause": "Promise rejection without .catch() or try/catch in async function",
            "solutions": [
                "Always use try/catch in async functions",
                "Always .catch() on promises",
                "Use asyncHandler wrapper for Express routes",
                "Global handler: process.on('unhandledRejection', handler)"
            ],
            "note": "Node 15+ treats unhandled rejections as crashes by default",
            "best_practice": "Global handler should log and exit gracefully, not suppress"
        }
    },
    {
        "instruction": "ECONNREFUSED when connecting to database",
        "error_type": "connection_error",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Is database server running?",
                "Correct host/port in connection string?",
                "Firewall allowing connections?",
                "Database accepting connections (pg_hba.conf)?",
                "Connection string format correct?"
            ],
            "docker_specific": "Use service name as host, not localhost",
            "recovery": "Implement connection retry with exponential backoff"
        }
    },
    {
        "instruction": "require is not defined in ES module scope",
        "error_type": "module_error",
        "response": {
            "status": "fixable",
            "cause": "Using require() in ES module (type: module in package.json)",
            "solutions": [
                "Replace with: import x from 'package'",
                "For CJS packages: const x = await import('package')",
                "For __dirname: import.meta.dirname (Node 20+)",
                "For __filename: import.meta.filename (Node 20+)",
                "Or: fileURLToPath(import.meta.url)"
            ]
        }
    },
    {
        "instruction": "ENOMEM: not enough memory, JavaScript heap out of memory",
        "error_type": "memory_error",
        "response": {
            "status": "critical",
            "cause": "V8 heap exceeded - processing too much data in memory",
            "solutions": [
                "Increase heap: node --max-old-space-size=4096",
                "Use streams instead of loading entire file",
                "Process data in chunks",
                "Check for memory leaks with heap snapshots",
                "Reduce concurrent operations"
            ],
            "investigation": "Use --inspect and Chrome DevTools to analyze heap"
        }
    },
    {
        "instruction": "ENOENT: no such file or directory",
        "error_type": "file_error",
        "response": {
            "status": "fixable",
            "common_causes": [
                "File path incorrect",
                "Working directory different from expected",
                "File not created yet",
                "Relative path resolved from wrong location"
            ],
            "solutions": [
                "Use path.join(__dirname, 'file') for relative paths",
                "Check process.cwd() vs __dirname",
                "Verify file exists: fs.existsSync()",
                "Use absolute paths from project root"
            ]
        }
    },
    {
        "instruction": "EADDRINUSE: address already in use",
        "error_type": "port_error",
        "response": {
            "status": "fixable",
            "cause": "Another process using the port",
            "solutions": [
                "Kill process: lsof -i :3000 then kill PID",
                "Windows: netstat -ano | findstr :3000 then taskkill /PID",
                "Use different port",
                "Ensure proper cleanup on process exit"
            ],
            "prevention": "Handle SIGTERM to close server gracefully"
        }
    },
    {
        "instruction": "ERR_MODULE_NOT_FOUND: Cannot find module",
        "error_type": "import_error",
        "response": {
            "status": "troubleshoot",
            "common_causes": [
                "Module not installed: npm install missing",
                "Typo in module name",
                "File extension required in ESM: import './file.js'",
                "Package not ESM compatible"
            ],
            "solutions": [
                "Check package.json dependencies",
                "Add file extension for local imports",
                "Use .js extension even for .ts source files",
                "Check package exports field compatibility"
            ]
        }
    },
    {
        "instruction": "Error: listen EACCES: permission denied on port 80",
        "error_type": "permission_error",
        "response": {
            "status": "fixable",
            "cause": "Ports below 1024 require root/admin privileges",
            "solutions": [
                "Use port 3000+ for development",
                "Use reverse proxy (nginx) on port 80",
                "Linux: setcap CAP_NET_BIND_SERVICE on node binary",
                "Docker: map 3000:80 in container"
            ],
            "warning": "Don't run Node as root in production"
        }
    },
    {
        "instruction": "MaxListenersExceededWarning: Possible EventEmitter memory leak",
        "error_type": "resource_warning",
        "response": {
            "status": "investigate",
            "cause": "More than 10 listeners added to single event",
            "possibilities": [
                "Actual memory leak - listeners not removed",
                "Legitimate need for many listeners",
                "Adding listeners in loop without cleanup"
            ],
            "solutions": [
                "Remove listeners when done: emitter.removeListener()",
                "Use once() for one-time listeners",
                "If legitimate: emitter.setMaxListeners(n)",
                "Audit listener registration patterns"
            ]
        }
    },
    {
        "instruction": "Error: Cannot find package '@types/express'",
        "error_type": "typescript_error",
        "response": {
            "status": "fixable",
            "cause": "TypeScript types not installed for JavaScript package",
            "solutions": [
                "Install: npm install -D @types/express",
                "Check DefinitelyTyped for package name variations",
                "Create local .d.ts file if types don't exist",
                "Use // @ts-ignore as last resort"
            ],
            "tip": "Many modern packages include types - check package.json types field"
        }
    },
    {
        "instruction": "TypeError: Cannot read properties of undefined (reading 'x')",
        "error_type": "runtime_error",
        "response": {
            "status": "common_bug",
            "cause": "Accessing property on undefined/null value",
            "common_sources": [
                "Async data not loaded yet",
                "API response missing expected field",
                "Function parameter not passed",
                "Object destructuring on undefined"
            ],
            "solutions": [
                "Use optional chaining: obj?.property",
                "Add null checks before access",
                "Validate API responses",
                "Provide default values"
            ]
        }
    },
    {
        "instruction": "Error: CORS policy: No 'Access-Control-Allow-Origin' header",
        "error_type": "cors_error",
        "response": {
            "status": "fixable",
            "cause": "Browser blocking cross-origin request",
            "solutions": [
                "Install cors: npm install cors",
                "Use middleware: app.use(cors())",
                "Configure specific origins: cors({ origin: 'http://localhost:3000' })",
                "Handle preflight: OPTIONS requests"
            ],
            "note": "CORS is browser security - server must explicitly allow cross-origin"
        }
    },
    {
        "instruction": "Error: EMFILE: too many open files",
        "error_type": "resource_error",
        "response": {
            "status": "system_limit",
            "cause": "Operating system file descriptor limit reached",
            "solutions": [
                "Increase limit: ulimit -n 10000",
                "Ensure files are closed after use",
                "Use streams for large files",
                "Pool and reuse file handles",
                "Check for file handle leaks"
            ],
            "persistent": "Add to /etc/security/limits.conf for permanent change"
        }
    },
    {
        "instruction": "SyntaxError: Unexpected token 'export'",
        "error_type": "module_error",
        "response": {
            "status": "fixable",
            "cause": "ES module syntax in CommonJS context",
            "solutions": [
                "Add 'type': 'module' to package.json",
                "Use .mjs extension",
                "Convert to CommonJS: module.exports = ",
                "Configure bundler to handle ESM"
            ],
            "note": "Can't mix import/export with require in same file"
        }
    },
    # === EXPANDED ERROR SCENARIOS ===
    {
        "instruction": "Error: ETIMEDOUT when making HTTP requests",
        "error_type": "network_error",
        "response": {
            "status": "troubleshoot",
            "cause": "HTTP request timed out before response",
            "common_reasons": [
                "Server taking too long to respond",
                "Network connectivity issues",
                "DNS resolution problems",
                "Server overloaded"
            ],
            "solutions": [
                "Increase timeout: axios.get(url, { timeout: 30000 })",
                "Add retry logic with exponential backoff",
                "Check if server is reachable: curl/ping",
                "Use connection pooling for repeated requests"
            ],
            "pattern": "Use axios-retry or got for automatic retries"
        }
    },
    {
        "instruction": "Error: CERT_HAS_EXPIRED or UNABLE_TO_VERIFY_LEAF_SIGNATURE",
        "error_type": "ssl_error",
        "response": {
            "status": "security_risk",
            "cause": "SSL/TLS certificate validation failure",
            "do_not": "Never use NODE_TLS_REJECT_UNAUTHORIZED=0 in production",
            "proper_solutions": [
                "Fix/renew the server certificate",
                "Add CA certificate: { ca: fs.readFileSync('ca.pem') }",
                "Update Node.js for latest root CAs",
                "For self-signed dev: provide cert in request options"
            ],
            "debug": "openssl s_client -connect host:443 to inspect cert"
        }
    },
    {
        "instruction": "TypeError: req.body is undefined in Express",
        "error_type": "middleware_error",
        "response": {
            "status": "fixable",
            "cause": "Body-parser middleware not configured",
            "solutions": [
                "Add: app.use(express.json())",
                "Add: app.use(express.urlencoded({ extended: true }))",
                "Ensure middleware is added BEFORE routes",
                "Check Content-Type header is application/json"
            ],
            "order_matters": "Middleware order: cors, body-parser, routes"
        }
    },
    {
        "instruction": "Error: querySelectorAll is not a function (DOM in Node)",
        "error_type": "environment_error",
        "response": {
            "status": "wrong_environment",
            "cause": "Trying to use browser APIs in Node.js",
            "solutions": [
                "Use JSDOM for HTML parsing: new JSDOM(html)",
                "Use cheerio for jQuery-like parsing",
                "Use Puppeteer for full browser automation",
                "Check if code should run client-side only"
            ],
            "tip": "Use isomorphic-fetch for code that runs in both environments"
        }
    },
    {
        "instruction": "MongoServerError: E11000 duplicate key error",
        "error_type": "database_error",
        "response": {
            "status": "data_integrity",
            "cause": "Trying to insert document with duplicate unique key",
            "solutions": [
                "Check for existing document before insert",
                "Use upsert: updateOne with { upsert: true }",
                "Handle error gracefully in catch block",
                "Review if unique index is correct"
            ],
            "pattern": "Use findOneAndUpdate with upsert for idempotent operations"
        }
    },
    {
        "instruction": "Error: Cannot set headers after they are sent to the client",
        "error_type": "http_error",
        "response": {
            "status": "logic_bug",
            "cause": "Trying to send multiple responses to same request",
            "common_causes": [
                "Missing return after res.send()",
                "Async callback executing after response sent",
                "Multiple middleware calling next() and sending response"
            ],
            "solutions": [
                "Always return after res.send/json/redirect",
                "Check async flow - ensure single response path",
                "Use res.headersSent check before sending"
            ]
        }
    },
    {
        "instruction": "Segmentation fault in native module",
        "error_type": "native_crash",
        "response": {
            "status": "critical",
            "cause": "Native addon crashed - usually memory corruption",
            "common_sources": [
                "Incompatible native module version",
                "Node.js version mismatch with compiled addon",
                "Bug in native code"
            ],
            "solutions": [
                "Rebuild native modules: npm rebuild",
                "Clear node_modules and reinstall",
                "Check Node.js version compatibility",
                "Use node-pre-gyp or prebuild for prebuilt binaries",
                "Report issue to module maintainer"
            ],
            "debug": "Run with: node --abort-on-uncaught-exception"
        }
    },
    {
        "instruction": "Warning: Accessing non-existent property of module exports",
        "error_type": "import_warning",
        "response": {
            "status": "likely_bug",
            "cause": "Importing property that doesn't exist on module",
            "common_causes": [
                "Named import from module with only default export",
                "Module API changed in newer version",
                "Circular dependency causing partial exports"
            ],
            "solutions": [
                "Check module documentation for correct import",
                "Use default import: import pkg from 'pkg'",
                "Review for circular dependencies",
                "Check package version matches docs"
            ]
        }
    },
    {
        "instruction": "Error: request entity too large",
        "error_type": "payload_error",
        "response": {
            "status": "configurable",
            "cause": "Request body exceeds size limit",
            "solutions": [
                "Increase limit: express.json({ limit: '50mb' })",
                "Configure nginx/load balancer body size",
                "Implement file upload with multipart/form-data",
                "Consider streaming for large payloads"
            ],
            "security": "Don't increase limits blindly - DoS risk"
        }
    },
    {
        "instruction": "Prisma error: P2002 Unique constraint failed",
        "error_type": "orm_error",
        "response": {
            "status": "constraint_violation",
            "cause": "Trying to create/update with duplicate unique field",
            "solutions": [
                "Check for existing record: findUnique first",
                "Use upsert for create-or-update pattern",
                "Handle error with specific error code check",
                "Review schema constraints"
            ],
            "pattern": "try { await prisma.user.create() } catch (e) { if (e.code === 'P2002') ... }"
        }
    },
    {
        "instruction": "Error: spawn ENOENT when executing child process",
        "error_type": "process_error",
        "response": {
            "status": "command_not_found",
            "cause": "Executable not found in PATH",
            "common_causes": [
                "Command not installed",
                "Wrong command name",
                "PATH not inherited in child process",
                "Windows: need .exe or use shell: true"
            ],
            "solutions": [
                "Verify command exists: which/where command",
                "Use full path to executable",
                "Set shell: true for shell built-ins",
                "Check environment variables passed to spawn"
            ]
        }
    },
    {
        "instruction": "RangeError: Maximum call stack size exceeded",
        "error_type": "recursion_error",
        "response": {
            "status": "infinite_recursion",
            "cause": "Recursive function without proper base case",
            "common_causes": [
                "Infinite recursion in code",
                "Circular object when JSON.stringify",
                "Accidentally recursive property access"
            ],
            "solutions": [
                "Add/fix base case in recursive function",
                "Use iterative approach instead",
                "For circular JSON: use circular-json library",
                "Check for accidental property recursion"
            ],
            "debug": "Add console.trace() to see call stack"
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
    } for task in NODE_TASKS]

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
    print("Generating Node.js Training Data")
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
    
    output_file = output_dir / "nodejs.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
