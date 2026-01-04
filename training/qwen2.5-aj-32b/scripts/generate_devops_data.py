#!/usr/bin/env python3
"""
Generate DevOps and CI/CD training data for AJ fine-tuning.
Covers GitHub Actions, Azure DevOps, Jenkins, deployment strategies, and infrastructure automation.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"

SYSTEM_PROMPT = "You are AJ, an AI coding assistant. You are helping with DevOps, CI/CD, and automation tasks."

# =============================================================================
# GITHUB ACTIONS
# =============================================================================

GITHUB_ACTIONS = [
    {
        "question": "How do I set up a basic GitHub Actions workflow?",
        "answer": "Create .github/workflows/ci.yml. Structure: name, on (triggers), jobs. Jobs contain steps with uses (actions) or run (commands). Basic example: on: [push, pull_request], jobs: build: runs-on: ubuntu-latest, steps: checkout, setup-node, npm install, npm test. Triggers: push, pull_request, schedule, workflow_dispatch (manual). Environment: runs-on sets OS. Secrets: ${{ secrets.NAME }}. Matrix builds for multiple versions."
    },
    {
        "question": "How do I cache dependencies in GitHub Actions?",
        "answer": "Use actions/cache. Key identifies cache, restore-keys for fallbacks. Example for npm: uses: actions/cache@v3, with: path: ~/.npm, key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}. For Python: path: ~/.cache/pip, key with requirements.txt hash. Built-in caching: actions/setup-node has cache option. Cache is scoped to branch. Restore order: exact key match, then restore-keys prefix match. 10GB limit per repo."
    },
    {
        "question": "How do I use secrets in GitHub Actions?",
        "answer": "Add secrets in repo Settings → Secrets. Access: ${{ secrets.SECRET_NAME }}. Don't echo secrets (masked but risky). Environment secrets: scoped to specific environment. Organization secrets: shared across repos. GITHUB_TOKEN: automatic, scoped to repo. For multi-line secrets: base64 encode. Encrypted at rest, masked in logs. Don't use in if conditions directly. Pass to steps as env: MY_VAR: ${{ secrets.SECRET }}."
    },
    {
        "question": "How do I create a reusable GitHub Actions workflow?",
        "answer": "Reusable workflows: workflow_call trigger. Define inputs and secrets. Call with: uses: owner/repo/.github/workflows/file.yml@ref, with: (inputs), secrets: (secrets). Can inherit secrets with secrets: inherit. Reusable workflow runs in caller's context. Composite actions: action.yml with runs: using: composite, steps. Composite for sharing steps, reusable workflows for complete workflows. Limit: 4 levels of nesting."
    },
    {
        "question": "How do I run jobs in parallel vs sequentially in GitHub Actions?",
        "answer": "Jobs run in parallel by default. Sequential: use needs keyword. needs: [job1, job2] waits for both. Can depend on specific job output. Matrix creates parallel variants: strategy: matrix: node: [14, 16, 18]. Fail-fast: true (default) cancels other jobs on failure. Max-parallel limits concurrent jobs. Artifacts: share data between jobs using actions/upload-artifact and download-artifact. If-else: if: ${{ needs.job1.result == 'success' }}."
    },
    {
        "question": "How do I deploy to different environments with GitHub Actions?",
        "answer": "Use environment keyword in job. Environments: Settings → Environments. Features: required reviewers, wait timer, deployment branches, secrets scoped to environment. Example: environment: name: production, url: ${{ steps.deploy.outputs.url }}. Protection rules: require approval for production. GitHub deployments API tracks status. Concurrency: group: production, cancel-in-progress: false prevents concurrent deploys."
    },
    {
        "question": "How do I trigger GitHub Actions workflow from another workflow?",
        "answer": "Options: repository_dispatch event, workflow_dispatch, or workflow_call. repository_dispatch: POST to /repos/{owner}/{repo}/dispatches with event_type. Trigger in workflow: on: repository_dispatch: types: [my-event]. workflow_dispatch: manual trigger with inputs. workflow_call: direct call to reusable workflow. Use GITHUB_TOKEN or PAT for API calls. workflow_run: trigger after another workflow completes."
    },
    {
        "question": "How do I use matrix builds effectively?",
        "answer": "Matrix runs job with multiple configurations. strategy: matrix: os: [ubuntu, windows], node: [16, 18]. Creates 4 jobs. Include: add specific combinations. Exclude: remove combinations. fail-fast: false continues other jobs on failure. Access values: ${{ matrix.os }}. Dynamic matrix: use output from previous job. max-parallel: limit concurrent jobs. Great for: cross-platform testing, multiple language versions, configuration combinations."
    },
]

# =============================================================================
# AZURE DEVOPS
# =============================================================================

AZURE_DEVOPS = [
    {
        "question": "What is the difference between YAML and Classic pipelines in Azure DevOps?",
        "answer": "YAML: pipeline as code, version controlled, triggers in file, full feature access, recommended approach. Classic: UI-based, stored in Azure DevOps, easier for beginners, limited to Release pipelines for some features. YAML advantages: review changes via PR, branch-specific pipelines, templates and sharing. Classic advantages: visual editor, quick setup. Migration: export Classic to YAML. Multi-stage YAML: combines build and release."
    },
    {
        "question": "How do I use variables in Azure DevOps pipelines?",
        "answer": "Define: variables: section in YAML, variable groups, pipeline settings UI. Syntax: $(variableName) or ${{ variables.variableName }}. Secret variables: set in UI with lock icon, or variable groups linked to Key Vault. Runtime vs compile-time: $() evaluated at runtime, ${{ }} at compile time. Output variables: share between jobs with isOutput=true. Predefined: $(Build.SourceBranch), $(System.DefaultWorkingDirectory). Variable groups: reusable across pipelines."
    },
    {
        "question": "How do I set up CI/CD in Azure DevOps?",
        "answer": "Build pipeline (CI): trigger on push/PR, build code, run tests, create artifacts. Release pipeline (CD): triggered by artifact, deploy to environments. Modern approach: multi-stage YAML with stages for build, test, deploy. Stages: stage: Build, stage: DeployDev, stage: DeployProd. Environments: define with approvals and checks. Service connections: authenticate to Azure, Docker registries, etc. Pipeline templates for reuse."
    },
    {
        "question": "How do I create pipeline templates in Azure DevOps?",
        "answer": "Templates: reusable YAML fragments. Types: stage template, job template, step template, variable template. Reference: template: path/to/template.yml. Parameters: parameters: section with defaults. Call: template: with parameters:. Store in same repo or separate template repo. Extends template: enforce structure with extends. Best practice: common steps in templates, customize with parameters. Security: extends with resources for required approvals."
    },
    {
        "question": "What are environments in Azure DevOps?",
        "answer": "Environments: target deployment destination with approvals and checks. Define in Pipelines → Environments. YAML: environment: name. Checks: approvals, branch control, business hours, Azure function, REST API. Deployment strategy: runOnce, rolling, canary. Resources: Kubernetes, VMs, virtual environments. Deployment history: tracked per environment. Lock: exclusive lock prevents concurrent deployments. Best for: production gates, compliance requirements."
    },
    {
        "question": "How do I connect Azure DevOps to Azure resources?",
        "answer": "Service connections: Settings → Service connections. Azure Resource Manager: workload identity (recommended), service principal, managed identity. Authentication: automatic (creates app registration) or manual (existing principal). Scope: subscription, resource group, or management group. Use in pipeline: azureSubscription: 'connection-name'. AzureCLI task, AzureWebApp task. Grant pipeline permission or require approval. Secure with limited scope."
    },
]

# =============================================================================
# JENKINS
# =============================================================================

JENKINS = [
    {
        "question": "What is a Jenkinsfile and how do I write one?",
        "answer": "Jenkinsfile: pipeline as code in Groovy DSL. Two syntaxes: Declarative (simpler, structured) and Scripted (flexible, Groovy). Declarative: pipeline { agent any; stages { stage('Build') { steps { sh 'npm install' } } } }. Agent: where to run (any, docker, label). Post: always, success, failure actions. Environment: define env vars. Parameters: user inputs. Store in repo root. Multibranch: Jenkinsfile per branch."
    },
    {
        "question": "How do I set up a Jenkins multibranch pipeline?",
        "answer": "Multibranch: discovers branches/PRs automatically. Create: New Item → Multibranch Pipeline. Configure: branch sources (Git/GitHub/Bitbucket), Jenkinsfile path, build strategies. Scan: discovers branches with Jenkinsfile. Branch filtering: include/exclude patterns. Build strategies: all branches, only PRs, tags. Organization folders: scan entire GitHub org. Index triggers: periodic scan or webhook. Orphaned items: prune deleted branches."
    },
    {
        "question": "How do I use credentials in Jenkins?",
        "answer": "Manage: Credentials → System → Global. Types: username/password, secret text, secret file, SSH key, certificate. Scope: global or specific folder. In pipeline: credentials('credential-id') or withCredentials block. Example: withCredentials([usernamePassword(credentialsId: 'id', usernameVariable: 'USER', passwordVariable: 'PASS')]) { sh 'command' }. Environment binding: environment { SECRET = credentials('id') } creates SECRET_USR and SECRET_PSW."
    },
    {
        "question": "How do I parallelize Jenkins builds?",
        "answer": "Parallel stages: parallel { stage('Test') { ... } stage('Lint') { ... } }. Each parallel branch runs concurrently. FailFast: failFast true stops others on first failure. Matrix: matrix { axes { axis { name 'OS'; values 'linux', 'windows' } } stages { ... } }. Combine axes for combinations. Exclude: exclude certain combinations. Parallel steps: parallel directive with closures. Great for: multi-platform testing, independent tasks."
    },
    {
        "question": "How do I set up Jenkins agents/nodes?",
        "answer": "Agents execute builds. Types: permanent (always connected), cloud (on-demand). Add: Manage Jenkins → Nodes. Connection: SSH, JNLP, Docker, Kubernetes. Labels: identify agents for specific jobs. Node: agent { label 'linux' }. Docker agent: agent { docker { image 'node:16' } }. Kubernetes plugin: dynamic pods. Executors: concurrent builds per agent. Best practice: containerized agents, immutable, security-hardened."
    },
]

# =============================================================================
# CI/CD BEST PRACTICES
# =============================================================================

CICD_CONCEPTS = [
    {
        "question": "What are CI/CD best practices?",
        "answer": "CI: commit often, build on every push, fast feedback (under 10 min), fix broken builds immediately, comprehensive tests. CD: automate everything, consistent environments, immutable artifacts, infrastructure as code. Pipeline: version control pipeline config, keep pipelines fast, parallelize tests. Security: secrets management, scan dependencies, sign artifacts. Culture: trunk-based development, feature flags, blameless postmortems. Monitor deployments, easy rollbacks."
    },
    {
        "question": "What is trunk-based development?",
        "answer": "Trunk-based: all developers commit to main (trunk) frequently. Short-lived feature branches (< 1 day ideally). Small commits, continuous integration. Avoid: long-lived branches, merge conflicts. Enable with: feature flags (hide incomplete features), comprehensive tests, fast CI. Benefits: simpler branching, faster integration, fewer conflicts. Release: from trunk with release branches or continuous deployment. Contrast with GitFlow: more branches, less frequent integration."
    },
    {
        "question": "What is a deployment pipeline?",
        "answer": "Deployment pipeline: automated path from commit to production. Stages: commit (compile, unit tests), acceptance (integration tests), staging (performance, smoke tests), production. Each stage is gate: fails = stops progression. Artifacts: built once, promoted through stages. Environments: increasingly production-like. Automated: no manual steps except approvals. Traceable: track commit through pipeline. Fast: optimize for quick feedback. Pipeline as code: version controlled."
    },
    {
        "question": "How do I implement feature flags?",
        "answer": "Feature flags: toggle features without deployment. Use cases: gradual rollout, A/B testing, kill switch, trunk-based dev. Implementation: if(featureEnabled('newUI')) { showNewUI() }. Storage: config file, database, feature flag service (LaunchDarkly, Split.io, Unleash). Types: release flags (temporary), ops flags (permanent kill switch), experiment flags. Best practices: clean up old flags, default to off, document flag purpose, don't nest deeply."
    },
    {
        "question": "What is GitOps?",
        "answer": "GitOps: Git as single source of truth for infrastructure and applications. Principles: declarative (desired state in YAML), versioned (Git history), automated (agents sync state). Tools: ArgoCD, Flux. Workflow: PR with changes → review → merge → agent syncs cluster. Benefits: audit trail, easy rollback (git revert), consistent environments. Pull-based: agent pulls from Git (secure, no external access). Compare: traditional push-based CI/CD pushes to cluster."
    },
    {
        "question": "How do I handle database migrations in CI/CD?",
        "answer": "Principles: migrations versioned with code, run automatically, support rollback. Tools: Flyway, Liquibase, Alembic, Rails migrations. CI: test migrations on fresh DB and with data. CD: run migrations before app deployment. Strategies: backward compatible first (add columns, don't remove), expand-contract for breaking changes. Risks: long-running migrations lock tables - plan for maintenance window or online schema change. Never: auto-rollback data migrations without consideration."
    },
    {
        "question": "What is infrastructure as code (IaC)?",
        "answer": "IaC: manage infrastructure through code files. Tools: Terraform, Pulumi, CloudFormation, Bicep. Benefits: version control, reproducible environments, code review for infra changes. Declarative: describe desired state, tool handles achieving it. State management: Terraform state, drift detection. Best practices: modules for reuse, separate envs with workspaces/directories, CI/CD for infra changes, plan before apply. Immutable infrastructure: replace, don't modify."
    },
    {
        "question": "How do I implement canary deployments?",
        "answer": "Canary: route small % of traffic to new version, monitor, increase if healthy. Implementation: Kubernetes with traffic splitting (Istio, Linkerd), cloud load balancers, feature flags by user %. Steps: deploy canary, route 5% traffic, monitor metrics, if healthy increase to 25%, 50%, 100%. Metrics: error rate, latency, business metrics. Automated: progressive delivery controllers (Argo Rollouts, Flagger). Rollback: automatic on metric degradation."
    },
    {
        "question": "What is a build artifact and how should I manage them?",
        "answer": "Artifact: built output (JAR, Docker image, binary, package). Management: artifact repository (Nexus, Artifactory, npm registry, Docker registry). Principles: build once, promote through environments, immutable (don't overwrite versions), signed/verified. Versioning: semantic versioning, commit SHA, timestamp. Retention: keep releases, prune PR/branch artifacts. CI: publish artifact on successful build. CD: pull specific artifact version for deployment."
    },
    {
        "question": "How do I secure CI/CD pipelines?",
        "answer": "Secrets: use secret management, never echo, rotate regularly. Permissions: least privilege for service accounts, scoped tokens. Dependencies: scan for vulnerabilities, use lock files, verify checksums. Pipeline: signed commits, protected branches, required reviews. Artifacts: sign and verify, immutable storage. Audit: log all pipeline activities, alert on anomalies. Supply chain: verify pipeline definition integrity, SLSA framework. Self-hosted runners: isolate, harden, don't run untrusted code."
    },
    {
        "question": "What is observability for CI/CD?",
        "answer": "Pipeline metrics: build time, success rate, queue time, failure patterns. Deployment metrics: deployment frequency, lead time, failure rate, recovery time (DORA metrics). Implementation: pipeline telemetry to metrics platform, dashboards, alerts. Track: flaky tests, slow stages, resource usage. Deployment tracking: which version where, deployment timeline. Benefits: identify bottlenecks, measure improvement, catch degradation. Tools: built-in analytics, export to Prometheus/Datadog."
    },
    # === ADDITIONAL CI/CD CONCEPTS ===
    {
        "question": "What are the DORA metrics and why do they matter?",
        "answer": "DORA (DevOps Research and Assessment) metrics measure software delivery performance. Four keys: 1) Deployment Frequency (how often you deploy to production), 2) Lead Time for Changes (time from commit to production), 3) Change Failure Rate (% of deployments causing incidents), 4) Mean Time to Recovery (time to restore service). Elite performers: multiple deploys/day, <1 hour lead time, <15% failure rate, <1 hour recovery. Track to improve: identify bottlenecks, measure impact of changes. Tools: DORA dashboard plugins, custom metrics pipelines."
    },
    {
        "question": "How do I implement blue-green deployments?",
        "answer": "Blue-green: two identical environments, switch traffic between them. Blue = current production, Green = new version. Process: deploy to Green, test, switch load balancer, Blue becomes standby. Rollback: switch back to Blue (instant). Benefits: zero-downtime deployment, instant rollback, test in production-like env. Considerations: database schema must be backward compatible, session handling, double infrastructure cost (temporary). Implementation: DNS switching, load balancer update, Kubernetes services. Compare to canary: all-or-nothing vs gradual."
    },
    {
        "question": "What is a deployment freeze and when to use it?",
        "answer": "Deployment freeze: period when no deployments to production. Use for: high-risk periods (Black Friday, holidays), major incidents, compliance audits, company events. Implementation: pipeline gates, calendar blocks, approval process override only. Best practices: plan around freezes, establish clear criteria, document exemption process. Anti-pattern: permanent or frequent freezes indicate CI/CD issues. Modern approach: improve deployment safety to reduce need for freezes - feature flags, canary, fast rollback."
    },
    {
        "question": "How do I handle environment-specific configuration in CI/CD?",
        "answer": "Principles: same artifact, different config. Methods: 1) Environment variables (12-factor), 2) Config files per environment, 3) Secret management (HashiCorp Vault, AWS Secrets Manager), 4) Config servers (Spring Cloud Config). CI/CD: inject at deploy time, never bake into artifacts. Patterns: .env files, Kubernetes ConfigMaps/Secrets, parameter stores. Validation: type-check config, fail fast on missing values. Security: encrypt secrets at rest, audit access, rotate regularly."
    },
    {
        "question": "What is continuous verification in deployment pipelines?",
        "answer": "Continuous verification: automated quality gates during deployment. Types: 1) Pre-deployment - tests, security scans, policy checks. 2) Deployment - health checks, smoke tests, synthetic monitoring. 3) Post-deployment - performance baselines, error rate monitoring, business metrics. Tools: Argo Rollouts analysis, Harness continuous verification, custom metric checks. Benefits: catch issues early, automated rollback, confidence in deployments. Implementation: define SLOs, set thresholds, automate decisions."
    },
    {
        "question": "How do I implement self-service CI/CD for developers?",
        "answer": "Self-service: developers own their pipelines without ops bottleneck. Implementation: 1) Pipeline templates - standardized patterns for common scenarios. 2) Platform team provides reusable actions/tasks. 3) Documentation and examples. 4) Sandbox environments for testing. 5) Guardrails - security scanning, policy enforcement. Benefits: faster delivery, reduced ops load, developer ownership. Balance: freedom within constraints. Tools: internal developer platforms, Backstage, custom tooling. Culture: shift-left operations, DevOps enablement."
    },
    # === MORE CI/CD CONCEPTS ===
    {
        "question": "How do I implement rollback strategies in CI/CD?",
        "answer": "Rollback strategies: 1) **Redeploy previous version**: Deploy last-known-good artifact from registry. 2) **Blue-green switch**: Instantly switch load balancer back. 3) **Feature flag disable**: Turn off problematic feature. 4) **Git revert + deploy**: Revert commit, trigger new build. Implementation: keep previous N deployments, immutable artifacts, database backward compatibility. Automated: detect failure metrics, trigger automatic rollback. Manual: clear process, documented runbooks, one-click rollback. Testing: regularly test rollback procedures."
    },
    {
        "question": "What is a monorepo and how does CI/CD differ?",
        "answer": "Monorepo: single repository with multiple projects/services. CI/CD challenges: 1) Build time - don't rebuild unchanged projects. 2) Test scope - only test affected code. 3) Deployment - deploy only changed services. Solutions: path-based triggers (only run on changes to specific dirs), dependency graph (build downstream dependencies), caching (aggressive cache of unchanged parts). Tools: Nx, Turborepo, Bazel, Lerna. Benefits: atomic changes, easier refactoring. Costs: more complex CI/CD, potential for larger blast radius."
    },
    {
        "question": "How do I implement release trains and scheduled releases?",
        "answer": "Release train: fixed schedule deployments (e.g., weekly). Process: 1) Feature freeze before release. 2) Only bug fixes after freeze. 3) Automated release at scheduled time. 4) Skip if critical issues found. Implementation: release branches, tag-based builds, automated promotion. Benefits: predictable cadence, coordinated releases, simpler communication. Compare to continuous deployment: less agile but more controlled. Hybrid: continuous to staging, scheduled to production. Tools: pipeline schedules, release automation."
    },
    {
        "question": "How do I set up pipeline notifications and alerts?",
        "answer": "Notification strategies: 1) **Channel per project**: Dedicated Slack/Teams channel. 2) **On failure only**: Reduce noise, alert on problems. 3) **Smart routing**: Route to commit author. 4) **Escalation**: Page on-call for production failures. Implementation: pipeline-level notifications, webhook integrations, email fallback. Content: clear failure message, link to logs, suggested action. Best practices: don't notify on expected failures (forks, draft PRs), batch notifications, opt-out for personal branches."
    },
    {
        "question": "What is progressive delivery?",
        "answer": "Progressive delivery: gradually roll out changes to limit blast radius. Techniques: 1) **Canary**: Small percentage of traffic first. 2) **Ring deployments**: Deploy to groups (internal → beta → all). 3) **Feature flags**: Enable for specific users/segments. 4) **A/B testing**: Compare variants with metrics. Tools: Argo Rollouts, Flagger, LaunchDarkly, Split.io. Process: deploy, monitor, advance or rollback. Benefits: reduce risk, get early feedback, data-driven decisions. Requires: good observability, automated analysis, quick rollback."
    },
    {
        "question": "How do I implement CI/CD for mobile apps?",
        "answer": "Mobile CI/CD specifics: 1) **Build**: Xcode for iOS, Gradle for Android. 2) **Signing**: Code signing certificates, provisioning profiles. 3) **Testing**: Device farms (Firebase Test Lab, AWS Device Farm). 4) **Distribution**: TestFlight, Google Play internal testing. 5) **App store submission**: Automated via Fastlane, App Store Connect API. Challenges: long build times, simulator/emulator flakiness, signing complexity. Tools: Fastlane, Bitrise, Codemagic, App Center. Consider: separate CI for library vs app."
    },
    {
        "question": "How do I implement disaster recovery in CI/CD?",
        "answer": "DR for CI/CD systems: 1) **Infrastructure as code**: Recreate CI/CD from scratch. 2) **Multi-region runners**: Fail over to alternate runners. 3) **Artifact backup**: Mirror artifacts to alternate storage. 4) **Pipeline config backup**: Store in git (already versioned). 5) **Secret backup**: Vault replication, documented recovery. Scenarios: CI platform outage, runner infrastructure failure, secret store unavailable. RTO/RPO: define acceptable downtime. Testing: regularly test recovery procedures."
    },
    {
        "question": "What is shift-left testing in CI/CD?",
        "answer": "Shift-left: move testing earlier in the development cycle. Practices: 1) **Pre-commit**: Linting, formatting, unit tests locally. 2) **Pre-merge**: Full test suite on PR. 3) **Fast feedback**: Prioritize quick tests first. 4) **Static analysis**: Security scanning, code quality in CI. Benefits: find bugs earlier (cheaper to fix), faster feedback, fewer production issues. Tools: pre-commit hooks, IDE integrations, PR checks. Philosophy: quality is everyone's responsibility, not just QA."
    },
    {
        "question": "How do I handle flaky tests in CI/CD?",
        "answer": "Flaky tests: tests that sometimes pass, sometimes fail non-deterministically. Causes: timing issues, shared state, external dependencies, race conditions. Strategies: 1) **Quarantine**: Isolate known flaky tests, fix separately. 2) **Retry**: Auto-retry failed tests (limited retries). 3) **Track flakiness**: Monitor which tests are flaky. 4) **Fix or delete**: Flaky tests worse than no tests. Detection: track test results over time, flag inconsistent results. Prevention: proper test isolation, mock external dependencies, avoid sleeps."
    },
    {
        "question": "How do I implement compliance and audit trails in CI/CD?",
        "answer": "Compliance requirements: audit trails, approvals, attestations. Implementation: 1) **Immutable logs**: All pipeline runs logged, tamper-proof. 2) **Approvals**: Required approvals before production. 3) **SLSA**: Supply-chain Levels for Software Artifacts. 4) **Signed artifacts**: Cosign, Sigstore for provenance. 5) **Policy as code**: OPA/Rego for enforcement. Audit data: who, what, when, why for every deployment. Tools: GitHub audit log, Azure DevOps compliance features. Standards: SOC2, PCI-DSS, HIPAA have CI/CD requirements."
    },
]

# =============================================================================
# COMMAND EXAMPLES
# =============================================================================

COMMAND_EXAMPLES = [
    {
        "instruction": "Create a GitHub Actions workflow for Node.js CI",
        "response": """Create .github/workflows/ci.yml:

```yaml
name: Node.js CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16, 18, 20]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm test
      - run: npm run build
```"""
    },
    {
        "instruction": "Set up automated Docker build and push in GitHub Actions",
        "response": """Create .github/workflows/docker.yml:

```yaml
name: Docker Build
on:
  push:
    branches: [main]
    tags: ['v*']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```"""
    },
    {
        "instruction": "Create Azure DevOps multi-stage pipeline",
        "response": """Create azure-pipelines.yml:

```yaml
trigger:
  - main

stages:
  - stage: Build
    jobs:
      - job: Build
        pool:
          vmImage: 'ubuntu-latest'
        steps:
          - task: NodeTool@0
            inputs:
              versionSpec: '18.x'
          - script: npm ci
          - script: npm run build
          - publish: $(Build.SourcesDirectory)/dist
            artifact: app

  - stage: DeployDev
    dependsOn: Build
    condition: succeeded()
    jobs:
      - deployment: Deploy
        environment: 'development'
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: app
                - script: echo "Deploy to dev"

  - stage: DeployProd
    dependsOn: DeployDev
    condition: succeeded()
    jobs:
      - deployment: Deploy
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: app
                - script: echo "Deploy to prod"
```"""
    },
    {
        "instruction": "Write a Jenkinsfile for a Python project",
        "response": """Create Jenkinsfile:

```groovy
pipeline {
    agent {
        docker {
            image 'python:3.11'
        }
    }
    
    environment {
        PIP_CACHE_DIR = "${WORKSPACE}/.pip-cache"
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Test') {
            steps {
                sh 'pytest --junitxml=results.xml --cov=src'
            }
            post {
                always {
                    junit 'results.xml'
                }
            }
        }
        
        stage('Build') {
            steps {
                sh 'python -m build'
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([string(credentialsId: 'pypi-token', variable: 'TOKEN')]) {
                    sh 'twine upload -u __token__ -p $TOKEN dist/*'
                }
            }
        }
    }
    
    post {
        failure {
            emailext subject: "Build Failed: ${currentBuild.fullDisplayName}",
                     body: "Check console output at ${env.BUILD_URL}",
                     recipientProviders: [culprits()]
        }
    }
}
```"""
    },
]

def main():
    """Generate DevOps and CI/CD training examples."""
    all_examples = []
    
    # GitHub Actions
    for item in GITHUB_ACTIONS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "devops_cicd",
                "subdomain": "github_actions",
                "response_type": "concepts"
            }
        })
    
    # Azure DevOps
    for item in AZURE_DEVOPS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "devops_cicd",
                "subdomain": "azure_devops",
                "response_type": "concepts"
            }
        })
    
    # Jenkins
    for item in JENKINS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "devops_cicd",
                "subdomain": "jenkins",
                "response_type": "concepts"
            }
        })
    
    # CI/CD Concepts
    for item in CICD_CONCEPTS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "devops_cicd",
                "subdomain": "best_practices",
                "response_type": "concepts"
            }
        })
    
    # Command Examples
    for item in COMMAND_EXAMPLES:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["instruction"],
            "response": item["response"],
            "metadata": {
                "domain": "devops_cicd",
                "subdomain": "code_examples",
                "response_type": "provide_code"
            }
        })
    
    # Save to file
    output_file = DATA_DIR / "devops_cicd.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"  [OK] Saved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
