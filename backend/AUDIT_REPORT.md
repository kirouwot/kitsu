# DB Constraints & ORM Invariants Audit Report
**STABILIZATION MODE - TASK A-6**
Generated: 412.197691198

## Summary
- **CRITICAL**: 2
- **WARNING**: 2
- **Total Issues**: 4

## Findings

| Table | Field/Constraint | Type | Severity | Model | Database | Recommendation |
|-------|------------------|------|----------|-------|----------|----------------|
| role_permissions | role_id, permission_id | MISSING_LOGICAL_UNIQUE | **CRITICAL** | No UniqueConstraint defined | No UNIQUE constraint in DB | Add UniqueConstraint(role_id, permission_id) to prevent duplicate permission grants |
| user_roles | user_id, role_id | MISSING_LOGICAL_UNIQUE | **CRITICAL** | No UniqueConstraint defined | No UNIQUE constraint in DB | Add UniqueConstraint(user_id, role_id) to prevent duplicate role assignments |
| refresh_tokens | token_hash | INDEX_NOT_IN_MODEL | **WARNING** | No index=True | Index exists: ix_refresh_tokens_token_hash | Add index=True to model or remove index from DB |
| refresh_tokens | user_id | INDEX_NOT_IN_MODEL | **WARNING** | No index=True | Index exists: ix_refresh_tokens_user_id | Add index=True to model or remove index from DB |

## Detailed Analysis

### CRITICAL Issues

#### 1. role_permissions.role_id, permission_id - MISSING_LOGICAL_UNIQUE
- **Model**: No UniqueConstraint defined
- **Database**: No UNIQUE constraint in DB
- **Recommendation**: Add UniqueConstraint(role_id, permission_id) to prevent duplicate permission grants

#### 2. user_roles.user_id, role_id - MISSING_LOGICAL_UNIQUE
- **Model**: No UniqueConstraint defined
- **Database**: No UNIQUE constraint in DB
- **Recommendation**: Add UniqueConstraint(user_id, role_id) to prevent duplicate role assignments

### WARNING Issues

#### 1. refresh_tokens.token_hash - INDEX_NOT_IN_MODEL
- **Model**: No index=True
- **Database**: Index exists: ix_refresh_tokens_token_hash
- **Recommendation**: Add index=True to model or remove index from DB

#### 2. refresh_tokens.user_id - INDEX_NOT_IN_MODEL
- **Model**: No index=True
- **Database**: Index exists: ix_refresh_tokens_user_id
- **Recommendation**: Add index=True to model or remove index from DB
