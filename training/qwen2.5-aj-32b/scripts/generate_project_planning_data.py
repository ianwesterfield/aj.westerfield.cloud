#!/usr/bin/env python3
"""
Generate project planning and multi-step plan training examples.

Focuses on: greenfield project setup, migration roadmaps, feature plans,
debugging workflows, and architectural decisions.
Boosts the 'multi_step_plan' response type.
"""

import json
from pathlib import Path
from typing import List, Dict

# Output path
OUTPUT_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, a technical AI assistant created by AJ Westerfield. You excel at breaking down complex projects into clear, actionable steps. You provide comprehensive planning guidance including prerequisites, step-by-step instructions, potential pitfalls, and verification steps."""

# Project planning examples
PROJECT_PLANNING_EXAMPLES: List[Dict] = [
    # Greenfield project setup
    {
        "instruction": "I want to create a new Python web API project with FastAPI, PostgreSQL, and Docker. What's the setup process?",
        "response": {
            "action": "multi_step_plan",
            "project_type": "FastAPI Web API",
            "estimated_time": "2-3 hours for initial setup",
            "steps": [
                {
                    "step": 1,
                    "title": "Initialize Project Structure",
                    "commands": [
                        "mkdir my-api && cd my-api",
                        "python -m venv venv",
                        "source venv/bin/activate  # or venv\\Scripts\\activate on Windows",
                        "pip install fastapi uvicorn sqlalchemy asyncpg alembic pydantic-settings python-dotenv pytest pytest-asyncio httpx"
                    ],
                    "files_to_create": [
                        "src/__init__.py",
                        "src/main.py",
                        "src/config.py",
                        "src/database.py",
                        "src/models/__init__.py",
                        "src/schemas/__init__.py",
                        "src/api/__init__.py",
                        "src/api/routes/__init__.py",
                        "tests/__init__.py"
                    ]
                },
                {
                    "step": 2,
                    "title": "Configure Environment and Settings",
                    "description": "Create .env file and pydantic settings",
                    "env_example": "DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mydb\nSECRET_KEY=your-secret-key\nDEBUG=true",
                    "config_code": "# src/config.py\nfrom pydantic_settings import BaseSettings\n\nclass Settings(BaseSettings):\n    database_url: str\n    secret_key: str\n    debug: bool = False\n    \n    class Config:\n        env_file = '.env'\n\nsettings = Settings()"
                },
                {
                    "step": 3,
                    "title": "Set Up Database Connection",
                    "description": "Configure async SQLAlchemy with connection pooling",
                    "key_considerations": [
                        "Use async engine for better performance",
                        "Configure connection pool size based on expected load",
                        "Set up session middleware for request-scoped sessions"
                    ]
                },
                {
                    "step": 4,
                    "title": "Initialize Alembic for Migrations",
                    "commands": [
                        "alembic init alembic",
                        "# Edit alembic/env.py to use async and import your models",
                        "alembic revision --autogenerate -m 'initial'",
                        "alembic upgrade head"
                    ]
                },
                {
                    "step": 5,
                    "title": "Create Docker Configuration",
                    "files": {
                        "Dockerfile": "FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY src/ src/\nCMD [\"uvicorn\", \"src.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]",
                        "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n    ports:\n      - '8000:8000'\n    environment:\n      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/mydb\n    depends_on:\n      - db\n  db:\n    image: postgres:15\n    environment:\n      - POSTGRES_PASSWORD=postgres\n      - POSTGRES_DB=mydb\n    volumes:\n      - pgdata:/var/lib/postgresql/data\nvolumes:\n  pgdata:"
                    }
                },
                {
                    "step": 6,
                    "title": "Set Up Testing Infrastructure",
                    "description": "Configure pytest with async support and test database",
                    "files": [
                        "pytest.ini",
                        "tests/conftest.py with fixtures",
                        "tests/test_api.py"
                    ]
                },
                {
                    "step": 7,
                    "title": "Add Development Tools",
                    "commands": [
                        "pip install black isort mypy ruff pre-commit",
                        "# Create pyproject.toml with tool configs",
                        "pre-commit install"
                    ]
                }
            ],
            "verification": [
                "docker-compose up -d",
                "curl http://localhost:8000/health",
                "pytest tests/ -v"
            ],
            "next_steps": [
                "Add authentication (JWT or OAuth)",
                "Set up CI/CD pipeline",
                "Configure logging and monitoring",
                "Add API documentation with examples"
            ]
        }
    },
    
    # Migration roadmap
    {
        "instruction": "We need to migrate our monolithic Django app to microservices. How should we approach this?",
        "response": {
            "action": "multi_step_plan",
            "project_type": "Monolith to Microservices Migration",
            "estimated_time": "3-6 months depending on codebase size",
            "principles": [
                "Strangler Fig Pattern - gradually replace, don't rewrite",
                "Start with clear domain boundaries",
                "Keep the monolith running during migration",
                "Extract one service at a time, validate, repeat"
            ],
            "phases": [
                {
                    "phase": 1,
                    "title": "Assessment and Planning (2-3 weeks)",
                    "tasks": [
                        "Map all modules and their dependencies",
                        "Identify bounded contexts (user, orders, inventory, etc.)",
                        "Analyze database schema coupling",
                        "Measure module-to-module API calls",
                        "Identify the best candidate for first extraction"
                    ],
                    "deliverables": [
                        "Dependency graph",
                        "Bounded context map",
                        "Risk assessment",
                        "Migration sequence plan"
                    ],
                    "criteria_for_first_service": [
                        "Low coupling to other modules",
                        "Clear domain boundary",
                        "Moderate complexity (not too simple, not too risky)",
                        "Team has domain expertise"
                    ]
                },
                {
                    "phase": 2,
                    "title": "Infrastructure Setup (2-3 weeks)",
                    "tasks": [
                        "Set up container orchestration (Kubernetes/ECS)",
                        "Implement service discovery",
                        "Set up API gateway for routing",
                        "Configure centralized logging (ELK/Datadog)",
                        "Set up distributed tracing (Jaeger/Zipkin)",
                        "Create CI/CD pipelines for microservices"
                    ],
                    "key_decisions": [
                        "Sync vs async communication (REST/gRPC vs message queues)",
                        "Shared database vs database per service",
                        "Service mesh needs (Istio, Linkerd)"
                    ]
                },
                {
                    "phase": 3,
                    "title": "Extract First Service (3-4 weeks)",
                    "steps": [
                        {
                            "step": "3.1",
                            "title": "Create API boundary in monolith",
                            "description": "Refactor internal calls to go through an internal API layer"
                        },
                        {
                            "step": "3.2",
                            "title": "Build new service",
                            "description": "Implement the same API in a new microservice"
                        },
                        {
                            "step": "3.3",
                            "title": "Data migration strategy",
                            "options": [
                                "Sync replication during transition",
                                "Event sourcing from monolith",
                                "Dual-write with eventual consistency"
                            ]
                        },
                        {
                            "step": "3.4",
                            "title": "Deploy with feature flag",
                            "description": "Route percentage of traffic to new service"
                        },
                        {
                            "step": "3.5",
                            "title": "Validate and cutover",
                            "description": "Monitor metrics, gradually increase traffic, then remove old code"
                        }
                    ]
                },
                {
                    "phase": 4,
                    "title": "Iterate and Scale (ongoing)",
                    "tasks": [
                        "Extract next service following same pattern",
                        "Refine inter-service communication",
                        "Implement saga pattern for distributed transactions",
                        "Add circuit breakers and retry logic",
                        "Document service contracts"
                    ]
                }
            ],
            "risks_and_mitigations": [
                {
                    "risk": "Distributed transactions",
                    "mitigation": "Use saga pattern, design for eventual consistency"
                },
                {
                    "risk": "Network failures",
                    "mitigation": "Circuit breakers, retries, timeouts, fallbacks"
                },
                {
                    "risk": "Data consistency",
                    "mitigation": "Event sourcing, CDC (Change Data Capture)"
                },
                {
                    "risk": "Operational complexity",
                    "mitigation": "Invest in observability, runbooks, on-call training"
                }
            ],
            "success_metrics": [
                "Deployment frequency per service",
                "Mean time to recovery (MTTR)",
                "Service latency and error rates",
                "Team autonomy (independent releases)"
            ]
        }
    },
    
    # Feature implementation plan
    {
        "instruction": "I need to add real-time notifications to our React app. We have a Node.js backend. What's the plan?",
        "response": {
            "action": "multi_step_plan",
            "feature": "Real-time Notifications",
            "tech_stack": "React frontend, Node.js backend, WebSockets",
            "estimated_time": "1-2 weeks",
            "phases": [
                {
                    "phase": 1,
                    "title": "Backend WebSocket Setup",
                    "time": "2-3 days",
                    "tasks": [
                        {
                            "task": "Install Socket.IO",
                            "command": "npm install socket.io",
                            "notes": "Socket.IO handles fallbacks and reconnection automatically"
                        },
                        {
                            "task": "Create WebSocket server",
                            "description": "Initialize alongside Express, handle connection/auth"
                        },
                        {
                            "task": "Implement authentication",
                            "description": "Verify JWT on connection, attach user to socket"
                        },
                        {
                            "task": "Set up rooms/channels",
                            "description": "User-specific room for targeted notifications"
                        }
                    ],
                    "code_structure": [
                        "src/websocket/index.ts - Socket.IO initialization",
                        "src/websocket/handlers/ - Event handlers",
                        "src/websocket/middleware/auth.ts - Auth middleware"
                    ]
                },
                {
                    "phase": 2,
                    "title": "Notification Service",
                    "time": "2-3 days",
                    "tasks": [
                        {
                            "task": "Design notification model",
                            "fields": ["id", "userId", "type", "title", "body", "data", "read", "createdAt"]
                        },
                        {
                            "task": "Create notification service",
                            "methods": ["create()", "markAsRead()", "getUnread()", "broadcast()"]
                        },
                        {
                            "task": "Integrate with existing events",
                            "examples": [
                                "Order placed -> notify user",
                                "Comment on post -> notify author",
                                "Mention -> notify mentioned user"
                            ]
                        },
                        {
                            "task": "Add REST endpoints",
                            "endpoints": [
                                "GET /api/notifications - list user notifications",
                                "PATCH /api/notifications/:id/read - mark as read",
                                "POST /api/notifications/read-all - mark all read"
                            ]
                        }
                    ]
                },
                {
                    "phase": 3,
                    "title": "Frontend Integration",
                    "time": "2-3 days",
                    "tasks": [
                        {
                            "task": "Install Socket.IO client",
                            "command": "npm install socket.io-client"
                        },
                        {
                            "task": "Create WebSocket context/hook",
                            "description": "Manage connection lifecycle, reconnection"
                        },
                        {
                            "task": "Build notification components",
                            "components": [
                                "NotificationBell - icon with unread count",
                                "NotificationDropdown - list recent notifications",
                                "NotificationToast - pop-up for new notifications",
                                "NotificationPage - full notification history"
                            ]
                        },
                        {
                            "task": "Add to app shell",
                            "description": "Connect on auth, show bell in header"
                        }
                    ]
                },
                {
                    "phase": 4,
                    "title": "Polish and Production",
                    "time": "2-3 days",
                    "tasks": [
                        {
                            "task": "Add sound/browser notifications",
                            "description": "Request permission, play sound on new notification"
                        },
                        {
                            "task": "Implement notification preferences",
                            "description": "Let users choose which notifications to receive"
                        },
                        {
                            "task": "Add rate limiting",
                            "description": "Prevent notification spam"
                        },
                        {
                            "task": "Scale for production",
                            "options": [
                                "Redis adapter for multi-server",
                                "Message queue for high volume",
                                "Batch notifications for digest"
                            ]
                        },
                        {
                            "task": "Add tests",
                            "tests": [
                                "Unit tests for notification service",
                                "Integration tests for WebSocket events",
                                "E2E tests for notification flow"
                            ]
                        }
                    ]
                }
            ],
            "architecture_decision": {
                "recommendation": "Socket.IO over raw WebSockets",
                "reasons": [
                    "Automatic reconnection handling",
                    "Room/namespace support built-in",
                    "Fallback to polling if needed",
                    "Redis adapter for horizontal scaling"
                ]
            }
        }
    },
    
    # Debugging workflow
    {
        "instruction": "Our production API is responding slowly. How do I diagnose and fix the performance issue?",
        "response": {
            "action": "multi_step_plan",
            "problem": "API Performance Degradation",
            "approach": "Systematic diagnosis from high-level to specific",
            "steps": [
                {
                    "step": 1,
                    "title": "Gather Initial Data",
                    "time": "15-30 minutes",
                    "tasks": [
                        "Check monitoring dashboards (response times, error rates)",
                        "Identify when the slowness started",
                        "Check if it affects all endpoints or specific ones",
                        "Review recent deployments or config changes",
                        "Check infrastructure metrics (CPU, memory, disk, network)"
                    ],
                    "tools": ["Datadog/New Relic APM", "CloudWatch/Grafana", "Application logs"]
                },
                {
                    "step": 2,
                    "title": "Identify the Bottleneck Layer",
                    "time": "30-60 minutes",
                    "checks": [
                        {
                            "layer": "Load Balancer/CDN",
                            "indicators": ["High latency before reaching app", "Connection timeouts"],
                            "check": "curl -w '@curl-format.txt' https://your-api.com/health"
                        },
                        {
                            "layer": "Application Server",
                            "indicators": ["High CPU/memory", "Thread pool exhaustion", "GC pauses"],
                            "check": "Application metrics, profiler, thread dumps"
                        },
                        {
                            "layer": "Database",
                            "indicators": ["Slow queries", "Connection pool exhaustion", "Lock contention"],
                            "check": "Slow query log, pg_stat_statements, EXPLAIN ANALYZE"
                        },
                        {
                            "layer": "External Services",
                            "indicators": ["Timeout on downstream calls", "Circuit breakers tripping"],
                            "check": "Distributed tracing, service health checks"
                        }
                    ]
                },
                {
                    "step": 3,
                    "title": "Database Investigation (Common Culprit)",
                    "time": "1-2 hours",
                    "queries": {
                        "postgresql": [
                            "-- Find slow queries\nSELECT query, calls, mean_time, total_time\nFROM pg_stat_statements\nORDER BY mean_time DESC LIMIT 20;",
                            "-- Check for missing indexes\nSELECT relname, seq_scan, idx_scan\nFROM pg_stat_user_tables\nWHERE seq_scan > idx_scan;",
                            "-- Active connections\nSELECT state, count(*)\nFROM pg_stat_activity\nGROUP BY state;",
                            "-- Lock contention\nSELECT * FROM pg_locks WHERE NOT granted;"
                        ]
                    },
                    "common_fixes": [
                        "Add missing indexes",
                        "Optimize N+1 queries with joins/eager loading",
                        "Increase connection pool size",
                        "Add query result caching"
                    ]
                },
                {
                    "step": 4,
                    "title": "Application Profiling",
                    "time": "1-2 hours",
                    "tasks": [
                        {
                            "task": "Enable APM tracing",
                            "description": "See breakdown of time spent in each operation"
                        },
                        {
                            "task": "Profile hot endpoints",
                            "python": "py-spy, cProfile",
                            "node": "clinic.js, 0x"
                        },
                        {
                            "task": "Check for",
                            "issues": [
                                "Synchronous I/O blocking event loop",
                                "Memory leaks causing GC pressure",
                                "Inefficient algorithms (O(n²) in loops)",
                                "Missing caching for repeated computations"
                            ]
                        }
                    ]
                },
                {
                    "step": 5,
                    "title": "Implement Fixes",
                    "priority_order": [
                        "Quick wins: Add indexes, fix obvious N+1 queries",
                        "Caching: Redis for frequently accessed data",
                        "Code optimization: Refactor hot paths",
                        "Infrastructure: Scale up/out if needed"
                    ]
                },
                {
                    "step": 6,
                    "title": "Validate and Monitor",
                    "tasks": [
                        "Load test the fix in staging",
                        "Deploy with feature flag if possible",
                        "Monitor metrics closely after deploy",
                        "Set up alerts for regression"
                    ]
                }
            ],
            "prevention": [
                "Set up performance budgets and alerts",
                "Regular load testing in CI/CD",
                "Database query review in code review",
                "APM in all environments"
            ]
        }
    },
    
    # CI/CD Pipeline Setup
    {
        "instruction": "I need to set up CI/CD for our TypeScript monorepo. We use GitHub and want to deploy to AWS.",
        "response": {
            "action": "multi_step_plan",
            "project_type": "TypeScript Monorepo CI/CD",
            "platform": "GitHub Actions -> AWS",
            "estimated_time": "1-2 weeks",
            "phases": [
                {
                    "phase": 1,
                    "title": "Repository Setup",
                    "time": "1-2 days",
                    "tasks": [
                        {
                            "task": "Configure monorepo tool",
                            "options": ["Turborepo (recommended)", "Nx", "Lerna"],
                            "setup": "npx create-turbo@latest"
                        },
                        {
                            "task": "Structure packages",
                            "structure": {
                                "apps/": ["web", "api", "admin"],
                                "packages/": ["shared", "ui", "config"]
                            }
                        },
                        {
                            "task": "Configure workspaces",
                            "file": "package.json",
                            "content": "{ \"workspaces\": [\"apps/*\", \"packages/*\"] }"
                        }
                    ]
                },
                {
                    "phase": 2,
                    "title": "Local Development Pipeline",
                    "time": "1 day",
                    "tasks": [
                        {
                            "task": "Add scripts to turbo.json",
                            "scripts": ["build", "test", "lint", "typecheck"]
                        },
                        {
                            "task": "Set up caching",
                            "description": "Turbo caches build outputs, only rebuilds changed packages"
                        },
                        {
                            "task": "Configure pre-commit hooks",
                            "command": "npx husky install",
                            "hooks": ["lint-staged for formatting", "type-check affected"]
                        }
                    ]
                },
                {
                    "phase": 3,
                    "title": "GitHub Actions Workflows",
                    "time": "2-3 days",
                    "workflows": [
                        {
                            "name": "CI (Pull Requests)",
                            "triggers": ["pull_request"],
                            "steps": [
                                "Checkout",
                                "Setup Node.js with pnpm",
                                "Install dependencies (cached)",
                                "Run affected: lint, typecheck, test, build",
                                "Upload test coverage"
                            ]
                        },
                        {
                            "name": "Deploy Staging",
                            "triggers": ["push to main"],
                            "steps": [
                                "Build affected apps",
                                "Push Docker images to ECR",
                                "Deploy to ECS/EKS staging",
                                "Run E2E tests",
                                "Notify Slack"
                            ]
                        },
                        {
                            "name": "Deploy Production",
                            "triggers": ["release tag"],
                            "steps": [
                                "Build all apps",
                                "Push versioned Docker images",
                                "Deploy to production with rolling update",
                                "Run smoke tests",
                                "Create GitHub release"
                            ]
                        }
                    ]
                },
                {
                    "phase": 4,
                    "title": "AWS Infrastructure",
                    "time": "2-3 days",
                    "tasks": [
                        {
                            "task": "Set up ECR repositories",
                            "description": "One per app: web, api, admin"
                        },
                        {
                            "task": "Configure ECS or EKS",
                            "recommendation": "ECS for simplicity, EKS for Kubernetes ecosystem"
                        },
                        {
                            "task": "Set up environments",
                            "environments": ["staging", "production"],
                            "separation": "Separate AWS accounts or VPCs"
                        },
                        {
                            "task": "Configure secrets",
                            "options": ["AWS Secrets Manager", "GitHub Secrets -> ECS task definition"]
                        },
                        {
                            "task": "Set up CDN for web apps",
                            "services": ["CloudFront", "S3 for static assets"]
                        }
                    ]
                },
                {
                    "phase": 5,
                    "title": "Monitoring and Alerts",
                    "time": "1-2 days",
                    "tasks": [
                        "CloudWatch alarms for ECS metrics",
                        "Error tracking (Sentry)",
                        "APM for performance (Datadog/New Relic)",
                        "Slack integration for deploy notifications",
                        "GitHub deployment environments for tracking"
                    ]
                }
            ],
            "workflow_example": '''name: CI
on:
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for Turbo affected
      
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      
      - name: Lint
        run: pnpm turbo lint --filter=...[origin/main]
      
      - name: Type Check
        run: pnpm turbo typecheck --filter=...[origin/main]
      
      - name: Test
        run: pnpm turbo test --filter=...[origin/main]
      
      - name: Build
        run: pnpm turbo build --filter=...[origin/main]''',
            "best_practices": [
                "Use Turbo's --filter for affected packages only",
                "Cache node_modules and Turbo cache between runs",
                "Separate build and deploy stages",
                "Use GitHub environments for deployment approvals",
                "Pin action versions for reproducibility"
            ]
        }
    },
    
    # Database Schema Design
    {
        "instruction": "I'm designing a database schema for a multi-tenant SaaS application. What should I consider?",
        "response": {
            "action": "multi_step_plan",
            "topic": "Multi-tenant Database Design",
            "decisions_to_make": ["Tenancy model", "Schema design", "Security", "Performance"],
            "phases": [
                {
                    "phase": 1,
                    "title": "Choose Tenancy Model",
                    "options": [
                        {
                            "model": "Shared Database, Shared Schema",
                            "description": "All tenants in same tables with tenant_id column",
                            "pros": ["Simple, cost-effective", "Easy to add tenants", "Shared maintenance"],
                            "cons": ["Risk of data leaks if queries forget tenant filter", "Noisy neighbor issues", "Complex backups per tenant"],
                            "best_for": "Most SaaS apps, especially early stage"
                        },
                        {
                            "model": "Shared Database, Separate Schemas",
                            "description": "Each tenant gets own schema (PostgreSQL) or database (MySQL)",
                            "pros": ["Better isolation", "Easy per-tenant backup/restore", "Can customize per tenant"],
                            "cons": ["More complex migrations", "Connection management", "Limited tenant count"],
                            "best_for": "Medium isolation needs, regulated industries"
                        },
                        {
                            "model": "Separate Databases",
                            "description": "Each tenant gets own database instance",
                            "pros": ["Full isolation", "Independent scaling", "Easy compliance"],
                            "cons": ["Highest cost", "Complex management", "Cross-tenant analytics hard"],
                            "best_for": "Enterprise, high compliance (HIPAA, etc.)"
                        }
                    ],
                    "recommendation": "Start with shared schema + tenant_id. Migrate to separate schemas if needed for compliance or enterprise customers."
                },
                {
                    "phase": 2,
                    "title": "Schema Design (Shared Schema Approach)",
                    "tasks": [
                        {
                            "task": "Create tenant table",
                            "schema": "tenants (id, name, slug, plan, settings, created_at)"
                        },
                        {
                            "task": "Add tenant_id to all tables",
                            "pattern": "Every business table gets tenant_id FK"
                        },
                        {
                            "task": "Composite primary keys or unique constraints",
                            "example": "UNIQUE(tenant_id, email) for users"
                        },
                        {
                            "task": "Index strategy",
                            "rule": "Always include tenant_id in indexes: (tenant_id, other_columns)"
                        }
                    ],
                    "example_schema": '''-- Core tables
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);

-- All queries must filter by tenant_id
SELECT * FROM users WHERE tenant_id = $1 AND email = $2;'''
                },
                {
                    "phase": 3,
                    "title": "Security Implementation",
                    "tasks": [
                        {
                            "task": "Row-Level Security (PostgreSQL)",
                            "code": '''-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Set tenant context in app
SET app.current_tenant = 'tenant-uuid';''',
                            "benefit": "Database enforces isolation even if app code has bugs"
                        },
                        {
                            "task": "Application-level tenant context",
                            "description": "Set tenant from JWT/session, pass to all queries"
                        },
                        {
                            "task": "Query audit",
                            "description": "Log queries that don't include tenant_id"
                        },
                        {
                            "task": "Testing",
                            "tests": [
                                "Verify tenant A can't access tenant B data",
                                "Test RLS policies with different tenant contexts",
                                "Fuzz test API endpoints with cross-tenant IDs"
                            ]
                        }
                    ]
                },
                {
                    "phase": 4,
                    "title": "Performance Optimization",
                    "strategies": [
                        {
                            "strategy": "Partitioning by tenant",
                            "when": "Very large tables (100M+ rows)",
                            "how": "PostgreSQL table partitioning by tenant_id range or hash"
                        },
                        {
                            "strategy": "Connection pooling",
                            "tools": ["PgBouncer", "pgpool-II"],
                            "note": "Critical for shared database model"
                        },
                        {
                            "strategy": "Read replicas per region",
                            "benefit": "Isolate tenant read traffic geographically"
                        },
                        {
                            "strategy": "Caching layer",
                            "implementation": "Redis with tenant-prefixed keys: tenant:{id}:users:{user_id}"
                        },
                        {
                            "strategy": "Query monitoring",
                            "tool": "pg_stat_statements with tenant tracking"
                        }
                    ]
                },
                {
                    "phase": 5,
                    "title": "Operations",
                    "tasks": [
                        {
                            "task": "Migrations",
                            "note": "Test on production-like data, run during low traffic"
                        },
                        {
                            "task": "Tenant data export",
                            "implementation": "COPY with tenant_id filter, pg_dump with --table for schemas"
                        },
                        {
                            "task": "Tenant deletion",
                            "approach": "Soft delete (is_deleted flag) then async hard delete"
                        },
                        {
                            "task": "Monitoring per tenant",
                            "metrics": ["Query count", "Storage usage", "Active users"]
                        }
                    ]
                }
            ]
        }
    },
    
    # Testing Strategy
    {
        "instruction": "How should I structure testing for a large React application?",
        "response": {
            "action": "multi_step_plan",
            "topic": "React Testing Strategy",
            "philosophy": "Testing Trophy: More integration tests, fewer unit and E2E tests",
            "layers": [
                {
                    "layer": "Static Analysis (Foundation)",
                    "coverage": "100% of code",
                    "tools": ["TypeScript", "ESLint", "Prettier"],
                    "what_it_catches": [
                        "Type errors",
                        "Unused variables",
                        "Import errors",
                        "Code style issues"
                    ],
                    "setup": "Runs automatically in IDE and CI"
                },
                {
                    "layer": "Unit Tests",
                    "coverage": "Pure functions, utilities, hooks",
                    "tools": ["Vitest or Jest"],
                    "what_to_test": [
                        "Utility functions (formatDate, calculateTotal)",
                        "Custom hooks in isolation",
                        "Reducers and state logic",
                        "Data transformations"
                    ],
                    "what_not_to_test": [
                        "React component rendering (use integration)",
                        "Implementation details",
                        "Third-party libraries"
                    ],
                    "example": '''// Good unit test
describe('calculateDiscount', () => {
  it('applies percentage discount', () => {
    expect(calculateDiscount(100, { type: 'percent', value: 20 })).toBe(80);
  });
  
  it('caps discount at item price', () => {
    expect(calculateDiscount(50, { type: 'fixed', value: 100 })).toBe(0);
  });
});'''
                },
                {
                    "layer": "Integration Tests (Primary Focus)",
                    "coverage": "Components, features, user flows",
                    "tools": ["React Testing Library", "MSW for API mocking"],
                    "what_to_test": [
                        "Component renders with props",
                        "User interactions (click, type, submit)",
                        "Form validation and submission",
                        "Data fetching and loading states",
                        "Error handling"
                    ],
                    "principles": [
                        "Test behavior, not implementation",
                        "Query by accessible roles, not test IDs",
                        "Simulate real user actions",
                        "Don't test CSS/styling"
                    ],
                    "example": '''// Good integration test
describe('LoginForm', () => {
  it('submits and redirects on success', async () => {
    const { user } = renderWithProviders(<LoginForm />);
    
    await user.type(screen.getByRole('textbox', { name: /email/i }), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    
    expect(await screen.findByText(/welcome/i)).toBeInTheDocument();
  });
  
  it('shows validation errors', async () => {
    const { user } = renderWithProviders(<LoginForm />);
    
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    
    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
  });
});'''
                },
                {
                    "layer": "E2E Tests",
                    "coverage": "Critical user journeys only",
                    "tools": ["Playwright (recommended)", "Cypress"],
                    "what_to_test": [
                        "Sign up / sign in flow",
                        "Main business flows (checkout, booking)",
                        "Payment integration",
                        "Critical happy paths"
                    ],
                    "principles": [
                        "Keep E2E tests minimal (slow, flaky)",
                        "Test against staging, not mocks",
                        "Use test accounts, not production data",
                        "Run in CI, not blocking PR"
                    ],
                    "example": '''// Playwright E2E
test('user can complete checkout', async ({ page }) => {
  await page.goto('/products');
  await page.click('[data-testid="product-1"] >> text=Add to Cart');
  await page.click('text=Checkout');
  
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="card"]', '4242424242424242');
  await page.click('text=Pay Now');
  
  await expect(page.locator('text=Order Confirmed')).toBeVisible();
});'''
                }
            ],
            "folder_structure": '''src/
├── components/
│   └── Button/
│       ├── Button.tsx
│       └── Button.test.tsx       # Integration test
├── hooks/
│   └── useDebounce/
│       ├── useDebounce.ts
│       └── useDebounce.test.ts   # Unit test
├── utils/
│   └── format.ts
│   └── format.test.ts            # Unit tests
├── features/
│   └── checkout/
│       ├── CheckoutPage.tsx
│       └── CheckoutPage.test.tsx # Integration test
tests/
└── e2e/
    └── checkout.spec.ts           # E2E test''',
            "ci_configuration": {
                "on_pr": [
                    "Type check",
                    "Lint",
                    "Unit tests",
                    "Integration tests",
                    "Build"
                ],
                "on_merge": [
                    "All above",
                    "E2E tests against staging"
                ],
                "nightly": [
                    "Full E2E suite",
                    "Performance tests",
                    "Visual regression"
                ]
            },
            "coverage_targets": {
                "unit": "90%+ for utils/hooks",
                "integration": "80%+ for components/features",
                "e2e": "Cover critical paths only"
            }
        }
    },
    
    # Security Audit Plan
    {
        "instruction": "We're preparing for a security audit. What should we check and fix in our web application?",
        "response": {
            "action": "multi_step_plan",
            "topic": "Security Audit Preparation",
            "approach": "OWASP Top 10 + defense in depth",
            "phases": [
                {
                    "phase": 1,
                    "title": "Authentication & Session Security",
                    "checklist": [
                        {
                            "item": "Password requirements",
                            "check": "Min 12 chars, complexity rules, bcrypt/argon2 hashing"
                        },
                        {
                            "item": "MFA support",
                            "check": "TOTP or WebAuthn available, enforced for admins"
                        },
                        {
                            "item": "Session management",
                            "checks": [
                                "Secure, HttpOnly, SameSite cookies",
                                "Session timeout (idle and absolute)",
                                "Session invalidation on password change",
                                "Prevent session fixation"
                            ]
                        },
                        {
                            "item": "JWT security",
                            "checks": [
                                "Short expiration (15-60 min)",
                                "Refresh token rotation",
                                "Proper signature verification",
                                "No sensitive data in payload"
                            ]
                        },
                        {
                            "item": "Brute force protection",
                            "check": "Rate limiting, account lockout, CAPTCHA after failures"
                        }
                    ]
                },
                {
                    "phase": 2,
                    "title": "Authorization & Access Control",
                    "checklist": [
                        {
                            "item": "RBAC implementation",
                            "check": "Roles defined, permissions enforced server-side"
                        },
                        {
                            "item": "IDOR protection",
                            "check": "All object access validates user ownership/permission"
                        },
                        {
                            "item": "API authorization",
                            "check": "Every endpoint has auth check, not just frontend"
                        },
                        {
                            "item": "Admin functions",
                            "check": "Separate admin routes, additional auth for sensitive ops"
                        }
                    ]
                },
                {
                    "phase": 3,
                    "title": "Input Validation & Injection",
                    "checklist": [
                        {
                            "item": "SQL Injection",
                            "check": "Parameterized queries everywhere, no string concatenation"
                        },
                        {
                            "item": "XSS Prevention",
                            "checks": [
                                "Output encoding (React does this by default)",
                                "CSP headers configured",
                                "No dangerouslySetInnerHTML with user input"
                            ]
                        },
                        {
                            "item": "CSRF Protection",
                            "check": "CSRF tokens on state-changing requests, SameSite cookies"
                        },
                        {
                            "item": "File uploads",
                            "checks": [
                                "Type validation (magic bytes, not just extension)",
                                "Size limits",
                                "Virus scanning",
                                "Store outside webroot"
                            ]
                        },
                        {
                            "item": "Input sanitization",
                            "check": "Server-side validation for all inputs, whitelist approach"
                        }
                    ]
                },
                {
                    "phase": 4,
                    "title": "Data Protection",
                    "checklist": [
                        {
                            "item": "Encryption in transit",
                            "check": "TLS 1.2+, HSTS header, no mixed content"
                        },
                        {
                            "item": "Encryption at rest",
                            "check": "Database encryption, encrypted backups"
                        },
                        {
                            "item": "Secrets management",
                            "check": "No secrets in code, use vault/secrets manager"
                        },
                        {
                            "item": "PII handling",
                            "check": "Masked in logs, encrypted fields for sensitive data"
                        },
                        {
                            "item": "Data retention",
                            "check": "Defined retention policy, automated deletion"
                        }
                    ]
                },
                {
                    "phase": 5,
                    "title": "Infrastructure & Dependencies",
                    "checklist": [
                        {
                            "item": "Dependency vulnerabilities",
                            "tools": ["npm audit", "Snyk", "Dependabot"],
                            "action": "Run daily, fix critical immediately"
                        },
                        {
                            "item": "Container security",
                            "checks": [
                                "Non-root user",
                                "Minimal base image",
                                "No secrets in image",
                                "Image scanning"
                            ]
                        },
                        {
                            "item": "Network security",
                            "checks": [
                                "Firewall rules (deny by default)",
                                "VPC for internal services",
                                "No public database access"
                            ]
                        },
                        {
                            "item": "Security headers",
                            "headers": [
                                "Content-Security-Policy",
                                "X-Content-Type-Options: nosniff",
                                "X-Frame-Options: DENY",
                                "Referrer-Policy: strict-origin"
                            ]
                        }
                    ]
                },
                {
                    "phase": 6,
                    "title": "Monitoring & Incident Response",
                    "checklist": [
                        {
                            "item": "Security logging",
                            "log": ["Auth events", "Admin actions", "Failed access", "Data exports"]
                        },
                        {
                            "item": "Alerting",
                            "alerts": ["Brute force attempts", "Unusual data access", "Config changes"]
                        },
                        {
                            "item": "Incident response plan",
                            "check": "Documented, tested, contacts defined"
                        }
                    ]
                }
            ],
            "tools_to_run": [
                "OWASP ZAP - automated security scanning",
                "npm audit / Snyk - dependency vulnerabilities",
                "Semgrep - static analysis for security patterns",
                "Burp Suite - manual penetration testing"
            ],
            "documentation_needed": [
                "Security architecture diagram",
                "Data flow diagram (where PII goes)",
                "Access control matrix",
                "Incident response runbook"
            ]
        }
    },
    
    # API Design Planning
    {
        "instruction": "I'm designing a REST API for a task management app. Help me plan the endpoints and structure.",
        "response": {
            "action": "multi_step_plan",
            "topic": "REST API Design",
            "principles": [
                "Resource-oriented URLs",
                "Proper HTTP methods",
                "Consistent response format",
                "Versioning from day one"
            ],
            "design": {
                "base_url": "/api/v1",
                "resources": [
                    {
                        "resource": "Projects",
                        "endpoints": [
                            {"method": "GET", "path": "/projects", "description": "List user's projects", "query": "?page=1&limit=20&status=active"},
                            {"method": "POST", "path": "/projects", "description": "Create project", "body": {"name": "required", "description": "optional"}},
                            {"method": "GET", "path": "/projects/:id", "description": "Get project details"},
                            {"method": "PATCH", "path": "/projects/:id", "description": "Update project"},
                            {"method": "DELETE", "path": "/projects/:id", "description": "Archive project (soft delete)"}
                        ]
                    },
                    {
                        "resource": "Tasks",
                        "endpoints": [
                            {"method": "GET", "path": "/projects/:projectId/tasks", "description": "List tasks in project", "query": "?status=todo,in_progress&assignee=user_id"},
                            {"method": "POST", "path": "/projects/:projectId/tasks", "description": "Create task"},
                            {"method": "GET", "path": "/tasks/:id", "description": "Get task details"},
                            {"method": "PATCH", "path": "/tasks/:id", "description": "Update task"},
                            {"method": "DELETE", "path": "/tasks/:id", "description": "Delete task"},
                            {"method": "POST", "path": "/tasks/:id/assign", "description": "Assign task to user"},
                            {"method": "POST", "path": "/tasks/:id/status", "description": "Change task status"}
                        ]
                    },
                    {
                        "resource": "Comments",
                        "endpoints": [
                            {"method": "GET", "path": "/tasks/:taskId/comments", "description": "List task comments"},
                            {"method": "POST", "path": "/tasks/:taskId/comments", "description": "Add comment"},
                            {"method": "PATCH", "path": "/comments/:id", "description": "Edit comment"},
                            {"method": "DELETE", "path": "/comments/:id", "description": "Delete comment"}
                        ]
                    },
                    {
                        "resource": "Users",
                        "endpoints": [
                            {"method": "GET", "path": "/users/me", "description": "Current user profile"},
                            {"method": "PATCH", "path": "/users/me", "description": "Update profile"},
                            {"method": "GET", "path": "/projects/:projectId/members", "description": "List project members"},
                            {"method": "POST", "path": "/projects/:projectId/members", "description": "Add member to project"}
                        ]
                    }
                ],
                "authentication": {
                    "method": "Bearer token (JWT)",
                    "endpoints": [
                        {"method": "POST", "path": "/auth/register", "description": "Create account"},
                        {"method": "POST", "path": "/auth/login", "description": "Get access token"},
                        {"method": "POST", "path": "/auth/refresh", "description": "Refresh access token"},
                        {"method": "POST", "path": "/auth/logout", "description": "Invalidate tokens"}
                    ]
                }
            },
            "response_format": {
                "success": {
                    "example": '''// Single resource
{
    "data": {
        "id": "task_123",
        "title": "Implement API",
        "status": "in_progress",
        "project": { "id": "proj_456", "name": "Backend" },
        "assignee": { "id": "user_789", "name": "John" },
        "createdAt": "2024-01-15T10:00:00Z"
    }
}

// Collection
{
    "data": [...],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 45,
        "totalPages": 3
    }
}'''
                },
                "error": {
                    "example": '''{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request data",
        "details": [
            { "field": "title", "message": "Title is required" },
            { "field": "dueDate", "message": "Must be a future date" }
        ]
    }
}'''
                },
                "http_status_codes": {
                    "200": "Success",
                    "201": "Created",
                    "204": "No Content (DELETE success)",
                    "400": "Bad Request (validation error)",
                    "401": "Unauthorized (no/invalid token)",
                    "403": "Forbidden (no permission)",
                    "404": "Not Found",
                    "409": "Conflict (duplicate)",
                    "422": "Unprocessable Entity",
                    "429": "Too Many Requests",
                    "500": "Internal Server Error"
                }
            },
            "best_practices": [
                "Use plural nouns for resources (/tasks, not /task)",
                "Use query params for filtering, not path params",
                "Include related resources via ?include=assignee,project",
                "Support partial updates with PATCH",
                "Use 204 for DELETE, not 200 with body",
                "Rate limit all endpoints",
                "Document with OpenAPI/Swagger"
            ],
            "versioning_strategy": {
                "approach": "URL versioning (/api/v1/...)",
                "when_to_version": [
                    "Breaking changes to response format",
                    "Removing fields",
                    "Changing authentication"
                ],
                "migration": "Support v1 for 6-12 months after v2 launch"
            }
        }
    },
    
    # Infrastructure Setup
    {
        "instruction": "How do I set up a production-ready Kubernetes cluster for our application?",
        "response": {
            "action": "multi_step_plan",
            "topic": "Production Kubernetes Setup",
            "estimated_time": "2-4 weeks",
            "phases": [
                {
                    "phase": 1,
                    "title": "Cluster Provisioning",
                    "time": "2-3 days",
                    "options": {
                        "managed": {
                            "services": ["EKS (AWS)", "GKE (Google)", "AKS (Azure)"],
                            "recommendation": "EKS for AWS shops, GKE for best K8s experience",
                            "benefits": ["Control plane managed", "Automatic updates", "Cloud integrations"]
                        },
                        "self_managed": {
                            "tools": ["kubeadm", "kops", "Rancher"],
                            "when": "Special compliance needs or cost optimization"
                        }
                    },
                    "sizing": {
                        "node_pools": [
                            {"name": "system", "type": "t3.medium", "count": "2-3", "purpose": "System workloads"},
                            {"name": "app", "type": "t3.large", "count": "3-10", "purpose": "Application pods"},
                            {"name": "spot", "type": "t3.large", "count": "0-10", "purpose": "Burst capacity, stateless workloads"}
                        ],
                        "considerations": [
                            "Start small, scale based on metrics",
                            "Use spot instances for cost savings",
                            "Separate node pools for different workload types"
                        ]
                    }
                },
                {
                    "phase": 2,
                    "title": "Networking",
                    "time": "2-3 days",
                    "components": [
                        {
                            "component": "Ingress Controller",
                            "options": ["NGINX Ingress", "AWS ALB Ingress", "Traefik"],
                            "recommendation": "NGINX for flexibility, ALB for AWS-native"
                        },
                        {
                            "component": "Service Mesh (optional)",
                            "options": ["Istio", "Linkerd"],
                            "when": "Need mTLS, traffic management, observability"
                        },
                        {
                            "component": "Network Policies",
                            "description": "Deny by default, allow specific traffic"
                        },
                        {
                            "component": "DNS",
                            "setup": "ExternalDNS for automatic DNS record management"
                        }
                    ]
                },
                {
                    "phase": 3,
                    "title": "Security",
                    "time": "3-4 days",
                    "tasks": [
                        {
                            "task": "RBAC Configuration",
                            "description": "Define roles for developers, CI/CD, services"
                        },
                        {
                            "task": "Pod Security",
                            "policies": [
                                "Non-root containers",
                                "Read-only root filesystem",
                                "Drop capabilities",
                                "Resource limits"
                            ]
                        },
                        {
                            "task": "Secrets Management",
                            "options": ["External Secrets Operator + AWS Secrets Manager", "Vault", "Sealed Secrets"]
                        },
                        {
                            "task": "Image Security",
                            "practices": [
                                "Private registry (ECR)",
                                "Image scanning (Trivy, Snyk)",
                                "Signed images"
                            ]
                        },
                        {
                            "task": "Audit Logging",
                            "description": "Enable Kubernetes audit logs, send to SIEM"
                        }
                    ]
                },
                {
                    "phase": 4,
                    "title": "Observability",
                    "time": "2-3 days",
                    "stack": {
                        "metrics": {
                            "tool": "Prometheus + Grafana",
                            "setup": "kube-prometheus-stack Helm chart",
                            "dashboards": ["Cluster overview", "Node health", "Pod metrics", "App-specific"]
                        },
                        "logging": {
                            "options": ["ELK Stack", "Loki + Grafana", "CloudWatch"],
                            "collection": "Fluentd or Fluent Bit DaemonSet"
                        },
                        "tracing": {
                            "tools": ["Jaeger", "Zipkin", "AWS X-Ray"],
                            "instrumentation": "OpenTelemetry SDK in apps"
                        },
                        "alerting": {
                            "tool": "Alertmanager",
                            "alerts": ["Node down", "Pod crash loops", "High CPU/memory", "Certificate expiry"]
                        }
                    }
                },
                {
                    "phase": 5,
                    "title": "CI/CD Integration",
                    "time": "2-3 days",
                    "components": [
                        {
                            "component": "GitOps (Recommended)",
                            "tools": ["ArgoCD", "Flux"],
                            "flow": "Git commit -> ArgoCD syncs -> K8s updated"
                        },
                        {
                            "component": "Image Pipeline",
                            "flow": "Build -> Scan -> Push to ECR -> Update manifests"
                        },
                        {
                            "component": "Deployment Strategies",
                            "options": [
                                "Rolling update (default)",
                                "Blue/Green with service switch",
                                "Canary with Istio or Flagger"
                            ]
                        }
                    ]
                },
                {
                    "phase": 6,
                    "title": "Reliability",
                    "time": "2-3 days",
                    "practices": [
                        {
                            "practice": "Pod Disruption Budgets",
                            "description": "Ensure minimum pods during upgrades"
                        },
                        {
                            "practice": "Horizontal Pod Autoscaler",
                            "description": "Scale based on CPU, memory, or custom metrics"
                        },
                        {
                            "practice": "Cluster Autoscaler",
                            "description": "Add/remove nodes based on pending pods"
                        },
                        {
                            "practice": "Multi-AZ deployment",
                            "description": "Spread nodes and pods across availability zones"
                        },
                        {
                            "practice": "Backup & DR",
                            "tool": "Velero for cluster backup and restore"
                        }
                    ]
                }
            ],
            "essential_manifests": [
                "Namespace per environment/team",
                "ResourceQuotas per namespace",
                "LimitRanges for default container limits",
                "NetworkPolicies for traffic control",
                "PodSecurityPolicies/Standards"
            ]
        }
    },
]


def generate_examples() -> List[Dict]:
    """Generate all project planning training examples."""
    examples = []
    
    for example in PROJECT_PLANNING_EXAMPLES:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": example["instruction"],
            "response": json.dumps(example["response"], indent=2)
        })
    
    return examples


def save_examples(examples: List[Dict], filename: str = "project_planning.jsonl"):
    """Save examples to JSONL file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"Generated {len(examples)} project planning examples -> {output_path}")
    return examples


if __name__ == "__main__":
    examples = generate_examples()
    save_examples(examples)
