#!/usr/bin/env python3
"""
Generate advanced systems architecture training data for AJ fine-tuning.
Covers enterprise architecture, distributed systems, and design patterns.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"

SYSTEM_PROMPT = "You are AJ, an AI coding assistant. You are helping with systems architecture and design patterns."

# =============================================================================
# DISTRIBUTED SYSTEMS ARCHITECTURE
# =============================================================================

DISTRIBUTED_SYSTEMS = [
    {
        "question": "How do I implement leader election in a distributed system?",
        "answer": "Leader election ensures one node coordinates work. Algorithms: Bully (highest ID wins), Raft (consensus-based), Paxos (academic but complex). Practical implementation: use ZooKeeper ephemeral nodes, etcd lease with TTL, Redis SETNX with expiry, Consul sessions. Pattern: acquire lock atomically, renew periodically, other nodes watch for leader failure. Handle: split-brain (require majority quorum), network partitions (fencing tokens). Cloud: AWS DynamoDB conditional writes, Azure Blob leases."
    },
    {
        "question": "What is the difference between two-phase commit and saga?",
        "answer": "Two-phase commit (2PC): coordinator asks all participants to prepare, then commit. Synchronous, locks resources, blocks on coordinator failure, doesn't scale well. Saga: sequence of local transactions with compensating actions for rollback. Async, no locks, eventually consistent, scales well. 2PC for: same database, strong consistency required. Saga for: microservices, different databases, acceptable eventual consistency. Saga types: choreography (event-driven) vs orchestration (central coordinator)."
    },
    {
        "question": "How do I handle split-brain in distributed systems?",
        "answer": "Split-brain: network partition causes multiple leaders. Prevention: quorum-based decisions (majority required), fencing tokens (monotonic IDs prevent stale leaders), STONITH (Shoot The Other Node In The Head - force shutdown). Detection: heartbeat timeouts, network partition detection. Resolution: automatic merge (CRDTs), manual reconciliation, last-writer-wins (data loss risk). In practice: use battle-tested tools (ZooKeeper, etcd, Consul) that handle this. Always prefer CP over AP for coordination."
    },
    {
        "question": "What is a consistent hash ring and when should I use it?",
        "answer": "Consistent hashing distributes data across nodes with minimal redistribution on node changes. Ring: nodes placed at hash positions, keys route to nearest node clockwise. Virtual nodes: each physical node has multiple ring positions for better distribution. Use for: distributed caches (Memcached, Redis Cluster), database sharding, CDN routing, load balancing. Benefits: only K/n keys move when node added/removed (vs rehashing everything). Libraries: jump consistent hash, rendezvous hashing, ketama."
    },
    {
        "question": "How do I implement rate limiting across distributed services?",
        "answer": "Algorithms: token bucket (burst-friendly), sliding window log (precise), sliding window counter (efficient). Distributed implementation: Redis with Lua scripts (atomic), dedicated rate limit service, API gateway level. Key design: identify client (IP, API key, user), choose limit granularity (per second/minute), handle limit exceeded gracefully (429 + Retry-After header). Consider: local + global limits, different tiers, cost-based limits (expensive operations count more). Tools: Redis Cell, Resilience4j, Kong rate limiting."
    },
    {
        "question": "What is gossip protocol and when is it useful?",
        "answer": "Gossip protocol: nodes periodically exchange state with random peers, information spreads epidemically. Properties: eventually consistent, fault tolerant, scalable, decentralized. Use cases: cluster membership (Cassandra, Consul), failure detection, configuration propagation. Trade-offs: eventual consistency (not immediate), bandwidth overhead, convergence time. Implementation: each node maintains membership list, periodically sends to random nodes, merge received state. Anti-entropy: periodic full state sync to fix inconsistencies."
    },
    {
        "question": "How do I design for exactly-once message delivery?",
        "answer": "True exactly-once is impossible (Two Generals Problem). Practical solution: at-least-once delivery + idempotent processing. Implementation: producer assigns unique message ID, consumer tracks processed IDs, deduplication window. Kafka exactly-once: idempotent producers + transactional consumers. Pattern: store message ID with result in same transaction. Alternative: at-most-once (accept message loss) or at-least-once (accept duplicates). Design consumers to be idempotent - same message processed multiple times = same result."
    },
    {
        "question": "What is backpressure and how should I handle it?",
        "answer": "Backpressure: downstream system slower than upstream, causing queue buildup. Without handling: OOM, cascading failures. Strategies: drop excess (lossy), buffer with limit then drop, slow down producer (reactive streams), sample/aggregate, shed load based on priority. Implementation: bounded queues, reactive streams (RxJava, Project Reactor), gRPC flow control. In HTTP: return 503 with Retry-After. Monitor: queue depths, processing latency. Design: make backpressure visible and controllable."
    },
    {
        "question": "How do I implement distributed locking?",
        "answer": "Use for: leader election, preventing duplicate processing, rate limiting. Options: Redis (SETNX + expire, Redlock for multi-node), ZooKeeper (ephemeral sequential nodes), etcd (lease-based), database (SELECT FOR UPDATE). Redis single node: SET key value NX PX milliseconds. Redlock: acquire on majority of nodes. Critical: always set TTL (holder might crash), use fencing tokens, handle clock skew. Libraries: python-redis-lock, redisson, curator. Be aware of Redlock controversy - Martin Kleppmann critique."
    },
    {
        "question": "What is vector clock vs Lamport timestamp?",
        "answer": "Lamport timestamp: single counter, incremented on events, establishes 'happens-before' partial ordering. Simple but can't detect concurrent events. Vector clock: array of counters (one per node), captures causality precisely, can detect concurrent events. Trade-off: vector clocks grow with node count. Use Lamport for: ordering events, simple systems. Use vector clocks for: detecting conflicts, causal consistency. Alternatives: version vectors (similar to vector clocks), hybrid logical clocks (combine physical + logical time)."
    },
    {
        "question": "How do I design a write-ahead log (WAL)?",
        "answer": "WAL: append-only log of changes, written before data modification. Guarantees: durability (fsync log), atomicity (replay on crash), consistency (recover to valid state). Implementation: sequential writes (fast), segment files, periodic checkpointing, log compaction. Used by: databases (PostgreSQL, MySQL), message queues (Kafka), distributed systems (Raft log). Design: fixed-size segments, background archival/cleanup, efficient replay (index checkpoints). Recovery: replay from last checkpoint, apply all log entries."
    },
    {
        "question": "What is the Byzantine Generals Problem and how does it affect distributed systems?",
        "answer": "Byzantine fault: node can behave arbitrarily (malicious or corrupted), not just fail-stop. Byzantine Generals: agreement problem with potential traitors. Tolerance: need 3f+1 nodes to tolerate f Byzantine faults. Solutions: PBFT (Practical Byzantine Fault Tolerance), blockchain consensus (PoW, PoS). Most systems assume crash-fault only (easier): Raft, Paxos, ZooKeeper. Use Byzantine tolerance for: public blockchains, untrusted environments. Regular distributed systems: crash-fault tolerance sufficient, much simpler."
    },
]

# =============================================================================
# ENTERPRISE ARCHITECTURE PATTERNS
# =============================================================================

ENTERPRISE_PATTERNS = [
    {
        "question": "How do I design a multi-tenant SaaS architecture?",
        "answer": "Isolation models: 1) Shared everything (cheapest, least isolation), 2) Shared app, separate DB (balanced), 3) Separate everything (most isolation, expensive). Implementation: tenant ID in every query, row-level security, schema per tenant, or database per tenant. Considerations: data isolation (compliance), noisy neighbor prevention, tenant-specific customization, billing integration. Infrastructure: single deployment serving all tenants vs tenant-specific deployments. Start simple (shared), add isolation as needed."
    },
    {
        "question": "What is the hexagonal architecture (ports and adapters)?",
        "answer": "Hexagonal architecture: business logic at center, external systems connect via ports (interfaces) and adapters (implementations). Ports: define how core communicates with outside (driven ports for outgoing, driving ports for incoming). Adapters: implement ports for specific technology (REST adapter, SQL adapter). Benefits: testable (mock adapters), technology-agnostic core, clear boundaries. Similar to: clean architecture, onion architecture. Use for: complex domain logic that should outlive infrastructure choices."
    },
    {
        "question": "How should I handle multi-region deployment?",
        "answer": "Strategies: active-passive (one region serves traffic, others standby), active-active (all regions serve traffic). Data: replicate async (eventual consistency) or sync (latency penalty). Routing: GeoDNS, anycast, global load balancer. Challenges: data consistency, failover time, cost. Active-active patterns: CRDT for conflicts, last-writer-wins, region-sticky users. Implementation: each region self-sufficient, cross-region replication for disaster recovery. Consider: compliance (data residency), latency requirements, complexity tolerance."
    },
    {
        "question": "What is feature flagging architecture?",
        "answer": "Feature flags: control feature rollout without deployment. Architecture: flag storage (database, config service), flag SDK (client-side evaluation), management UI. Evaluation: user attributes → rules → flag value. Types: release flags (temporary), ops flags (kill switches), experiment flags (A/B tests), permission flags (entitlements). Best practices: clean up old flags, default to off, monitor flag usage. Services: LaunchDarkly, Split.io, Unleash, Flagsmith. Self-hosted: database + cache + evaluation library."
    },
    {
        "question": "How do I design an audit logging system?",
        "answer": "Capture: who (user/service), what (action, resource), when (timestamp), where (IP, service), why (business context). Storage: append-only (immutability), separate from operational DB, long retention. Implementation: middleware captures, async queue to audit store. Query needs: by user, by resource, by time range, by action type. Compliance: tamper-evident (hash chaining), retention policies, access controls. Scale: event streaming (Kafka) to data lake (S3/BigQuery). Consider: PII handling, log aggregation, alerting on suspicious patterns."
    },
    {
        "question": "What is the outbox pattern?",
        "answer": "Outbox pattern: reliable event publishing with database transactions. Problem: updating database AND publishing event must be atomic. Solution: write event to outbox table in same transaction, separate process publishes events, mark as published. Implementation: outbox table (id, payload, created, published), poller or CDC (Change Data Capture). Guarantees: at-least-once delivery (consumer must be idempotent). Used in: microservices event publishing, transactional messaging. Alternative: listen to database transaction log directly (Debezium)."
    },
    {
        "question": "How do I design for GDPR compliance?",
        "answer": "Data architecture: catalog all PII, document processing purposes, enable data portability (export), enable right to erasure (soft delete + hard delete). Implementation: consent management, data access controls, audit logging, encryption at rest/transit. Right to be forgotten: soft delete + scheduled hard delete, handle backups, notify data processors. Data portability: structured export (JSON/XML), machine-readable format. Breach notification: detection systems, incident response process. Privacy by design: minimize data collected, pseudonymization, retention limits."
    },
    {
        "question": "What is a service mesh and when do I need one?",
        "answer": "Service mesh: dedicated infrastructure layer for service-to-service communication. Features: traffic management, security (mTLS), observability. Components: data plane (sidecar proxies like Envoy), control plane (Istio, Linkerd). Benefits: consistent policies, language-agnostic, centralized config. When needed: many microservices, complex traffic patterns, security requirements, observability gaps. When not needed: few services, monolith, simple communication. Consider: complexity cost, performance overhead, operational expertise required. Start without, add when pain points emerge."
    },
    {
        "question": "How do I design a plugin architecture?",
        "answer": "Core concepts: host application defines extension points (interfaces), plugins implement extensions, runtime discovers and loads plugins. Implementation patterns: 1) Interface-based (plugins implement contracts), 2) Event-based (plugins subscribe to hooks), 3) Pipeline (plugins process data in chain). Discovery: directory scanning, registration, manifest files. Isolation: sandboxing, resource limits, capability restrictions. Security: plugin signing, permission model. Examples: VS Code extensions, Webpack plugins, WordPress hooks. Design stable extension points that rarely change."
    },
    {
        "question": "What is blue-green vs canary deployment?",
        "answer": "Blue-green: two identical environments, switch traffic atomically. Deploy to inactive, test, switch load balancer. Rollback: switch back immediately. Pros: instant rollback, full testing in prod-like environment. Cons: double infrastructure cost, database migrations tricky. Canary: gradual rollout to subset of users/traffic. Monitor metrics, increase percentage if healthy. Rollback: route all traffic to old version. Pros: catch issues with minimal impact, less infrastructure. Cons: slower rollout, need good observability. Choose based on: risk tolerance, infrastructure cost, deployment frequency."
    },
    {
        "question": "How do I implement a rate limiting architecture for APIs?",
        "answer": "Levels: edge (CDN/API gateway), service (per-service limits), user (per-user quotas). Algorithms: token bucket (bursty), leaky bucket (smooth), fixed window, sliding window. Storage: local (fast, inconsistent), distributed (consistent, slower - Redis). Implementation: middleware checks quota, returns 429 with Retry-After, tracks usage. Considerations: different limits per tier/plan, cost-based limits (expensive ops count more), grace periods, alerts on abuse. API response: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers."
    },
    {
        "question": "What is data mesh architecture?",
        "answer": "Data mesh: decentralized data architecture treating data as product. Principles: domain ownership (teams own their data), data as product (discoverable, documented, quality guaranteed), self-serve platform (infrastructure as platform), federated governance (standards with autonomy). Contrast to: data lake (centralized), data warehouse (centralized). Implementation: domain teams publish data products, platform provides infrastructure (storage, compute, catalog), governance defines interoperability. Use when: large organization, multiple domains, data quality issues with central approach."
    },
]

# =============================================================================
# INTEGRATION PATTERNS
# =============================================================================

INTEGRATION_PATTERNS = [
    {
        "question": "What is the difference between message queue and event stream?",
        "answer": "Message queue: point-to-point, message consumed once, deleted after processing. Use for: task distribution, job queues. Examples: RabbitMQ, SQS, Azure Service Bus. Event stream: publish-subscribe, multiple consumers read same events, events retained. Use for: event sourcing, real-time analytics, event-driven architecture. Examples: Kafka, Kinesis, Pulsar. Queue semantics: competing consumers. Stream semantics: consumer groups with offsets. Choose queue for: work distribution. Choose stream for: event replay, multiple consumers, audit trail."
    },
    {
        "question": "How do I design a webhook system?",
        "answer": "Components: event generation, subscriber management, delivery engine, retry mechanism. Delivery: POST to subscriber URL with event payload, verify response (2xx = success). Reliability: retry with exponential backoff, circuit breaker per subscriber, dead letter queue for failures. Security: HMAC signature (webhook secret), HTTPS only, IP allowlisting option. Scalability: async delivery via queue, rate limiting per subscriber. Management: subscriber registration API, delivery status dashboard, log retention. Consider: payload size limits, timeout configuration, idempotency keys."
    },
    {
        "question": "What is API composition pattern in microservices?",
        "answer": "API composition: aggregate data from multiple services to fulfill request. Implementation: API gateway or BFF (Backend for Frontend) calls multiple services, combines responses. Challenges: latency (parallel calls when possible), partial failures (fallback/defaults), transactions (saga if writes needed). Patterns: parallel calls (independent data), sequential (dependent data), circuit breakers per service. Alternative: CQRS with materialized views (precomputed aggregates). Use composition for: read-heavy queries spanning services. Avoid for: complex aggregations (consider dedicated query service)."
    },
    {
        "question": "How do I implement request/response over messaging?",
        "answer": "Pattern: correlation ID links request to response. Implementation: 1) Generate correlation ID, 2) Send request to request queue with reply-to and correlation ID, 3) Wait for response on reply queue matching correlation ID. Temporary reply queue: per-request queue, auto-delete. Shared reply queue: filter by correlation ID. Timeout: essential, handle no response. Libraries: RabbitMQ RPC pattern, request-reply in messaging frameworks. Use for: sync semantics over async transport. Consider: direct HTTP call often simpler for request-response."
    },
    {
        "question": "What is change data capture (CDC) and how do I use it?",
        "answer": "CDC: capture database changes and publish as events. Methods: log-based (read transaction log - best), trigger-based (database triggers), polling (timestamp/version columns). Tools: Debezium (most popular, supports many DBs), Maxwell (MySQL), AWS DMS. Use cases: cache invalidation, search index sync, cross-service data sync, event sourcing from existing DB. Benefits: no application changes, complete change history, low latency. Considerations: log retention settings, schema evolution handling, exactly-once delivery (consumer idempotency)."
    },
    {
        "question": "How do I handle API versioning with breaking changes?",
        "answer": "Non-breaking changes: add fields (don't remove), new endpoints, optional parameters. Breaking changes: field removal, type changes, semantic changes. Strategies: run parallel versions (resource intensive), adapter layer (translate old to new), consumer-driven contracts (negotiated changes). Deprecation process: announce timeline, deprecation headers, sunset period, monitor usage before removal. GraphQL approach: field deprecation, schema evolution. Consider: API gateway can transform requests, SDKs can abstract version differences. Document: changelog, migration guides."
    },
    {
        "question": "What is the anti-corruption layer pattern?",
        "answer": "Anti-corruption layer: translation layer between your domain and external/legacy system. Purpose: prevent foreign concepts from leaking into your domain model. Implementation: facade that translates between models, adapters for external calls. Use for: integrating legacy systems, third-party APIs, different bounded contexts. Components: translator (model mapping), adapter (protocol), facade (simplified interface). Benefits: isolate change, clean domain model, easier testing. Cost: additional layer, mapping maintenance. Essential in DDD when integrating systems with different domain languages."
    },
    {
        "question": "How do I design an ETL pipeline?",
        "answer": "ETL: Extract (read sources), Transform (clean/enrich), Load (write to destination). Modern approach: ELT (load raw, transform in warehouse). Architecture: orchestrator (Airflow, Dagster), workers (Spark, dbt), storage (data lake, warehouse). Extract: CDC for databases, APIs, file drops. Transform: data quality checks, joins, aggregations, business logic. Load: incremental (append/upsert) vs full refresh. Considerations: idempotency (rerunnable), lineage tracking, monitoring, alerting on failures. Streaming alternative: real-time ETL with Kafka + stream processing."
    },
]

# =============================================================================
# RESILIENCE PATTERNS
# =============================================================================

RESILIENCE_PATTERNS = [
    {
        "question": "What is bulkhead pattern and how do I implement it?",
        "answer": "Bulkhead: isolate components so failure in one doesn't cascade. Types: thread pool bulkhead (dedicated threads per dependency), connection pool bulkhead, process bulkhead. Implementation: separate thread pools per external service, dedicated connection pools, Kubernetes resource limits. Example: Netflix Hystrix thread pools. Benefits: prevent slow service from exhausting all threads, contain failures. Sizing: based on expected throughput and latency. Monitor: pool exhaustion, queue depths. Combine with: circuit breaker, timeout, fallback."
    },
    {
        "question": "How do I implement retry with exponential backoff?",
        "answer": "Formula: delay = base * 2^attempt + jitter. Jitter prevents thundering herd (all clients retrying simultaneously). Implementation: base delay (100ms), max delay cap (30s), max attempts (5), jitter (random 0-100%). Retryable errors: network failures, 503, 429 (respect Retry-After). Non-retryable: 4xx client errors, business validation. Libraries: tenacity (Python), retry (Node.js), Polly (.NET), resilience4j (Java). Combine with: circuit breaker (stop retrying if service down), timeout per attempt."
    },
    {
        "question": "What is graceful degradation and how do I design for it?",
        "answer": "Graceful degradation: reduce functionality rather than fail completely. Examples: serve cached data if DB slow, disable recommendations if service down, show placeholder content. Implementation: feature flags for degraded mode, fallback data sources, default responses. Design: identify core vs nice-to-have features, define degradation levels, implement fallbacks. Monitoring: track degraded mode activations, alert on duration. User experience: communicate reduced functionality. Testing: chaos engineering to verify degraded behavior works."
    },
    {
        "question": "How do I implement health checks properly?",
        "answer": "Types: liveness (app running - restart if fails), readiness (can handle traffic - remove from load balancer), startup (initializing - give more time). Implementation: /healthz (liveness), /readyz (readiness), check critical dependencies. What to check: database connectivity, cache connectivity, external services (with timeouts). What NOT to check in liveness: dependencies (causes cascading restarts). Kubernetes: separate probes, appropriate timeouts and intervals. Response: 200 OK or 503, optional JSON details. Monitoring: aggregate health across instances."
    },
    {
        "question": "What is the timeout pattern and how do I configure timeouts?",
        "answer": "Timeout types: connection timeout (establishing connection), read/request timeout (waiting for response), total timeout (entire operation). Configuration: shorter timeouts for retryable calls, longer for non-retryable. Guidelines: connection timeout 1-5s, request timeout based on P99 latency + buffer. Implementation: set at HTTP client level, not global. Consider: downstream service SLAs, user experience, retry budget. Avoid: infinite timeouts, timeouts longer than parent timeout. Combine with: circuit breaker, retry. Monitor: timeout rate as health indicator."
    },
    {
        "question": "How do I implement the fallback pattern?",
        "answer": "Fallback: alternative behavior when primary fails. Types: cache fallback (serve stale data), default fallback (hardcoded response), alternative service (secondary provider), degraded fallback (reduced functionality). Implementation: try primary, catch failure, return fallback. Triggers: timeout, circuit open, error response. Design: fallbacks should be low-risk (avoid fallback to another failing service). Testing: verify fallbacks work in production (chaos testing). Examples: CDN falls back to origin, recommendation service returns popular items, search returns cached results."
    },
    {
        "question": "What is chaos engineering and how do I start?",
        "answer": "Chaos engineering: controlled experiments to test system resilience. Process: 1) Define steady state (normal behavior metrics), 2) Hypothesize (what should happen under failure), 3) Inject failure, 4) Observe and learn. Start simple: kill random pod, inject latency, block network. Tools: Chaos Monkey, Gremlin, Litmus, AWS FIS. Safety: start in staging, small blast radius, automated rollback, runbooks ready. Experiments: service failure, network partition, resource exhaustion, dependency slowdown. Goal: find weaknesses before production incidents reveal them."
    },
]

# =============================================================================
# OBSERVABILITY ARCHITECTURE
# =============================================================================

OBSERVABILITY = [
    {
        "question": "What are the three pillars of observability?",
        "answer": "Metrics: numeric measurements over time (counters, gauges, histograms). Use for: dashboards, alerting, SLO tracking. Tools: Prometheus, Datadog, CloudWatch. Logs: discrete events with context. Use for: debugging, audit trail, error details. Tools: ELK, Loki, CloudWatch Logs. Traces: request path across services. Use for: latency analysis, dependency mapping, error localization. Tools: Jaeger, Zipkin, X-Ray. Together: metrics alert to problem, traces localize it, logs explain root cause. Correlation: trace ID links all three."
    },
    {
        "question": "How do I design a logging architecture at scale?",
        "answer": "Architecture: app logs → shipper (Fluentd/Vector) → queue (Kafka) → processor → storage (Elasticsearch/S3). Structured logging: JSON format, consistent fields (timestamp, level, service, trace_id). Levels: ERROR (alerts), WARN (investigate), INFO (audit), DEBUG (development). Retention: hot (7 days searchable), warm (30 days), cold (S3 archive). Cost control: sampling, log levels by environment, aggressive retention policies. Security: no PII in logs, access controls. Query: indexed fields for fast search, full-text for exploration."
    },
    {
        "question": "How do I implement SLOs and error budgets?",
        "answer": "SLO (Service Level Objective): target reliability (99.9% availability). SLI (Indicator): measurement (successful requests / total requests). Error budget: allowed failures (0.1% of requests). Implementation: track SLI continuously, alert when burning error budget too fast. Multi-window alerts: 1h burn rate for page, 6h for ticket. Use budget: trade reliability for velocity - if budget remaining, deploy faster. If exhausted, focus on reliability. Examples: latency SLO (95% under 200ms), availability SLO (99.95%), error SLO (<0.1% 5xx). Dashboards: current SLI, budget remaining, burn rate."
    },
    {
        "question": "What is the difference between black-box and white-box monitoring?",
        "answer": "Black-box: external probes testing system as user would. Synthetic monitoring, health checks, uptime monitoring. Detects: user-visible failures, external availability. Tools: Pingdom, synthetic monitors, external health checks. White-box: internal metrics from within system. Request latency, error rates, resource usage, business metrics. Detects: internal issues, capacity problems, performance degradation. Tools: Prometheus, application metrics. Use both: black-box for alerting (user impact), white-box for debugging and capacity planning. Black-box catches what white-box misses (network, DNS)."
    },
    {
        "question": "How do I design alerting that doesn't cause alert fatigue?",
        "answer": "Principles: alert on symptoms (user impact), not causes; page only for urgent issues; every alert actionable. Severity levels: page (immediate action), ticket (business hours), log (investigate later). Reduce noise: aggregate related alerts, suppress during known maintenance, require sustained condition. Design: start with few alerts, add as needed. Each alert needs: clear title, runbook link, dashboard link, escalation path. Review: track alert frequency, remove noisy alerts, tune thresholds. On-call: reasonable rotation, blameless postmortems, learn from incidents."
    },
    {
        "question": "What is event-driven architecture and when should I use it?",
        "answer": "EDA: systems communicate through events (facts about what happened). Components: event producers, event broker (Kafka, EventBridge), event consumers. Benefits: loose coupling, scalability, real-time processing, audit trail. Patterns: event notification (signal change), event-carried state transfer (include data), event sourcing (events as source of truth). Use for: microservices integration, real-time analytics, async workflows. Challenges: eventual consistency, debugging (trace events), ordering guarantees. Avoid for: simple CRUD, strong consistency requirements."
    },
    {
        "question": "How do I implement domain-driven design (DDD) in microservices?",
        "answer": "Core concepts: bounded contexts (microservice boundaries), aggregates (consistency boundaries), domain events (cross-context communication). Process: event storming to discover domains, identify aggregates, define context maps. Per microservice: aggregate root entity, value objects, domain services, repository interface. Communication: domain events via message broker, anti-corruption layers for integration. Benefits: aligned with business, clear boundaries, maintainable. Pitfalls: over-engineering simple domains, distributed transactions, premature decomposition."
    },
    {
        "question": "What is CQRS (Command Query Responsibility Segregation)?",
        "answer": "CQRS: separate read and write models. Commands: change state, return void or result. Queries: return data, no side effects. Implementation: command handlers write to source DB, projections update read-optimized views. Benefits: optimized reads (denormalized), different scaling (read vs write), simpler models. Combined with event sourcing: events as write model, projections as read model. Use for: complex domains, different read/write patterns, high read:write ratio. Avoid for: simple CRUD, if eventual consistency unacceptable."
    },
    {
        "question": "How do I design idempotent APIs?",
        "answer": "Idempotency: same request produces same result regardless of repetition. For GET/PUT/DELETE: naturally idempotent. For POST: use idempotency key (client-provided UUID). Implementation: store idempotency key + response, return cached response on retry. Key considerations: TTL on stored responses (24h typical), scope (per user, per resource). Database: unique constraint on idempotency key, store with result atomically. Benefits: safe retries, handles network failures, duplicate message handling. Design all write operations to be idempotent."
    },
    {
        "question": "What is the strangler fig pattern for legacy migration?",
        "answer": "Strangler fig: gradually replace legacy system by routing requests to new system. Process: 1) Identify seams (natural boundaries), 2) Build new implementation behind facade, 3) Route increasing traffic to new system, 4) Eventually decommission legacy. Implementation: API gateway routes based on path/feature, feature flags for gradual rollout. Benefits: reduce risk, deliver value incrementally, no big bang cutover. Challenges: data sync between systems, testing both paths, shared dependencies. Used by: Amazon, BBC, numerous legacy modernization projects."
    },
    {
        "question": "How do I design for horizontal scalability?",
        "answer": "Principles: stateless services (store state externally), partition data (sharding), async processing (queues), cache aggressively. Stateless: no local session storage, externalize to Redis/database. Data: partition by tenant/user/geography, consistent hashing for distribution. Async: use message queues for work that doesn't need immediate response. Caching: CDN for static content, Redis for session/data cache. Auto-scaling: metrics-based (CPU, queue depth, custom metrics). Avoid: sticky sessions, local file storage, single points of failure."
    },
]

def main():
    """Generate architecture training examples."""
    all_examples = []
    
    # Distributed Systems
    for item in DISTRIBUTED_SYSTEMS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "architecture",
                "subdomain": "distributed_systems",
                "response_type": "concepts"
            }
        })
    
    # Enterprise Patterns
    for item in ENTERPRISE_PATTERNS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "architecture",
                "subdomain": "enterprise_patterns",
                "response_type": "concepts"
            }
        })
    
    # Integration Patterns
    for item in INTEGRATION_PATTERNS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "architecture",
                "subdomain": "integration_patterns",
                "response_type": "concepts"
            }
        })
    
    # Resilience Patterns
    for item in RESILIENCE_PATTERNS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "architecture",
                "subdomain": "resilience_patterns",
                "response_type": "concepts"
            }
        })
    
    # Observability
    for item in OBSERVABILITY:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "architecture",
                "subdomain": "observability",
                "response_type": "concepts"
            }
        })
    
    # Save to file
    output_file = DATA_DIR / "architecture.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"  [OK] Saved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
