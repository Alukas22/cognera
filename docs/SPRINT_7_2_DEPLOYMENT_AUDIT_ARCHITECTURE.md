# Sprint 7.2 Architecture: Deployment Audit and Runtime Version Traceability

Status: Implementation blueprint  
Scope: Deployment traceability, runtime commit visibility, and production auditability

## 1. Problem

Production appears out of sync with recent repository commits, but runtime metadata does not expose commit or branch identity.

Without explicit runtime version telemetry, deployment drift cannot be proven or remediated quickly.

## 2. Architecture

### 2.1 Backend Version Contract

Extend `GET /version` to return immutable deployment metadata:

1. `commit_sha`
2. `build_timestamp`
3. `git_branch`
4. `application_version`

Backward compatibility is maintained by preserving existing keys (`app_name`, `version`).

### 2.2 Runtime Metadata Sources

Version metadata is read from environment variables populated by CI/deployment:

1. `GIT_COMMIT_SHA` (fallback `RAILWAY_GIT_COMMIT_SHA`)
2. `GIT_BRANCH` (fallback `RAILWAY_GIT_BRANCH`)
3. `BUILD_TIMESTAMP` (fallback unknown)
4. `APP_VERSION` (existing app version contract)

### 2.3 Docker Build Injection

Docker build arguments are mapped into runtime environment values so packaged images can be traced independently of source checkout state.

### 2.4 Frontend Visibility

The application footer renders runtime version telemetry from `GET /version`, showing commit, branch, build timestamp, and version.

## 3. Audit Flow

1. Read latest pushed SHA from remote branch.
2. Query production `GET /version`.
3. Compare deployed SHA and branch to remote head SHA.
4. Compare production asset fingerprints with local build output.
5. Correlate deployed SHA with latest CI run SHA.
6. Flag cache or stale artifact risk.

## 4. Constraints

1. No puzzle-generation behavior changes.
2. No API breaking changes.
3. Deterministic metadata contract.
4. Visible runtime traceability in UI.
