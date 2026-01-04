#!/usr/bin/env python3
"""
Multi-Step Workflows Training Data Generator
Target: ~300 examples for complex, cross-domain development tasks
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for software development.
You help with complex, multi-step development workflows that span multiple tools and technologies."""

# =============================================================================
# COMPLEX WORKFLOW TASKS
# =============================================================================

FULL_STACK_WORKFLOWS = [
    {
        "instruction": "Set up a full-stack application with React frontend and Node.js API",
        "steps": [
            "Create project root directory and initialize git",
            "Create /frontend with create-react-app or Vite",
            "Create /backend with Express.js scaffold",
            "Set up TypeScript in both frontend and backend",
            "Configure ESLint and Prettier with shared config",
            "Set up environment variables (.env files)",
            "Create Docker Compose for local development",
            "Add database service (PostgreSQL) to compose",
            "Set up API routes and React Router",
            "Configure CORS and proxy for development",
            "Add authentication (JWT) to backend",
            "Create auth context and hooks in React",
            "Set up database migrations with Prisma or Knex",
            "Add API client with Axios/React Query",
            "Configure testing: Jest for both, React Testing Library",
            "Create GitHub Actions CI pipeline"
        ],
        "context": "Full-stack setup from scratch"
    },
    {
        "instruction": "Debug production issue: users can't login",
        "steps": [
            "Check monitoring/alerting for error spikes",
            "Review recent deployments for changes",
            "Check API health endpoints",
            "Examine error logs for auth service",
            "Verify database connections are healthy",
            "Check if session/token store (Redis) is accessible",
            "Test login flow manually in staging",
            "Check for certificate expiration (SSL/JWT)",
            "Review rate limiting rules",
            "Check if auth provider (OAuth) is up",
            "Examine network/firewall changes",
            "Roll back if recent deployment is cause",
            "Communicate status to stakeholders",
            "Document incident and create post-mortem"
        ],
        "context": "Production incident response"
    },
    {
        "instruction": "Implement CI/CD pipeline for microservices",
        "steps": [
            "Analyze service dependencies and build order",
            "Create Dockerfiles for each service",
            "Set up container registry (ECR, GCR, Docker Hub)",
            "Create base GitHub Actions workflow",
            "Add linting and type checking steps",
            "Add unit test jobs for each service",
            "Add integration test jobs",
            "Build and push Docker images",
            "Set up staging environment in Kubernetes",
            "Add deployment to staging on PR merge",
            "Add smoke tests post-deployment",
            "Create manual approval for production",
            "Add production deployment step",
            "Set up rollback mechanism",
            "Configure monitoring and alerting",
            "Document deployment process"
        ],
        "context": "DevOps pipeline creation"
    },
    {
        "instruction": "Build a real-time collaborative document editor",
        "steps": [
            "Design data model with operational transforms or CRDTs",
            "Set up WebSocket server with Socket.io or native WS",
            "Implement document state synchronization protocol",
            "Create cursor presence system for collaborators",
            "Build rich text editor UI with Slate.js or ProseMirror",
            "Implement operational transform algorithm",
            "Add conflict resolution for concurrent edits",
            "Store document snapshots periodically",
            "Implement undo/redo history per user",
            "Add user presence indicators",
            "Build document sharing and permissions system",
            "Add offline support with sync on reconnect",
            "Implement document versioning",
            "Test with multiple concurrent users",
            "Optimize for low latency"
        ],
        "context": "Real-time collaboration"
    },
    {
        "instruction": "Implement feature flags system",
        "steps": [
            "Design feature flag data model (name, variants, rules)",
            "Create feature flag admin interface",
            "Build evaluation engine for targeting rules",
            "Implement SDK for frontend feature checks",
            "Create server-side middleware for backend",
            "Add percentage rollout capability",
            "Implement user targeting (by ID, email, attributes)",
            "Add A/B testing variant support",
            "Create metrics tracking for flags",
            "Build flag override for testing/debugging",
            "Implement flag lifecycle (create, archive, delete)",
            "Add audit logging for changes",
            "Set up local evaluation caching",
            "Document flag naming conventions",
            "Train team on flag usage"
        ],
        "context": "Feature management"
    },
    {
        "instruction": "Implement multi-tenant SaaS architecture",
        "steps": [
            "Choose tenant isolation model (shared DB, schema per tenant, DB per tenant)",
            "Design tenant provisioning flow",
            "Create tenant identification (subdomain, header, or token)",
            "Implement request middleware to inject tenant context",
            "Modify database queries to filter by tenant",
            "Add tenant-aware caching layer",
            "Create tenant admin portal",
            "Implement usage metering per tenant",
            "Build billing integration",
            "Add tenant data export functionality",
            "Implement tenant deletion with data cleanup",
            "Add cross-tenant analytics (aggregated)",
            "Set up tenant-specific rate limiting",
            "Configure monitoring per tenant",
            "Document operational procedures"
        ],
        "context": "SaaS architecture"
    },
    {
        "instruction": "Build event-driven architecture with message queues",
        "steps": [
            "Choose message broker (RabbitMQ, Kafka, SQS)",
            "Design event schema and naming conventions",
            "Create event publishing service",
            "Implement event consumers with idempotency",
            "Add dead letter queue handling",
            "Implement retry logic with exponential backoff",
            "Create event schema registry",
            "Add event versioning strategy",
            "Implement saga pattern for distributed transactions",
            "Build event replay capability",
            "Add tracing across event boundaries",
            "Set up monitoring for queue depth",
            "Create alerting for consumer lag",
            "Document event contracts",
            "Test failure scenarios"
        ],
        "context": "Event-driven architecture"
    },
    {
        "instruction": "Implement GraphQL API with subscriptions",
        "steps": [
            "Set up Apollo Server or GraphQL Yoga",
            "Define schema with SDL or code-first",
            "Implement Query resolvers",
            "Add Mutation resolvers with validation",
            "Set up DataLoader for batching",
            "Implement authentication middleware",
            "Add field-level authorization",
            "Create Subscription resolvers",
            "Set up WebSocket server for subscriptions",
            "Implement PubSub for real-time events",
            "Add query complexity limiting",
            "Implement persisted queries",
            "Set up schema stitching or federation",
            "Generate TypeScript types from schema",
            "Document API with GraphQL Playground"
        ],
        "context": "GraphQL implementation"
    },
    # === EXPANDED FULL-STACK WORKFLOWS ===
    {
        "instruction": "Build a notification system (push, email, SMS)",
        "steps": [
            "Design notification data model",
            "Create notification preferences per user",
            "Build notification queue with priorities",
            "Implement email provider integration (SendGrid, SES)",
            "Add push notification support (FCM, APNS)",
            "Integrate SMS provider (Twilio)",
            "Create notification templates",
            "Implement template variable substitution",
            "Add notification batching/digest option",
            "Build notification center UI",
            "Track notification delivery status",
            "Handle unsubscribe/preferences",
            "Add rate limiting per user",
            "Set up delivery monitoring",
            "Document notification types"
        ],
        "context": "Notification system"
    },
    {
        "instruction": "Implement search functionality with Elasticsearch",
        "steps": [
            "Set up Elasticsearch cluster",
            "Design index mappings for documents",
            "Create data sync pipeline from database",
            "Implement incremental index updates",
            "Build search API with filters and facets",
            "Add autocomplete/typeahead",
            "Implement fuzzy matching and synonyms",
            "Create relevance scoring tuning",
            "Add highlighting of search terms",
            "Implement pagination with scroll API",
            "Build search analytics tracking",
            "Set up index maintenance jobs",
            "Monitor cluster health and performance",
            "Document search configuration"
        ],
        "context": "Search implementation"
    },
    {
        "instruction": "Build file upload and processing pipeline",
        "steps": [
            "Design file storage architecture (S3, GCS)",
            "Implement secure upload endpoints",
            "Add file type validation and virus scanning",
            "Create thumbnail generation for images",
            "Implement video transcoding pipeline",
            "Build progress tracking for large uploads",
            "Add resumable uploads support",
            "Implement access control for files",
            "Create signed URLs for downloads",
            "Build file preview functionality",
            "Add metadata extraction",
            "Set up CDN for file delivery",
            "Implement file expiration/cleanup",
            "Document storage costs and limits"
        ],
        "context": "File processing"
    },
    {
        "instruction": "Implement payment processing integration",
        "steps": [
            "Choose payment processor (Stripe, PayPal)",
            "Design payment data model",
            "Implement webhook handlers",
            "Add idempotency for payment operations",
            "Create checkout flow",
            "Implement subscription management",
            "Handle payment failures and retries",
            "Add invoice generation",
            "Implement refund functionality",
            "Create payment analytics",
            "Set up PCI compliance measures",
            "Add fraud detection rules",
            "Document payment flows",
            "Test with sandbox environment"
        ],
        "context": "Payment integration"
    },
    {
        "instruction": "Build admin dashboard with analytics",
        "steps": [
            "Design dashboard layout and navigation",
            "Create role-based access control",
            "Build user management interface",
            "Implement data visualization charts",
            "Add real-time metrics updates",
            "Create export functionality (CSV, PDF)",
            "Build audit log viewer",
            "Implement search and filtering",
            "Add date range selectors",
            "Create scheduled report generation",
            "Implement alert configuration UI",
            "Build system health dashboard",
            "Add performance metrics display",
            "Document dashboard features"
        ],
        "context": "Admin dashboard"
    },
    {
        "instruction": "Implement internationalization (i18n)",
        "steps": [
            "Choose i18n library (react-intl, i18next)",
            "Extract translatable strings",
            "Set up translation files structure",
            "Implement language detection",
            "Create language switcher UI",
            "Handle pluralization rules",
            "Implement date/number formatting",
            "Set up RTL support for Arabic/Hebrew",
            "Create translation workflow",
            "Integrate with translation service",
            "Add missing translation detection",
            "Test with all supported languages",
            "Document translation process",
            "Train team on i18n patterns"
        ],
        "context": "Internationalization"
    },
    {
        "instruction": "Build API rate limiting and quota management",
        "steps": [
            "Design rate limiting architecture",
            "Choose algorithm (token bucket, sliding window)",
            "Implement distributed rate limiting with Redis",
            "Configure per-endpoint limits",
            "Add tier-based quotas per user",
            "Create quota usage tracking",
            "Implement overage handling",
            "Build quota dashboard",
            "Add rate limit headers to responses",
            "Create quota reset scheduling",
            "Implement alerting for quota exhaustion",
            "Document rate limits in API docs",
            "Test under high load"
        ],
        "context": "API quota management"
    },
    # === EXPANDED WORKFLOW EXAMPLES ===
    {
        "instruction": "Implement OAuth2 single sign-on with multiple providers",
        "steps": [
            "Research OAuth2/OIDC specifications",
            "Set up Google OAuth credentials",
            "Configure GitHub OAuth application",
            "Add Microsoft/Azure AD credentials",
            "Choose auth library (passport.js, next-auth)",
            "Implement OAuth callback handlers",
            "Create user linking for multiple providers",
            "Handle account merging scenarios",
            "Store refresh tokens securely",
            "Implement token refresh logic",
            "Add logout from all providers",
            "Create provider management UI",
            "Implement error handling for OAuth failures",
            "Add audit logging for auth events",
            "Test all provider flows end-to-end"
        ],
        "context": "SSO implementation"
    },
    {
        "instruction": "Build a background job processing system",
        "steps": [
            "Choose job queue (BullMQ, Agenda, Celery)",
            "Set up Redis/RabbitMQ for queue backend",
            "Design job schema and priority levels",
            "Create job producer service",
            "Implement worker processes",
            "Add job retry logic with backoff",
            "Implement dead letter queue handling",
            "Create job progress tracking",
            "Build job monitoring dashboard",
            "Add job cancellation support",
            "Implement rate limiting per job type",
            "Add job scheduling (cron-like)",
            "Create alerting for failed jobs",
            "Implement job result storage",
            "Document job types and usage"
        ],
        "context": "Job queue system"
    },
    {
        "instruction": "Implement a comprehensive logging and observability stack",
        "steps": [
            "Choose logging framework (Winston, Bunyan, Pino)",
            "Define log levels and formatting standards",
            "Add structured logging with correlation IDs",
            "Set up log aggregation (ELK, Loki)",
            "Configure log shipping from applications",
            "Implement distributed tracing (Jaeger, Zipkin)",
            "Add metrics collection (Prometheus)",
            "Create Grafana dashboards",
            "Set up alerting rules",
            "Add error tracking (Sentry)",
            "Implement log retention policies",
            "Create runbooks for common alerts",
            "Add health check endpoints",
            "Document observability practices",
            "Train team on dashboard usage"
        ],
        "context": "Observability stack"
    },
    {
        "instruction": "Build a content management system with versioning",
        "steps": [
            "Design content model (pages, blocks, media)",
            "Create content versioning data model",
            "Implement draft/published workflow",
            "Build rich text editor integration",
            "Add media library with upload handling",
            "Implement content scheduling",
            "Create content preview functionality",
            "Add content localization support",
            "Build content search with full-text",
            "Implement content permissions/roles",
            "Create revision history viewer",
            "Add content rollback capability",
            "Implement content export/import",
            "Build content analytics",
            "Document content authoring workflow"
        ],
        "context": "CMS development"
    },
    {
        "instruction": "Implement WebSocket-based real-time updates",
        "steps": [
            "Choose WebSocket library (Socket.io, ws)",
            "Design event types and message format",
            "Create WebSocket server with auth",
            "Implement connection state management",
            "Add room/channel subscription logic",
            "Create message broadcasting service",
            "Implement message acknowledgment",
            "Add reconnection handling on client",
            "Create presence system (online/offline)",
            "Implement message queuing for offline users",
            "Add typing indicators",
            "Create horizontal scaling with Redis adapter",
            "Implement rate limiting per connection",
            "Add monitoring for connections",
            "Test with many concurrent connections"
        ],
        "context": "Real-time WebSocket"
    },
    {
        "instruction": "Build a comprehensive API gateway",
        "steps": [
            "Choose API gateway solution (Kong, AWS API Gateway)",
            "Design routing architecture",
            "Implement request authentication",
            "Add request validation middleware",
            "Create rate limiting rules",
            "Implement request/response transformation",
            "Add caching layer",
            "Create circuit breaker patterns",
            "Implement load balancing",
            "Add API versioning support",
            "Create API analytics collection",
            "Implement IP whitelisting/blacklisting",
            "Add request logging and tracing",
            "Create developer portal",
            "Document all gateway configurations"
        ],
        "context": "API gateway"
    },
    {
        "instruction": "Implement a recommendation engine",
        "steps": [
            "Analyze data for recommendation basis",
            "Choose recommendation algorithm approach",
            "Design data pipeline for training",
            "Implement collaborative filtering",
            "Add content-based filtering",
            "Create hybrid recommendation system",
            "Build model training pipeline",
            "Implement real-time scoring service",
            "Add A/B testing for recommendations",
            "Create feedback collection system",
            "Implement recommendation caching",
            "Build monitoring for recommendation quality",
            "Add diversity and fairness controls",
            "Create recommendation explanation",
            "Document model performance metrics"
        ],
        "context": "Recommendation system"
    },
    {
        "instruction": "Build a document generation and PDF export system",
        "steps": [
            "Choose PDF generation library (PDFKit, Puppeteer)",
            "Design document template system",
            "Create template editor with preview",
            "Implement dynamic data binding",
            "Add support for images and charts",
            "Create page layout system",
            "Implement table generation",
            "Add PDF signing capability",
            "Create batch document generation",
            "Implement document storage and retrieval",
            "Add watermarking support",
            "Create email delivery integration",
            "Implement document versioning",
            "Add accessibility compliance",
            "Document template authoring"
        ],
        "context": "Document generation"
    },
    {
        "instruction": "Implement a multi-region deployment strategy",
        "steps": [
            "Analyze traffic patterns and latency needs",
            "Choose multi-region database strategy",
            "Design data replication architecture",
            "Implement CDN for static assets",
            "Create regional container deployments",
            "Set up DNS-based geo-routing",
            "Implement session affinity handling",
            "Create cross-region failover",
            "Build deployment pipeline for all regions",
            "Implement data consistency strategy",
            "Add regional health monitoring",
            "Create disaster recovery procedures",
            "Test failover scenarios",
            "Document runbooks for incidents",
            "Monitor latency per region"
        ],
        "context": "Multi-region deployment"
    },
    {
        "instruction": "Build a workflow automation engine",
        "steps": [
            "Design workflow definition format (DAG)",
            "Create workflow builder UI",
            "Implement workflow execution engine",
            "Add condition and branching logic",
            "Create action library (HTTP, email, etc.)",
            "Implement parallel execution",
            "Add workflow variables and context",
            "Create workflow triggers (webhook, schedule)",
            "Implement workflow versioning",
            "Add execution history and logs",
            "Create error handling and retry",
            "Implement workflow pause/resume",
            "Add workflow templates",
            "Create monitoring dashboard",
            "Document workflow authoring"
        ],
        "context": "Workflow automation"
    },
]

DATABASE_WORKFLOWS = [
    {
        "instruction": "Migrate from MongoDB to PostgreSQL",
        "steps": [
            "Audit MongoDB collections and document structure",
            "Design PostgreSQL schema (normalize data)",
            "Set up PostgreSQL with Docker for development",
            "Create migration scripts for schema",
            "Write data transformation scripts",
            "Export MongoDB data as JSON",
            "Transform and import into PostgreSQL",
            "Update application data access layer",
            "Create repository pattern for database agnostic code",
            "Update queries (MongoDB → SQL)",
            "Add indexes based on query patterns",
            "Test thoroughly with production-like data",
            "Plan cutover window",
            "Execute migration with rollback plan",
            "Monitor for issues post-migration"
        ],
        "context": "Database migration"
    },
    {
        "instruction": "Implement database sharding for scale",
        "steps": [
            "Identify sharding requirements (data growth, query patterns)",
            "Choose shard key (must be in most queries)",
            "Design shard mapping strategy (hash, range)",
            "Set up additional database servers",
            "Create shard router/proxy layer",
            "Update application to use router",
            "Plan data distribution across shards",
            "Write resharding scripts",
            "Migrate existing data to sharded setup",
            "Update cross-shard queries (aggregation)",
            "Set up shard-aware backups",
            "Test failover scenarios",
            "Monitor shard balance",
            "Document operational procedures"
        ],
        "context": "Database scaling"
    },
    {
        "instruction": "Set up database replication for high availability",
        "steps": [
            "Provision primary and replica database servers",
            "Configure streaming replication on primary",
            "Set up pg_hba.conf for replication connections",
            "Initialize replica from base backup",
            "Configure recovery.conf on replica",
            "Verify replication is working",
            "Set up monitoring for replication lag",
            "Configure connection pooler (PgBouncer)",
            "Route read queries to replicas",
            "Update application for read/write split",
            "Test failover procedure",
            "Document manual failover steps",
            "Set up automated failover (Patroni)",
            "Configure alerting for lag/failures"
        ],
        "context": "Database high availability"
    },
    {
        "instruction": "Implement database backup and disaster recovery",
        "steps": [
            "Design backup strategy (full, incremental, continuous)",
            "Set up automated daily backups",
            "Configure point-in-time recovery with WAL archiving",
            "Store backups in separate region/provider",
            "Encrypt backups at rest",
            "Test backup restoration regularly",
            "Document RTO and RPO requirements",
            "Create disaster recovery runbook",
            "Set up backup monitoring and alerting",
            "Implement backup retention policy",
            "Test cross-region recovery",
            "Train team on recovery procedures",
            "Schedule quarterly DR drills"
        ],
        "context": "Backup and recovery"
    },
    {
        "instruction": "Optimize slow database queries",
        "steps": [
            "Enable slow query logging",
            "Identify top slow queries from logs",
            "Analyze queries with EXPLAIN ANALYZE",
            "Check for missing indexes",
            "Look for sequential scans on large tables",
            "Identify N+1 query patterns",
            "Add covering indexes where beneficial",
            "Consider partial indexes for filtered queries",
            "Rewrite queries to use CTEs or subqueries efficiently",
            "Check for statistics freshness (ANALYZE)",
            "Consider query plan caching",
            "Add query result caching (Redis)",
            "Monitor query performance post-optimization",
            "Set up query performance tracking"
        ],
        "context": "Query optimization"
    },
    # === EXPANDED DATABASE WORKFLOWS ===
    {
        "instruction": "Implement database connection pooling",
        "steps": [
            "Audit current connection patterns",
            "Choose pooling solution (PgBouncer, built-in)",
            "Configure pool size based on DB limits",
            "Set up connection timeout parameters",
            "Implement connection health checks",
            "Configure prepared statement mode",
            "Set up pool monitoring metrics",
            "Update application connection strings",
            "Test under load conditions",
            "Configure graceful connection release",
            "Set up alerts for pool exhaustion",
            "Document pool configuration",
            "Train team on connection management"
        ],
        "context": "Connection pooling"
    },
    {
        "instruction": "Set up database audit logging",
        "steps": [
            "Define audit requirements (what to log)",
            "Enable PostgreSQL audit extension (pgaudit)",
            "Configure audit log categories",
            "Set up log shipping to central system",
            "Create audit log retention policy",
            "Build audit query interface",
            "Set up alerts for suspicious activity",
            "Implement log analysis dashboards",
            "Configure role-based audit rules",
            "Test audit log completeness",
            "Document compliance requirements",
            "Schedule regular audit reviews"
        ],
        "context": "Database auditing"
    },
    {
        "instruction": "Implement database schema versioning",
        "steps": [
            "Choose migration tool (Flyway, Liquibase, Knex)",
            "Create baseline migration from current schema",
            "Set up migration directory structure",
            "Create naming convention for migrations",
            "Implement up and down migrations",
            "Add migration testing in CI pipeline",
            "Configure migration for multiple environments",
            "Create rollback procedures",
            "Implement data migrations separately",
            "Set up migration locking",
            "Document migration workflow",
            "Train team on migration process"
        ],
        "context": "Schema management"
    },
    {
        "instruction": "Implement multi-tenant database architecture",
        "steps": [
            "Choose isolation model (shared tables, shared schema, separate schemas, separate databases)",
            "Design tenant identification strategy",
            "Implement row-level security if using shared tables",
            "Create tenant provisioning automation",
            "Set up tenant-aware connection routing",
            "Implement cross-tenant query restrictions",
            "Configure tenant-specific backups",
            "Set up resource quotas per tenant",
            "Implement tenant data export",
            "Create tenant deletion procedure",
            "Set up per-tenant monitoring",
            "Document operational procedures"
        ],
        "context": "Multi-tenant database"
    },
]

PERFORMANCE_WORKFLOWS = [
    {
        "instruction": "Diagnose and fix slow page load time",
        "steps": [
            "Measure current performance (Lighthouse, WebPageTest)",
            "Set up performance monitoring (Real User Monitoring)",
            "Analyze bundle size with webpack-bundle-analyzer",
            "Check for render-blocking resources",
            "Implement code splitting (React.lazy)",
            "Optimize images (compression, WebP, lazy loading)",
            "Add caching headers for static assets",
            "Enable compression (gzip/brotli)",
            "Audit third-party scripts",
            "Implement critical CSS",
            "Defer non-critical JavaScript",
            "Optimize fonts (font-display: swap)",
            "Check for layout shifts (CLS)",
            "Use CDN for static assets",
            "Measure improvements and compare"
        ],
        "context": "Frontend performance optimization"
    },
    {
        "instruction": "Optimize API endpoint that's timing out",
        "steps": [
            "Identify the slow endpoint from APM/logs",
            "Add detailed timing logs to endpoint",
            "Profile database queries (EXPLAIN ANALYZE)",
            "Check for N+1 query problems",
            "Add appropriate database indexes",
            "Implement query result caching (Redis)",
            "Consider pagination for large results",
            "Move heavy processing to background jobs",
            "Evaluate database connection pooling",
            "Check for external API bottlenecks",
            "Implement request timeouts",
            "Add circuit breaker for dependencies",
            "Load test to verify improvements",
            "Set up alerts for response time"
        ],
        "context": "Backend performance optimization"
    },
    # === EXPANDED PERFORMANCE WORKFLOWS ===
    {
        "instruction": "Reduce memory usage in a high-traffic application",
        "steps": [
            "Profile memory usage with heap snapshots",
            "Identify largest memory consumers",
            "Check for memory leaks with multiple snapshots",
            "Review caching strategies (size limits, TTL)",
            "Implement streaming for large data processing",
            "Optimize object pooling patterns",
            "Check for retained closures holding large data",
            "Evaluate container memory limits",
            "Review session storage mechanism",
            "Implement lazy loading for expensive resources",
            "Check event listener cleanup",
            "Use WeakMap/WeakRef for caches",
            "Monitor GC pause times",
            "Set up memory alerts"
        ],
        "context": "Memory optimization"
    },
    {
        "instruction": "Improve database query performance",
        "steps": [
            "Enable slow query logging",
            "Identify top 10 slowest queries",
            "Run EXPLAIN ANALYZE on slow queries",
            "Check for missing indexes",
            "Identify sequential scans on large tables",
            "Look for N+1 query patterns in code",
            "Add covering indexes for frequent queries",
            "Consider partial indexes for filtered queries",
            "Evaluate query execution plans",
            "Check table statistics (ANALYZE)",
            "Review join orders and strategies",
            "Implement materialized views for complex aggregations",
            "Add query result caching",
            "Set up query performance monitoring"
        ],
        "context": "Database query optimization"
    },
    {
        "instruction": "Optimize webpack build time",
        "steps": [
            "Measure current build time baseline",
            "Enable build caching (cache: { type: 'filesystem' })",
            "Use esbuild-loader instead of babel-loader",
            "Optimize source-map generation",
            "Exclude node_modules from processing",
            "Use thread-loader for heavy loaders",
            "Minimize resolve extensions list",
            "Set explicit resolve.modules",
            "Reduce loader scope with include/exclude",
            "Split vendor chunks appropriately",
            "Remove unused plugins",
            "Use DllPlugin for vendor bundles",
            "Profile with speed-measure-plugin",
            "Compare with alternative bundlers (Vite, esbuild)"
        ],
        "context": "Build optimization"
    },
    {
        "instruction": "Fix high CPU usage in Node.js application",
        "steps": [
            "Identify CPU-heavy processes with top/htop",
            "Profile with --inspect and Chrome DevTools",
            "Generate CPU flamegraph with 0x or clinic",
            "Look for synchronous operations blocking event loop",
            "Check for infinite loops or expensive regex",
            "Review JSON parsing of large payloads",
            "Move CPU-intensive tasks to worker threads",
            "Implement request throttling",
            "Check for polling intervals too aggressive",
            "Review sorting/filtering of large arrays",
            "Optimize hot code paths identified in profile",
            "Consider horizontal scaling if CPU-bound",
            "Set up CPU monitoring and alerts",
            "Document optimization findings"
        ],
        "context": "CPU optimization"
    },
]

SECURITY_WORKFLOWS = [
    {
        "instruction": "Implement security audit for web application",
        "steps": [
            "Run automated security scanner (OWASP ZAP, Snyk)",
            "Audit authentication implementation",
            "Check password storage (bcrypt/argon2)",
            "Review session management",
            "Test for SQL injection vulnerabilities",
            "Check for XSS vulnerabilities",
            "Verify CSRF protection",
            "Audit file upload handling",
            "Review API authentication/authorization",
            "Check rate limiting implementation",
            "Audit logging for sensitive data exposure",
            "Review dependency vulnerabilities (npm audit)",
            "Check security headers (CSP, HSTS)",
            "Test access control between users",
            "Document findings and remediation plan"
        ],
        "context": "Security assessment"
    },
    {
        "instruction": "Implement OAuth2/OIDC authentication",
        "steps": [
            "Choose identity provider (Auth0, Okta, Keycloak)",
            "Register application with provider",
            "Configure OAuth2 settings (client ID, secret, redirect URIs)",
            "Install OAuth library (passport.js, auth libraries)",
            "Implement authorization code flow",
            "Handle token storage securely",
            "Implement token refresh logic",
            "Add protected routes middleware",
            "Store user profile from ID token",
            "Handle logout (revoke tokens, clear session)",
            "Implement PKCE for public clients",
            "Add error handling for auth failures",
            "Test with multiple providers if needed",
            "Document authentication flow"
        ],
        "context": "Authentication implementation"
    },
    # === EXPANDED SECURITY WORKFLOWS ===
    {
        "instruction": "Implement role-based access control (RBAC)",
        "steps": [
            "Design role hierarchy (admin, manager, user)",
            "Define permissions for each role",
            "Create roles and permissions database tables",
            "Implement permission checking middleware",
            "Add role assignment to user management",
            "Create permission decorators for routes",
            "Implement resource-level permissions",
            "Add permission inheritance between roles",
            "Create admin interface for role management",
            "Implement permission caching",
            "Add audit logging for permission changes",
            "Test permission boundaries thoroughly",
            "Document role definitions",
            "Create migration path for new permissions"
        ],
        "context": "Access control"
    },
    {
        "instruction": "Secure API with rate limiting and abuse prevention",
        "steps": [
            "Implement rate limiting middleware",
            "Choose appropriate algorithm (token bucket, sliding window)",
            "Set up Redis for distributed rate limit storage",
            "Configure per-endpoint rate limits",
            "Implement per-user and per-IP limits",
            "Add burst allowance configuration",
            "Create rate limit response headers",
            "Implement exponential backoff suggestions",
            "Add IP reputation checking",
            "Implement request throttling for expensive operations",
            "Set up anomaly detection for abuse patterns",
            "Create monitoring for rate limit triggers",
            "Document rate limits in API documentation",
            "Test under load conditions"
        ],
        "context": "API protection"
    },
    {
        "instruction": "Implement secure file upload handling",
        "steps": [
            "Validate file type by content (magic bytes), not extension",
            "Set maximum file size limits",
            "Generate random filenames (don't use original)",
            "Store uploads outside web root",
            "Scan uploads for malware if possible",
            "Implement file type whitelist",
            "Strip metadata from images (EXIF)",
            "Set proper content-type on download",
            "Implement virus scanning integration",
            "Add upload progress tracking",
            "Create cleanup job for orphaned files",
            "Implement access control for downloads",
            "Log all upload activities",
            "Test with malicious file payloads"
        ],
        "context": "Secure file handling"
    },
    {
        "instruction": "Implement secrets management",
        "steps": [
            "Audit current secret storage (find hardcoded secrets)",
            "Choose secrets manager (Vault, AWS Secrets Manager)",
            "Set up secrets manager infrastructure",
            "Migrate secrets from env files to manager",
            "Implement secret rotation automation",
            "Create access policies for secrets",
            "Set up audit logging for secret access",
            "Implement local development workflow",
            "Configure CI/CD secret injection",
            "Remove secrets from version control history",
            "Set up secret expiration alerts",
            "Document secret management procedures",
            "Train team on secure practices",
            "Implement emergency secret rotation process"
        ],
        "context": "Secrets management"
    },
    {
        "instruction": "Respond to security breach incident",
        "steps": [
            "Assess scope of the breach immediately",
            "Document timeline and affected systems",
            "Isolate compromised systems",
            "Preserve evidence for forensics",
            "Rotate all potentially compromised credentials",
            "Patch the exploited vulnerability",
            "Review access logs for attacker activity",
            "Check for backdoors or persistence mechanisms",
            "Notify affected users per legal requirements",
            "Report to relevant authorities if required",
            "Update monitoring for similar attacks",
            "Conduct post-incident review",
            "Update incident response procedures",
            "Schedule security training if human error involved"
        ],
        "context": "Incident response"
    },
]

INFRASTRUCTURE_WORKFLOWS = [
    {
        "instruction": "Deploy application to Kubernetes cluster",
        "steps": [
            "Create Dockerfile with multi-stage build",
            "Build and push image to container registry",
            "Create Kubernetes namespace for app",
            "Create ConfigMap for environment config",
            "Create Secret for sensitive values",
            "Write Deployment manifest",
            "Configure resource limits and requests",
            "Create Service for internal communication",
            "Create Ingress for external access",
            "Configure horizontal pod autoscaler",
            "Set up liveness and readiness probes",
            "Deploy with kubectl apply",
            "Verify pods are running: kubectl get pods",
            "Set up logging (Fluentd/Loki)",
            "Configure monitoring (Prometheus/Grafana)",
            "Test failover and scaling"
        ],
        "context": "Kubernetes deployment"
    },
    {
        "instruction": "Set up infrastructure as code with Terraform",
        "steps": [
            "Install Terraform and configure provider (AWS/GCP/Azure)",
            "Set up remote state backend (S3 + DynamoDB)",
            "Create modules for reusable components",
            "Define VPC and networking",
            "Create compute resources (EC2/GKE)",
            "Set up database (RDS/Cloud SQL)",
            "Configure load balancer",
            "Set up DNS with Route53/Cloud DNS",
            "Create IAM roles and policies",
            "Plan infrastructure: terraform plan",
            "Apply changes: terraform apply",
            "Store state files securely",
            "Set up Terraform in CI/CD",
            "Create workspace for environments",
            "Document module usage"
        ],
        "context": "Infrastructure automation"
    },
    # === EXPANDED INFRASTRUCTURE WORKFLOWS ===
    {
        "instruction": "Set up monitoring and alerting stack",
        "steps": [
            "Deploy Prometheus for metrics collection",
            "Configure service discovery for targets",
            "Set up Grafana for visualization",
            "Create dashboards for key metrics",
            "Configure AlertManager for notifications",
            "Define alerting rules (SLOs, thresholds)",
            "Set up notification channels (Slack, PagerDuty)",
            "Implement log aggregation (Loki, ELK)",
            "Create log-based alerts",
            "Set up distributed tracing (Jaeger)",
            "Create service dependency maps",
            "Configure uptime monitoring",
            "Set up synthetic monitoring",
            "Document runbooks for alerts"
        ],
        "context": "Observability setup"
    },
    {
        "instruction": "Implement zero-downtime deployment",
        "steps": [
            "Configure rolling update strategy in Kubernetes",
            "Set appropriate maxUnavailable and maxSurge",
            "Implement proper readiness probes",
            "Configure preStop hooks for graceful shutdown",
            "Set up pod disruption budgets",
            "Implement database migration strategy",
            "Use feature flags for gradual rollout",
            "Configure load balancer health checks",
            "Implement canary deployment pipeline",
            "Set up automatic rollback on errors",
            "Test deployment with load",
            "Monitor error rates during deploy",
            "Document rollback procedure",
            "Train team on deployment process"
        ],
        "context": "Zero-downtime deployment"
    },
    {
        "instruction": "Set up disaster recovery infrastructure",
        "steps": [
            "Define RPO and RTO requirements",
            "Set up cross-region database replication",
            "Configure backup retention policies",
            "Create infrastructure in secondary region",
            "Set up DNS failover configuration",
            "Implement data synchronization",
            "Create automated failover scripts",
            "Document manual failover procedure",
            "Test failover quarterly",
            "Set up monitoring for replication lag",
            "Create runbook for disaster scenarios",
            "Train team on recovery procedures",
            "Review and update annually",
            "Document communication plan"
        ],
        "context": "Disaster recovery"
    },
    {
        "instruction": "Migrate on-premise application to cloud",
        "steps": [
            "Audit current infrastructure and dependencies",
            "Choose cloud provider and services",
            "Design cloud architecture (VPC, networking)",
            "Set up identity and access management",
            "Create development/staging environment",
            "Migrate database with minimal downtime",
            "Update application for cloud-native features",
            "Set up CI/CD for cloud deployment",
            "Configure monitoring and logging",
            "Implement security controls",
            "Plan production cutover window",
            "Execute migration with rollback plan",
            "Verify all functionality post-migration",
            "Decommission on-premise infrastructure"
        ],
        "context": "Cloud migration"
    },
    {
        "instruction": "Set up service mesh with Istio",
        "steps": [
            "Install Istio on Kubernetes cluster",
            "Enable automatic sidecar injection",
            "Configure mutual TLS between services",
            "Set up traffic management rules",
            "Implement circuit breakers",
            "Configure retry policies",
            "Set up fault injection for testing",
            "Implement canary deployments with traffic splitting",
            "Configure rate limiting per service",
            "Set up distributed tracing",
            "Create observability dashboards",
            "Implement authorization policies",
            "Document service mesh patterns",
            "Train team on Istio concepts"
        ],
        "context": "Service mesh"
    },
]

TESTING_WORKFLOWS = [
    {
        "instruction": "Implement comprehensive testing strategy",
        "steps": [
            "Audit current test coverage",
            "Define testing pyramid (unit, integration, e2e)",
            "Set up test frameworks (Jest, Cypress, Playwright)",
            "Create testing utilities and fixtures",
            "Write unit tests for business logic",
            "Add integration tests for API endpoints",
            "Create end-to-end tests for critical paths",
            "Set up test database/mocks",
            "Configure code coverage requirements",
            "Add visual regression testing",
            "Set up performance testing (k6, Artillery)",
            "Integrate tests into CI pipeline",
            "Configure test parallelization",
            "Add mutation testing (Stryker)",
            "Create test documentation"
        ],
        "context": "Testing implementation"
    },
    {
        "instruction": "Debug flaky end-to-end test",
        "steps": [
            "Identify patterns (which tests fail, when)",
            "Check for race conditions in async operations",
            "Add explicit waits for dynamic content",
            "Verify test isolation (no shared state)",
            "Check for time-dependent code",
            "Review network request handling",
            "Add retry logic for known flaky operations",
            "Check CI environment differences",
            "Run tests in debug mode with video",
            "Add more specific assertions",
            "Review parallel test conflicts",
            "Check database state between tests",
            "Verify test cleanup (afterEach)",
            "Consider test quarantine process"
        ],
        "context": "Test debugging"
    },
    # === EXPANDED TESTING WORKFLOWS ===
    {
        "instruction": "Set up contract testing for microservices",
        "steps": [
            "Choose contract testing framework (Pact, Spring Cloud Contract)",
            "Define consumer-driven contracts",
            "Generate contracts from consumer tests",
            "Set up contract broker (Pactflow)",
            "Implement provider verification tests",
            "Integrate contracts into CI pipeline",
            "Configure can-i-deploy checks",
            "Set up webhooks for contract changes",
            "Create contract versioning strategy",
            "Document contract testing workflow",
            "Train team on contract concepts",
            "Add contracts for new service interactions",
            "Monitor contract test results",
            "Review and clean up old contracts"
        ],
        "context": "Contract testing"
    },
    {
        "instruction": "Implement load testing strategy",
        "steps": [
            "Define performance requirements (response time, throughput)",
            "Choose load testing tool (k6, Gatling, Artillery)",
            "Create realistic test scenarios",
            "Design user journeys for testing",
            "Set up test environment matching production",
            "Establish performance baselines",
            "Create incremental load profiles",
            "Implement spike testing scenarios",
            "Configure soak testing for memory leaks",
            "Set up monitoring during tests",
            "Run tests and collect metrics",
            "Analyze bottlenecks and optimize",
            "Integrate into CI/CD pipeline",
            "Create performance regression alerts"
        ],
        "context": "Performance testing"
    },
    {
        "instruction": "Set up test data management",
        "steps": [
            "Audit current test data approach",
            "Design test data architecture",
            "Create data factories for test entities",
            "Implement test database seeding",
            "Set up database snapshots for fast reset",
            "Create anonymization for production data",
            "Implement test data generators",
            "Configure per-test isolation",
            "Set up test data cleanup",
            "Create shared fixtures library",
            "Document test data patterns",
            "Implement test data versioning",
            "Set up test data refresh process",
            "Train team on test data practices"
        ],
        "context": "Test data management"
    },
    {
        "instruction": "Implement chaos engineering",
        "steps": [
            "Define steady state hypothesis",
            "Identify failure scenarios to test",
            "Choose chaos engineering tool (Chaos Monkey, Litmus)",
            "Start with small blast radius experiments",
            "Test network partition scenarios",
            "Simulate service failures",
            "Test database failover",
            "Implement CPU/memory stress tests",
            "Test dependency failures",
            "Run experiments in staging first",
            "Gradually increase to production",
            "Monitor and measure impact",
            "Document findings and improvements",
            "Create regular chaos testing schedule"
        ],
        "context": "Chaos engineering"
    },
]

REFACTORING_WORKFLOWS = [
    {
        "instruction": "Refactor monolith to microservices",
        "steps": [
            "Map existing monolith domains and dependencies",
            "Identify service boundaries (bounded contexts)",
            "Design API contracts between services",
            "Set up service infrastructure (K8s, Docker)",
            "Create first microservice (lowest dependency)",
            "Implement strangler fig pattern",
            "Add API gateway for routing",
            "Migrate data gradually to service DB",
            "Update monolith to call new service",
            "Add distributed tracing",
            "Implement circuit breakers",
            "Migrate next service domain",
            "Handle cross-service transactions (Saga pattern)",
            "Document service ownership",
            "Plan decommission of monolith components"
        ],
        "context": "Architecture modernization"
    },
    {
        "instruction": "Legacy codebase modernization",
        "steps": [
            "Audit codebase for pain points",
            "Set up static analysis tools",
            "Add TypeScript gradually (allowJs: true)",
            "Improve test coverage on critical paths",
            "Update outdated dependencies incrementally",
            "Refactor to modern patterns (hooks, composition)",
            "Remove deprecated API usage",
            "Standardize code style (ESLint, Prettier)",
            "Create component library for consistency",
            "Improve error handling",
            "Add monitoring and logging",
            "Document architecture decisions",
            "Train team on new patterns",
            "Create migration guides"
        ],
        "context": "Code modernization"
    },
    # === EXPANDED REFACTORING WORKFLOWS ===
    {
        "instruction": "Extract shared library from monorepo",
        "steps": [
            "Identify code to extract (shared utilities)",
            "Audit dependencies of target code",
            "Create new package structure",
            "Move code with git history preservation",
            "Set up package build configuration",
            "Create TypeScript definitions",
            "Add unit tests for extracted code",
            "Publish to private registry",
            "Update consuming projects to use package",
            "Remove duplicated code from projects",
            "Set up versioning strategy",
            "Create CHANGELOG automation",
            "Document package API",
            "Set up release automation"
        ],
        "context": "Library extraction"
    },
    {
        "instruction": "Migrate JavaScript to TypeScript",
        "steps": [
            "Set up TypeScript configuration (strict: false initially)",
            "Install TypeScript and dependencies",
            "Rename entry file to .ts",
            "Add type definitions (@types packages)",
            "Start with strict: false, allowJs: true",
            "Convert files from leaf to root",
            "Add types incrementally (any → specific)",
            "Fix compilation errors as they arise",
            "Enable stricter options gradually",
            "Add JSDoc types for JS files in transition",
            "Create custom type definitions as needed",
            "Enable strict mode when fully converted",
            "Update build and lint configurations",
            "Document type conventions"
        ],
        "context": "TypeScript migration"
    },
    {
        "instruction": "Refactor to clean architecture",
        "steps": [
            "Map current code structure and dependencies",
            "Define domain entities and business rules",
            "Create use cases (application services)",
            "Implement repository interfaces",
            "Create adapter implementations",
            "Set up dependency injection",
            "Move business logic to domain layer",
            "Implement DTOs for layer boundaries",
            "Create mapper functions between layers",
            "Update tests for new structure",
            "Document architecture decisions",
            "Create architecture diagrams",
            "Train team on clean architecture",
            "Enforce layer dependencies with linting"
        ],
        "context": "Clean architecture"
    },
    {
        "instruction": "Optimize database schema for scale",
        "steps": [
            "Profile current query performance",
            "Identify slow queries and hot tables",
            "Analyze table growth patterns",
            "Consider normalization vs denormalization",
            "Design partitioning strategy if needed",
            "Plan index optimization",
            "Create migration scripts",
            "Test migrations on copy of production data",
            "Plan downtime or online migration",
            "Implement read replicas if needed",
            "Update application queries",
            "Execute migration during low-traffic",
            "Verify performance improvements",
            "Set up ongoing monitoring"
        ],
        "context": "Schema optimization"
    },
]

# =============================================================================
# CONCEPT Q&A (High-Level Architecture)
# =============================================================================

ARCHITECTURE_CONCEPTS = [
    {
        "question": "When should I use microservices vs monolith?",
        "answer": "Start with a monolith unless you have strong reasons. Microservices add: network latency, distributed debugging complexity, deployment coordination, data consistency challenges. Use microservices when: different parts scale differently, teams need autonomy, different tech stacks are beneficial, or when monolith becomes unmaintainable. Many successful companies started monolith and extracted services later. Martin Fowler's advice: 'Don't start with microservices.'"
    },
    {
        "question": "How do I design for horizontal scalability?",
        "answer": "Key principles: stateless services (session state in Redis), database connection pooling, read replicas for read-heavy loads, caching layers (Redis, CDN), message queues for async work, load balancers for traffic distribution. Avoid: shared state between instances, sticky sessions, file storage on app servers. Design data layer carefully - database is usually the bottleneck. Consider event-driven architecture for loose coupling."
    },
    {
        "question": "What is the CAP theorem and how does it affect architecture?",
        "answer": "CAP theorem: distributed systems can only guarantee 2 of 3: Consistency (all nodes see same data), Availability (every request gets response), Partition tolerance (system works despite network splits). In practice, network partitions happen, so choose CP or AP. Banks choose CP (consistency critical). Social media often choose AP (eventual consistency OK). PACELC extends this: if no partition, choose Latency vs Consistency."
    },
    {
        "question": "How should I handle secrets and configuration?",
        "answer": "Never commit secrets to git. Use environment variables for config. Hierarchy: env vars > config files > defaults. For secrets: use vault (HashiCorp Vault, AWS Secrets Manager). In Kubernetes: use Secrets with encryption at rest. Rotate secrets regularly. Different secrets per environment. In CI/CD: use platform secret management. Audit secret access. Encrypt secrets in transit and at rest."
    },
    # === EXPANDED ARCHITECTURE CONCEPTS ===
    {
        "question": "What is domain-driven design (DDD) and when should I use it?",
        "answer": "DDD is an approach to software design centered on the business domain. Core concepts: Bounded Contexts (clear boundaries), Aggregates (consistency boundaries), Entities (identity), Value Objects (immutable attributes), Domain Events (state changes). Use for: complex business logic, large teams, evolving domains. Don't use for: CRUD apps, small projects. Strategic patterns (context mapping) help with large systems. Requires domain expert collaboration."
    },
    {
        "question": "How do I implement eventual consistency?",
        "answer": "Eventual consistency means data becomes consistent over time, not immediately. Patterns: event sourcing (store events, derive state), CQRS (separate read/write models), saga pattern (distributed transactions). Implementation: publish events on changes, consumers update eventually. Handle: out-of-order events, duplicate events (idempotency), conflict resolution. User experience: show optimistic updates, handle conflicts gracefully. Testing: simulate network delays."
    },
    {
        "question": "What is the saga pattern and when do I need it?",
        "answer": "Saga pattern handles distributed transactions across services without 2PC. Two types: Choreography (events, each service reacts) and Orchestration (central coordinator). Steps: each service performs action and publishes event. Compensation: if step fails, previous steps rollback via compensating transactions. Use for: order processing (reserve→pay→ship), booking systems. Complexity: track saga state, handle partial failures. Prefer orchestration for complex flows."
    },
    {
        "question": "How do I design API versioning?",
        "answer": "Options: URL path (/api/v1), query param (?version=1), header (Accept-Version: v1), content negotiation (Accept: application/vnd.api.v1+json). URL versioning is simplest, most visible. Support at least N-1 version. Deprecation: announce timeline, return deprecation headers. Breaking changes: new endpoints or version bump. Non-breaking: add fields (don't remove), new endpoints. Document changes clearly. Consider GraphQL for flexibility."
    },
    {
        "question": "What is the strangler fig pattern?",
        "answer": "Incremental migration pattern: new system grows around old, gradually replacing it. Steps: 1) Identify feature to migrate, 2) Build in new system, 3) Route traffic to new system, 4) Remove old code. Benefits: low risk, gradual migration, always working system. Implementation: use facade/proxy to route, feature flags to switch. Perfect for: monolith to microservices, legacy modernization. Named after strangler fig vine that grows around trees."
    },
    {
        "question": "How do I implement circuit breaker pattern?",
        "answer": "Circuit breaker prevents cascading failures. States: Closed (normal), Open (failing), Half-Open (testing recovery). When failures exceed threshold, circuit opens - fast fail instead of waiting. After timeout, try one request (half-open). If succeeds, close circuit. Libraries: Resilience4j (Java), opossum (Node.js), Polly (.NET). Configure: failure threshold, timeout, retry attempts. Combine with: retry, timeout, fallback. Monitor circuit state for alerting."
    },
    {
        "question": "What is event sourcing and when should I use it?",
        "answer": "Event sourcing stores state changes as events, not current state. Events are immutable, append-only. State derived by replaying events. Benefits: complete audit trail, temporal queries, event replay for debugging. Challenges: schema evolution, storage growth, learning curve. Use for: financial systems, audit requirements, complex business rules. Don't use for: simple CRUD. Often combined with CQRS for read optimization."
    },
    {
        "question": "How do I design for failure in distributed systems?",
        "answer": "Assume everything fails. Patterns: timeouts (never wait forever), retries with exponential backoff, circuit breakers, bulkheads (isolate failures), fallbacks (degraded mode). Implementation: health checks, graceful degradation, queue-based load leveling. Testing: chaos engineering, fault injection. Monitoring: detect partial failures, alert on error rates. Design for idempotency - operations may execute multiple times. Document failure modes and recovery."
    },
    {
        "question": "What is CQRS and when is it appropriate?",
        "answer": "CQRS: Command Query Responsibility Segregation - separate read and write models. Write model optimized for transactions, read model optimized for queries. Benefits: independent scaling, optimized models, complex queries simplified. Challenges: eventual consistency, increased complexity. Use when: read/write patterns differ significantly, complex reporting needs, event sourcing already used. Don't use for: simple CRUD apps. Implementation: separate databases or projections from event store."
    },
    {
        "question": "How do I implement idempotency in APIs?",
        "answer": "Idempotency: same request produces same result. Critical for retry safety. Implementation: idempotency key (client-provided unique ID), store request results, return cached response for duplicate requests. Storage: Redis with TTL for keys. Include in: POST/PUT endpoints, payment processing, order creation. Client: generate UUID, retry with same key. Server: check key before processing, store result after. Handle race conditions with locking."
    },
    {
        "question": "What is API gateway pattern and why use it?",
        "answer": "API gateway is single entry point for all clients. Responsibilities: routing, authentication, rate limiting, request/response transformation, aggregation. Benefits: simplified client, cross-cutting concerns centralized, service isolation. Tools: Kong, AWS API Gateway, nginx. Consider: BFF (Backend for Frontend) per client type. Avoid: business logic in gateway. Monitor: latency added by gateway. Can become bottleneck - scale appropriately."
    },
    {
        "question": "How do I handle distributed tracing?",
        "answer": "Distributed tracing tracks requests across services. Implementation: inject trace ID at entry, propagate through all calls, collect spans. Tools: Jaeger, Zipkin, OpenTelemetry (standard). Each service: receives trace context, creates span, passes context downstream. Collect: timing, errors, metadata. Visualize: request flow, latency breakdown, error location. Essential for: debugging microservices, performance analysis, dependency mapping."
    },
    {
        "question": "What is the sidecar pattern?",
        "answer": "Sidecar is helper container deployed alongside main application. Use for: logging, proxying, monitoring, service mesh. Benefits: language-agnostic, separation of concerns, reusable components. Examples: Envoy proxy (Istio), Fluentd (logging), Vault agent (secrets). Implementation: Kubernetes pod with multiple containers, shared network/storage. Sidecar handles cross-cutting concerns, main container focuses on business logic. Common in service mesh architectures."
    },
    {
        "question": "How should I approach database per service in microservices?",
        "answer": "Database per service ensures loose coupling. Each service owns its data, accessed only via API. Benefits: independent schema evolution, technology choice, scaling. Challenges: distributed transactions, data consistency, joins across services. Patterns: saga for transactions, API composition for queries, event-driven sync. Consider: shared database for tightly coupled services (pragmatic). Data duplication is OK for performance. Eventually consistent reporting database."
    },
]

# =============================================================================
# ERROR/COMPLEX SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "Production database is running out of disk space",
        "error_type": "critical_infrastructure",
        "response": {
            "status": "immediate_action_required",
            "immediate_steps": [
                "Check disk usage: df -h",
                "Identify large tables: SELECT pg_size_pretty(pg_table_size(table_name))",
                "Check for long-running transactions holding locks",
                "Clear pg_wal if safe (check replication first)",
                "Remove old backups if stored locally"
            ],
            "short_term": [
                "Add disk space (resize volume)",
                "Archive/delete old data",
                "Vacuum tables to reclaim space",
                "Set up autovacuum properly"
            ],
            "long_term": [
                "Implement data retention policies",
                "Set up disk space monitoring/alerts",
                "Consider partitioning large tables",
                "Archive historical data to cold storage"
            ]
        }
    },
    {
        "instruction": "Kubernetes pods are in CrashLoopBackOff",
        "error_type": "deployment_failure",
        "response": {
            "status": "needs_diagnosis",
            "diagnostic_commands": [
                "kubectl describe pod <pod-name>",
                "kubectl logs <pod-name> --previous",
                "kubectl get events --sort-by=.metadata.creationTimestamp"
            ],
            "common_causes": [
                "Application error on startup (check logs)",
                "Missing environment variables or secrets",
                "Liveness probe failing too quickly",
                "Resource limits too restrictive (OOM)",
                "Image pull errors",
                "Missing dependencies (database not ready)"
            ],
            "solutions": {
                "startup_error": "Fix application code, check logs",
                "missing_config": "Verify ConfigMaps and Secrets",
                "probe_failure": "Increase initialDelaySeconds",
                "oom": "Increase memory limits",
                "image_pull": "Check imagePullSecrets and registry access"
            }
        }
    },
    {
        "instruction": "Memory leak in Node.js application",
        "error_type": "performance_degradation",
        "response": {
            "status": "investigation_required",
            "diagnosis": [
                "Monitor heap usage: process.memoryUsage()",
                "Take heap snapshots: --inspect with Chrome DevTools",
                "Compare snapshots to find growing objects",
                "Check for common patterns: event listeners not removed, closures holding references",
                "Use clinic.js for profiling"
            ],
            "common_causes": [
                "Event listeners not being removed",
                "Growing arrays/caches without bounds",
                "Closures capturing large objects",
                "Streams not properly closed",
                "Global state accumulation"
            ],
            "fixes": [
                "Use WeakMap/WeakSet for caches",
                "Implement LRU cache with size limits",
                "Remove event listeners in cleanup",
                "Use streaming for large data",
                "Review and fix identified leaks"
            ]
        }
    },
    # === EXPANDED ERROR SCENARIOS ===
    {
        "instruction": "Service returning 504 Gateway Timeout intermittently",
        "error_type": "networking_timeout",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check which endpoint is timing out",
                "Review load balancer timeout settings",
                "Check backend service response times",
                "Look for database slow queries at timeout times",
                "Check external API dependencies",
                "Review connection pool exhaustion"
            ],
            "common_causes": [
                "Database query taking too long",
                "External API not responding",
                "Connection pool exhausted",
                "Load balancer timeout too short",
                "Resource contention under load"
            ],
            "solutions": {
                "slow_db": "Add indexes, optimize queries, add caching",
                "external_api": "Add circuit breaker, timeout, fallback",
                "connection_pool": "Increase pool size, check for leaks",
                "load_balancer": "Increase timeout, add retry policy",
                "resource": "Scale horizontally, add rate limiting"
            }
        }
    },
    {
        "instruction": "Deployment succeeded but users report 500 errors",
        "error_type": "post_deployment_failure",
        "response": {
            "status": "production_incident",
            "immediate_actions": [
                "Check error rates in monitoring",
                "Review application logs for exceptions",
                "Check if all pods are healthy",
                "Verify database connectivity",
                "Check for configuration differences"
            ],
            "diagnosis": [
                "Compare new vs old deployment",
                "Check environment variable changes",
                "Review recent code changes for issues",
                "Verify database migrations ran successfully",
                "Check for dependency version changes"
            ],
            "resolution": {
                "quick_fix": "Rollback to previous deployment",
                "root_cause": "Fix bug and redeploy",
                "prevent": "Add better testing, canary deployments"
            }
        }
    },
    {
        "instruction": "Redis connection refused in production",
        "error_type": "infrastructure_failure",
        "response": {
            "status": "critical_dependency_down",
            "immediate_checks": [
                "Verify Redis server is running",
                "Check network connectivity to Redis",
                "Verify Redis host/port configuration",
                "Check for Redis memory exhaustion",
                "Verify authentication credentials"
            ],
            "recovery_steps": [
                "Restart Redis if crashed",
                "Implement graceful degradation",
                "Use fallback cache (in-memory)",
                "Scale Redis if memory exhausted",
                "Check for maxclients limit"
            ],
            "prevention": [
                "Set up Redis Sentinel or Cluster",
                "Implement connection retry logic",
                "Add Redis health monitoring",
                "Configure proper memory limits"
            ]
        }
    },
    {
        "instruction": "SSL certificate expired causing outage",
        "error_type": "certificate_expiry",
        "response": {
            "status": "immediate_fix_required",
            "immediate_actions": [
                "Identify which certificate expired",
                "Generate or obtain new certificate",
                "Update certificate on load balancer/server",
                "Verify certificate chain is complete",
                "Test HTTPS connectivity"
            ],
            "prevention": [
                "Set up certificate expiry monitoring",
                "Use Let's Encrypt with auto-renewal",
                "Alert at 30, 14, 7 days before expiry",
                "Document certificate locations",
                "Automate certificate rotation"
            ]
        }
    },
    {
        "instruction": "Database replication lag causing stale reads",
        "error_type": "data_consistency",
        "response": {
            "status": "investigate_cause",
            "diagnostic_steps": [
                "Check replication lag metrics",
                "Verify network between primary and replicas",
                "Check for long-running transactions on primary",
                "Review write load on primary",
                "Check replica hardware/resources"
            ],
            "immediate_mitigations": [
                "Route critical reads to primary",
                "Add read-after-write consistency logic",
                "Implement session affinity for user requests"
            ],
            "long_term_fixes": [
                "Scale primary write capacity",
                "Add more replicas to distribute read load",
                "Optimize write queries",
                "Consider synchronous replication for critical data"
            ]
        }
    },
    {
        "instruction": "CI/CD pipeline failing with out of memory",
        "error_type": "build_failure",
        "response": {
            "status": "pipeline_optimization_needed",
            "diagnosis": [
                "Check which step is running out of memory",
                "Review build agent resource limits",
                "Check for memory leaks in test suite",
                "Review parallel test execution settings"
            ],
            "solutions": [
                "Increase build agent memory",
                "Split tests into smaller jobs",
                "Run memory-heavy tests serially",
                "Optimize webpack/build memory usage",
                "Use smaller Docker images for builds"
            ],
            "prevention": [
                "Monitor build memory over time",
                "Set memory limits per step",
                "Regular cleanup of build caches"
            ]
        }
    },
    {
        "instruction": "API rate limited by third-party service",
        "error_type": "external_dependency",
        "response": {
            "status": "implement_resilience",
            "immediate_actions": [
                "Implement exponential backoff",
                "Cache responses where possible",
                "Queue and batch requests",
                "Check if rate limit can be increased"
            ],
            "architectural_solutions": [
                "Implement request queuing system",
                "Add local caching layer",
                "Use webhook instead of polling if available",
                "Consider multiple API keys",
                "Implement circuit breaker"
            ],
            "monitoring": [
                "Track rate limit headers",
                "Alert before hitting limits",
                "Dashboard for API usage"
            ]
        }
    },
    {
        "instruction": "Message queue consumer falling behind",
        "error_type": "backpressure",
        "response": {
            "status": "scaling_needed",
            "diagnosis": [
                "Check consumer processing time",
                "Review message production rate",
                "Check for failed message retries",
                "Verify consumer resources",
                "Check dead letter queue"
            ],
            "immediate_actions": [
                "Scale up consumer instances",
                "Increase consumer concurrency",
                "Temporarily pause non-critical producers"
            ],
            "long_term": [
                "Optimize message processing",
                "Implement auto-scaling for consumers",
                "Add consumer lag monitoring",
                "Consider partitioning for parallelism",
                "Review message batch sizes"
            ]
        }
    },
    {
        "instruction": "WebSocket connections dropping randomly",
        "error_type": "connection_stability",
        "response": {
            "status": "investigate_network",
            "diagnostic_steps": [
                "Check load balancer WebSocket support",
                "Review connection timeout settings",
                "Check for proxy/firewall issues",
                "Review client reconnection logic",
                "Check server resource limits"
            ],
            "common_causes": [
                "Load balancer idle timeout too short",
                "Proxy not configured for WebSocket",
                "Server hitting connection limits",
                "Network instability"
            ],
            "solutions": {
                "load_balancer": "Increase idle timeout, enable WebSocket support",
                "proxy": "Configure upgrade headers passthrough",
                "limits": "Increase ulimit, connection pool size",
                "client": "Implement robust reconnection with backoff"
            }
        }
    },
    {
        "instruction": "Docker builds failing with 'no space left on device'",
        "error_type": "build_infrastructure",
        "response": {
            "status": "cleanup_required",
            "immediate_fix": [
                "docker system prune -a",
                "docker volume prune",
                "Remove old images: docker image prune -a --filter 'until=24h'",
                "Check disk usage: df -h"
            ],
            "prevention": [
                "Set up automated cleanup job",
                "Limit Docker storage driver size",
                "Use multi-stage builds to reduce layer size",
                "Implement image retention policy",
                "Monitor disk usage with alerts"
            ]
        }
    },
    {
        "instruction": "Horizontal pod autoscaler not scaling",
        "error_type": "kubernetes_scaling",
        "response": {
            "status": "configuration_review",
            "diagnostic_steps": [
                "kubectl describe hpa <name>",
                "Check if metrics-server is running",
                "Verify resource requests are set on pods",
                "Check target metric values",
                "Review HPA events"
            ],
            "common_issues": [
                "No resource requests/limits on deployment",
                "Metrics server not installed",
                "Target utilization already below threshold",
                "minReplicas equals maxReplicas",
                "Custom metrics not available"
            ],
            "solutions": [
                "Set CPU/memory requests on containers",
                "Install metrics-server if missing",
                "Adjust target utilization threshold",
                "Review min/max replica settings"
            ]
        }
    },
    {
        "instruction": "Terraform state locked and blocking deployments",
        "error_type": "infrastructure_as_code",
        "response": {
            "status": "careful_intervention",
            "diagnosis": [
                "Check who/what is holding the lock",
                "Verify if terraform apply is actually running",
                "Check for crashed CI/CD jobs",
                "Review state backend access"
            ],
            "resolution": [
                "Wait for legitimate operation to complete",
                "If orphaned lock: terraform force-unlock <lock-id>",
                "Check DynamoDB for lock entry if using S3 backend"
            ],
            "warning": "Force unlock can cause state corruption if operation is still running",
            "prevention": [
                "Set up state lock timeout",
                "Use separate state per environment",
                "Implement CI/CD job timeouts"
            ]
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_planning_response(steps: List[str], context: str = "") -> str:
    response = {
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
        "requires_confirmation": True
    }
    if context:
        response["context"] = context
    return json.dumps(response, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_workflow_examples() -> List[Dict]:
    examples = []
    all_workflows = (FULL_STACK_WORKFLOWS + DATABASE_WORKFLOWS + 
                     PERFORMANCE_WORKFLOWS + SECURITY_WORKFLOWS +
                     INFRASTRUCTURE_WORKFLOWS + TESTING_WORKFLOWS +
                     REFACTORING_WORKFLOWS)
    
    for workflow in all_workflows:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": workflow["instruction"],
            "response": format_planning_response(workflow["steps"], workflow.get("context", ""))
        })
    return examples

def generate_concept_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in ARCHITECTURE_CONCEPTS]

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
    print("Generating Multi-Step Workflows Training Data")
    print("=" * 60)
    
    all_examples = []
    
    workflow_examples = generate_workflow_examples()
    all_examples.extend(workflow_examples)
    print(f"Generated {len(workflow_examples)} workflow examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "multistep_workflows.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
