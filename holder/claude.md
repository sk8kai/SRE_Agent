# SRE Intelligence Layer — CD Repo Scanner

## Metadata

| Field | Value |
|---|---|
| Source | Application CD Repository |
| Audience | Site Reliability Engineers |
| Output | Automated Intelligence Signals |
| Trigger | On commit / On schedule |
| Total Signals | 14 across 4 capability domains |

## Scan Sources

The scanner parses the following file types from the CD repository:

- `hpa.yaml` — Autoscaling config
- `deployment.yaml` — Workload spec
- `pdb.yaml` — Pod disruption budgets
- `service.yaml` — Service definitions
- `pipeline.yaml` / `.github/workflows` — Pipeline configs
- `resourcequota.yaml` — Namespace resource limits
- `networkpolicy.yaml` — Traffic control rules
- `cronjob.yaml` — Scheduled job configs
- `CODEOWNERS` — Ownership definitions
- `configmap.yaml` — Configuration data
- `ingress.yaml` — Ingress routing rules
- `limitrange.yaml` — Container limit defaults
- `statefulset.yaml` — Stateful workload specs
- `daemonset.yaml` — Node-level workload specs

---

## Domain 1: Deployment Risk Intelligence

### Signal 1.1 — Change Risk Scorer
**Priority:** P1 | **Sources:** `git diff`, `pipeline.yaml`, `deployment.yaml`

Diff-level analysis on every PR. Scores each change against deployment history to flag high-probability blast events before merge.

**Detected signals:**
- Resource limit reductions in prod
- Health check removal or modification
- Env var changes without canary gate
- Skipped approval stages detected

---

### Signal 1.2 — Missing Probe Detector
**Priority:** P1 | **Sources:** `deployment.yaml`, `daemonset.yaml`

Scans all Deployment manifests for absent or misconfigured readiness and liveness probes. No probe means silent crash loops during rollout.

**Detected signals:**
- `readinessProbe` absent entirely
- `livenessProbe` with zero `failureThreshold`
- Probe timeout shorter than app startup time
- `initialDelaySeconds: 0` on slow-starting containers

---

### Signal 1.3 — Rollout Strategy Auditor
**Priority:** P1 | **Sources:** `deployment.yaml`

Flags services using `Recreate` strategy in prod, and `RollingUpdate` configs missing `maxUnavailable` or `maxSurge`.

**Detected signals:**
- `strategy: Recreate` in production namespace
- `maxUnavailable` not set (defaults to 25%)
- `maxSurge: 0` + `maxUnavailable: 0` deadlock condition
- No `progressDeadlineSeconds` defined

---

### Signal 1.4 — Image Tag Hygiene Report
**Priority:** P2 | **Sources:** `deployment.yaml`, `statefulset.yaml`, `cronjob.yaml`, `daemonset.yaml`

Scans all image references across all environments. Flags non-deterministic references that make rollbacks unreliable.

**Detected signals:**
- `latest` tag in any environment
- Digest-pinned vs tag-only split by namespace
- Images not matching approved registry prefixes
- Same image tag used across prod and staging
- Images with no registry specified (implicit Docker Hub)
- Stale images: last updated more than 90 days ago

---

### Signal 1.5 — Pipeline Gate Compliance
**Priority:** P2 | **Sources:** `pipeline.yaml`, `.github/workflows`

Verifies every pipeline has required PTD → PTO gates: smoke tests, canary steps, approval sign-offs. Flags services that bypass governance stages.

**Detected signals:**
- No canary stage before prod promotion
- Approval gates missing in prod pipelines
- Smoke test step absent post-deploy
- Rollback step not defined

---

## Domain 2: Scaling & Capacity Intelligence

### Signal 2.1 — HPA Boundary Auditor
**Priority:** P1 | **Sources:** `hpa.yaml`

Detects HPA configurations that are silently disabled or structurally broken. Most common case: `minReplicas` = `maxReplicas` = current replica count.

**Detected signals:**
- `minReplicas` = `maxReplicas` (HPA effectively disabled)
- `maxReplicas` set below current running count
- `targetCPUUtilizationPercentage: 100`
- CPU-only scaling configured on I/O-bound services

---

### Signal 2.2 — PDB + HPA Conflict Detector
**Priority:** P1 | **Sources:** `pdb.yaml`, `hpa.yaml`

Surfaces the silent availability trap: `PDB minAvailable` >= `HPA minReplicas` means voluntary disruptions are permanently blocked.

**Detected signals:**
- `PDB minAvailable` >= `HPA minReplicas`
- `PDB maxUnavailable: 0` with single-replica HPA
- No PDB defined for stateful workloads
- PDB covers pods with no matching HPA

---

### Signal 2.3 — Resource Limit/Request Ratio
**Priority:** P2 | **Sources:** `deployment.yaml`, `limitrange.yaml`

Identifies over-provisioned and under-provisioned services. Flags where limits equal requests (no burst headroom) and where no limits exist at all.

**Detected signals:**
- CPU limit = CPU request (no burstability)
- Memory limit absent (OOM risk uncontrolled)
- Requests set without any limits defined
- Ratio > 10x (over-provisioned, noisy neighbor risk)

---

### Signal 2.4 — Namespace Quota Saturation
**Priority:** P2 | **Sources:** `resourcequota.yaml`, `deployment.yaml`

Compares declared resource requests across all services against namespace ResourceQuota ceilings. Flags namespaces approaching exhaustion.

**Detected signals:**
- Sum of requests > 80% of quota ceiling
- Namespaces with no quota defined
- CPU vs memory saturation imbalance
- PVC quota vs active claims ratio

---

### Signal 2.5 — Scaling Headroom Calculator
**Priority:** P2 | **Sources:** `hpa.yaml`, `resourcequota.yaml`

Computes available replica headroom per service. Services within 20% of their HPA maxReplicas ceiling at declared target utilization are flagged for pre-emptive review.

**Detected signals:**
- Headroom < 20% at target CPU utilization
- Scale-up buffer vs cluster node capacity
- Services with no custom metric scaling configured
- Historical spike pattern vs max replica ceiling

---

### Signal 2.6 — CronJob Overlap Detector
**Priority:** P3 | **Sources:** `cronjob.yaml`, `resourcequota.yaml`

Detects CronJobs with overlapping schedules and permissive concurrency policies. Concurrent jobs are a leading cause of noisy-neighbor incidents.

**Detected signals:**
- `concurrencyPolicy: Allow` on resource-heavy jobs
- Jobs overlapping in schedule within the same namespace
- `startingDeadlineSeconds` not set
- No resource limits on CronJob pods

---

## Domain 3: Resilience & Blast Radius Intelligence

### Signal 3.1 — Dependency & Blast Radius Map
**Priority:** P1 | **Sources:** `networkpolicy.yaml`, `service.yaml`, `ingress.yaml`

Builds a live dependency graph from Service selectors, Ingress backends, and NetworkPolicy rules. For each service, shows what breaks if it goes down and what it can reach.

**Detected signals:**
- Upstream and downstream dependency chains
- Services with no NetworkPolicy (implicit allow-all)
- Single points of failure in service mesh
- Circular dependency detection
- Cross-namespace traffic paths

---

### Signal 3.2 — Zero-Trust Gap Map
**Priority:** P1 | **Sources:** `networkpolicy.yaml`, `service.yaml`

Every service without a NetworkPolicy is implicitly allow-all. This signal surfaces the full gap map — which services are open to lateral movement from any compromised pod.

**Detected signals:**
- Services with no ingress NetworkPolicy
- Services with no egress NetworkPolicy
- Overly broad `podSelector` (matches all pods)
- Allows traffic from all namespaces (no `namespaceSelector`)
- Sensitive services reachable from dev namespace

---

### Signal 3.3 — Availability Guarantee Gap Detector
**Priority:** P2 | **Sources:** `pdb.yaml`, `deployment.yaml`, `statefulset.yaml`

Finds production workloads without a PodDisruptionBudget. These are invisible to Kubernetes voluntary disruption controls — node drains silently take them down.

**Detected signals:**
- Deployments with `replicas > 1` but no PDB
- StatefulSets without `minAvailable` set
- PDB selector mismatch (covers zero actual pods)
- PDB defined but deployment scaled to 1

---

### Signal 3.4 — Deployment Drift Detector
**Priority:** P2 | **Sources:** `deployment.yaml`, `configmap.yaml`, live k8s API

Compares what is declared in the CD repo against what is actually running per environment. Surfaces configuration drift before it becomes an incident during the next deployment.

**Detected signals:**
- Image version mismatch: repo spec vs running pod
- Replica count drift from declared spec
- Resource limits changed out-of-band
- ConfigMap values modified post-deploy
- Env-specific overrides not present in repo

---

## Domain 4: Operational Intelligence

### Signal 4.1 — Auto-Generated Runbooks
**Priority:** P1 | **Sources:** `deployment.yaml`, `pipeline.yaml`, `service.yaml`

Parses deployment configs, rollout strategies, and health check definitions to auto-generate environment-specific runbooks with real commands and actual values.

**Generated content per service:**
- Deploy, rollback, and scale commands
- Health check endpoints and expected responses
- Canary promotion and abort procedures
- Known startup and shutdown sequences

---

### Signal 4.2 — Incident Context Enricher
**Priority:** P1 | **Sources:** git history, pipeline logs, alertmanager

When an alert fires, automatically correlates it with recent deployments. Surfaces the last 3 deploys per affected service with diff summaries and risk scores.

**Generated content per incident:**
- Alert to last deploy time delta
- What changed: image, config, limits, probes
- Who deployed and which pipeline ran
- Pre-generated rollback command

---

### Signal 4.3 — Ownership & Escalation Map
**Priority:** P2 | **Sources:** `CODEOWNERS`, `pipeline.yaml`, namespace labels

From CODEOWNERS, pipeline approval groups, and namespace labels, generates a live ownership registry mapping services to teams, approvers, and on-call contacts.

**Generated content:**
- Service → team → on-call mapping
- Approval group per environment per service
- Services with no CODEOWNERS entry flagged
- Escalation path generated per namespace

---

## Source to Signal Mapping

| Source File | Intelligence Signals Enabled |
|---|---|
| `hpa.yaml` | HPA boundary audit, PDB conflict detection, Scaling headroom calc, Pre-deploy readiness score |
| `deployment.yaml` | Missing probe detector, Rollout strategy risk, Image tag hygiene, Resource ratio analysis, Drift detector |
| `networkpolicy.yaml` | Zero-trust gap map, Blast radius map, Lateral movement exposure |
| `pipeline.yaml` | Gate compliance audit, Auto-generated runbooks, Change risk scoring, Ownership map |
| `pdb.yaml` | PDB + HPA conflict, Availability gap detector, Node drain safety check |
| `resourcequota.yaml` | Namespace saturation forecast, Noisy neighbor risk score, Capacity planning feed |
| `cronjob.yaml` | CronJob overlap detection, Noisy neighbor prevention |
| `CODEOWNERS` | Ownership map, Escalation paths |
| `configmap.yaml` | Drift detection, Runbook generation |
| `ingress.yaml` | Blast radius map, Dependency graph |

---

## Build Priority Matrix

Signals ranked by SRE incident reduction potential. Effort is measured in sprints (1 sprint = approximately 2 weeks).

| Rank | Signal | Primary Source | Impact | Effort | Wires Into |
|---|---|---|---|---|---|
| 1 | HPA Boundary Auditor | `hpa.yaml` | Critical | 1 sprint | Pre-deploy gate, alerts |
| 2 | Missing Probe Detector | `deployment.yaml` | Critical | 1 sprint | Pre-deploy gate, runbooks |
| 3 | PDB + HPA Conflict Detector | `pdb.yaml` + `hpa.yaml` | Critical | 2 sprints | Availability guarantees |
| 4 | Change Risk Scorer | git diff + pipeline | Critical | 2 sprints | PR checks, PTD workflow |
| 5 | Incident Context Enricher | git history + alerts | Critical | 2 sprints | PagerDuty, Slack, runbooks |
| 6 | Auto-Generated Runbooks | deployment + pipeline | High | 2 sprints | Incident response, onboarding |
| 7 | Rollout Strategy Auditor | `deployment.yaml` | High | 1 sprint | Pre-deploy gate |
| 8 | Blast Radius Map | networkpolicy + service | High | 3 sprints | Incident triage, capacity |
| 9 | Resource Limit/Request Ratio | deployment + limitrange | High | 1 sprint | Capacity planning, cost |
| 10 | Deployment Drift Detector | deployment + k8s API | High | 2 sprints | Compliance, alerting |
| 11 | Availability Guarantee Gap | pdb + deployment | High | 1 sprint | Node drain procedures |
| 12 | Zero-Trust Gap Map | `networkpolicy.yaml` | Medium | 2 sprints | Security posture review |
| 13 | Namespace Quota Saturation | `resourcequota.yaml` | Medium | 1 sprint | Capacity planning |
| 14 | CronJob Overlap Detector | `cronjob.yaml` | Medium | 1 sprint | Noisy neighbor prevention |

---

## Recommended Build Phases

### Phase 1 — Quick Wins (Sprint 1)
**Signals:** HPA Auditor, Missing Probe Detector, Rollout Strategy Auditor

Pure YAML parsing. No live cluster access needed. Immediate PR gate value. All three together form a pre-deploy readiness score.

### Phase 2 — High Leverage (Sprints 2–3)
**Signals:** Change Risk Scorer, Incident Context Enricher, Auto-Generated Runbooks

Requires git history access and alertmanager integration. Directly reduces MTTR and toil during incidents. Wires into PTD → PTO workflow.

### Phase 3 — Strategic Layer (Sprint 4+)
**Signals:** Blast Radius Map, Drift Detector, Zero-Trust Gap Map

Requires live cluster API access. Produces long-lived operational artifacts: dependency graphs, ownership registries, and network topology maps.

---

## Priority Legend

| Priority | Meaning |
|---|---|
| P1 | Incident Risk — directly causes or masks outages |
| P2 | Reliability Risk — degrades resilience or observability |
| P3 | Operational Debt — increases toil or reduces confidence |gi