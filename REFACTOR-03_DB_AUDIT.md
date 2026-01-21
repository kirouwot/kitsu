# REFACTOR-03: Database Consistency & Contract Alignment Audit

**Generated:** 2026-01-21T06:59:20.265505Z

**Status:** SCHEMA & CONTRACT ANALYSIS

**Mode:** Template for database audit (database currently empty)

---

## Executive Summary

This audit report provides a comprehensive template for auditing the database
against the RBAC contract defined in `backend/app/auth/rbac_contract.py`.

- **Total Permissions in Contract:** 26
- **Total Roles in Contract:** 8
  - User Roles: 6
  - System Roles: 2
- **Role-Permission Mappings Defined:** 8

---

## RBAC Contract Overview

### Hard Invariants

The following security invariants MUST be enforced:

1. ❌ **NO wildcard permissions** - All permissions must be explicit
2. ❌ **NO legacy colon format** - Use dot notation only (e.g., `admin.parser.settings`)
3. ❌ **NO admin permissions for system actors** - Parser ≠ Admin
4. ❌ **NO mixing actor types** - System roles cannot be assigned to users and vice versa
5. ✅ **ALL permissions must be in ALLOWED_PERMISSIONS** - No implicit permissions

### Permission Categories


**Anime Permissions (7):**
- `anime.create`
- `anime.delete`
- `anime.edit`
- `anime.lock`
- `anime.publish`
- `anime.unlock`
- `anime.view`

**Episode Permissions (6):**
- `episode.create`
- `episode.delete`
- `episode.edit`
- `episode.lock`
- `episode.unlock`
- `episode.view`

**Parser Permissions (3):**
- `parser.configure`
- `parser.override_lock`
- `parser.run`

**Admin Permissions (7):**
- `admin.parser.emergency`
- `admin.parser.logs`
- `admin.parser.settings`
- `admin.roles.manage`
- `admin.statistics.view`
- `admin.users.manage`
- `admin.users.view`

**Audit Permissions (1):**
- `audit.view`

**Security Permissions (2):**
- `security.ban.ip`
- `security.unban.ip`

### User Roles

These roles can ONLY be assigned to `actor_type='user'`:


**`admin`** (19 permissions):
  - `admin.parser.logs`
  - `admin.parser.settings`
  - `admin.statistics.view`
  - `admin.users.view`
  - `anime.create`
  - `anime.delete`
  - `anime.edit`
  - `anime.lock`
  - `anime.publish`
  - `anime.unlock`
  - `anime.view`
  - `audit.view`
  - `episode.create`
  - `episode.delete`
  - `episode.edit`
  - `episode.lock`
  - `episode.unlock`
  - `episode.view`
  - `parser.configure`

**`editor`** (6 permissions):
  - `anime.create`
  - `anime.edit`
  - `anime.view`
  - `episode.create`
  - `episode.edit`
  - `episode.view`

**`moderator`** (7 permissions):
  - `anime.edit`
  - `anime.lock`
  - `anime.view`
  - `audit.view`
  - `episode.edit`
  - `episode.lock`
  - `episode.view`

**`super_admin`** (25 permissions):
  - `admin.parser.emergency`
  - `admin.parser.logs`
  - `admin.parser.settings`
  - `admin.roles.manage`
  - `admin.statistics.view`
  - `admin.users.manage`
  - `admin.users.view`
  - `anime.create`
  - `anime.delete`
  - `anime.edit`
  - `anime.lock`
  - `anime.publish`
  - `anime.unlock`
  - `anime.view`
  - `audit.view`
  - `episode.create`
  - `episode.delete`
  - `episode.edit`
  - `episode.lock`
  - `episode.unlock`
  - `episode.view`
  - `parser.configure`
  - `parser.override_lock`
  - `security.ban.ip`
  - `security.unban.ip`

**`support`** (4 permissions):
  - `admin.users.view`
  - `anime.view`
  - `audit.view`
  - `episode.view`

**`user`** (2 permissions):
  - `anime.view`
  - `episode.view`

### System Roles

These roles can ONLY be assigned to `actor_type='system'`:


**`parser_bot`** (8 permissions):
  - `anime.create`
  - `anime.edit`
  - `anime.view`
  - `episode.create`
  - `episode.edit`
  - `episode.view`
  - `parser.override_lock`
  - `parser.run`

**`worker_bot`** (3 permissions):
  - `anime.view`
  - `episode.view`
  - `parser.run`

---

## Database Audit Checklist


When running against a live database, verify the following:

### STAGE 1: Inventory

- [ ] Query all permissions from `permissions` table
- [ ] Query all roles from `roles` table
- [ ] Query all role-permission mappings from `role_permissions` table
- [ ] Query all user-role assignments from `user_roles` table
- [ ] Query all users from `users` table
- [ ] Check for duplicate permission names
- [ ] Check for duplicate role names
- [ ] Check for duplicate role-permission mappings
- [ ] Identify roles without permissions
- [ ] Identify permissions without roles
- [ ] Identify users without roles

### STAGE 2: Contract Compliance

- [ ] **Legacy Permissions Check:**
  - Find all permissions with `:` (colon) instead of `.` (dot)
  - Example forbidden: `admin:parser.settings`, `parser:*`
  - Example correct: `admin.parser.settings`
- [ ] **Wildcard Permissions Check:**
  - Find all permissions ending with `*`, `.*`, or `:*`
  - These are FORBIDDEN and must be removed immediately
- [ ] **Unknown Permissions Check:**
  - Find permissions in DB that are NOT in `rbac_contract.ALLOWED_PERMISSIONS`
  - Action: Either add to contract OR delete from DB
- [ ] **Unknown Roles Check:**
  - Find roles in DB that are NOT in `rbac_contract.ALL_ROLES`
  - Action: Either add to contract OR delete from DB
- [ ] **Role-Permission Mapping Check:**
  - For each role, compare DB permissions vs `ROLE_PERMISSION_MAPPINGS`
  - Identify extra permissions (in DB but not in contract)
  - Identify missing permissions (in contract but not in DB)
- [ ] **System Role Violation Check:**
  - Verify NO system role (`parser_bot`, `worker_bot`) has admin permissions
  - This is a HARD INVARIANT: Parser ≠ Admin
- [ ] **Actor Type Segregation Check:**
  - Verify no users have system roles
  - Verify no system actors have user roles

### STAGE 3: Data Quality

- [ ] Check for users with multiple system roles (should be 0)
- [ ] Check for inactive users with active roles
- [ ] Check for roles marked as inactive but still assigned
- [ ] Verify all `is_system` flags are consistent with role type

---

## Expected Database State


Based on the contract, the database SHOULD contain:


### Expected Permissions Table

Total: 26 permissions

| Permission Name | Resource | Action | Category |
|-----------------|----------|--------|----------|
| `admin.parser.emergency` | admin | emergency | Admin |
| `admin.parser.logs` | admin | logs | Admin |
| `admin.parser.settings` | admin | settings | Admin |
| `admin.roles.manage` | admin | manage | Admin |
| `admin.statistics.view` | admin | view | Admin |
| `admin.users.manage` | admin | manage | Admin |
| `admin.users.view` | admin | view | Admin |
| `anime.create` | anime | create | Anime |
| `anime.delete` | anime | delete | Anime |
| `anime.edit` | anime | edit | Anime |
| `anime.lock` | anime | lock | Anime |
| `anime.publish` | anime | publish | Anime |
| `anime.unlock` | anime | unlock | Anime |
| `anime.view` | anime | view | Anime |
| `audit.view` | audit | view | Audit |
| `episode.create` | episode | create | Episode |
| `episode.delete` | episode | delete | Episode |
| `episode.edit` | episode | edit | Episode |
| `episode.lock` | episode | lock | Episode |
| `episode.unlock` | episode | unlock | Episode |
| `episode.view` | episode | view | Episode |
| `parser.configure` | parser | configure | Parser |
| `parser.override_lock` | parser | override_lock | Parser |
| `parser.run` | parser | run | Parser |
| `security.ban.ip` | security | ip | Security |
| `security.unban.ip` | security | ip | Security |

### Expected Roles Table

Total: 8 roles

| Role Name | Type | Is System | Permission Count |
|-----------|------|-----------|------------------|
| `admin` | User | False | 19 |
| `editor` | User | False | 6 |
| `moderator` | User | False | 7 |
| `parser_bot` | System | True | 8 |
| `super_admin` | User | False | 25 |
| `support` | User | False | 4 |
| `user` | User | False | 2 |
| `worker_bot` | System | True | 3 |

---

## Common Issues and Fixes


### Issue 1: Legacy Colon Format Permissions

**Problem:** Permissions use old format: `admin:parser.settings`

**Fix:**
```sql
-- Option 1: Rename to dot format
UPDATE permissions SET name = 'admin.parser.settings' WHERE name = 'admin:parser.settings';

-- Option 2: Delete if truly legacy
DELETE FROM permissions WHERE name LIKE '%:%';
```

### Issue 2: Wildcard Permissions

**Problem:** Permissions use wildcards: `admin.*`, `parser:*`, `*`

**Fix:**
```sql
-- These MUST be deleted immediately (security violation)
DELETE FROM permissions WHERE name LIKE '%*';
DELETE FROM permissions WHERE name LIKE '%.*';
DELETE FROM permissions WHERE name LIKE '%:*';
```

### Issue 3: Unknown Permissions

**Problem:** Permissions exist in DB but not in contract

**Fix:**
```python
# Option 1: Add to contract if needed
# Edit rbac_contract.py and add to appropriate permission set

# Option 2: Delete from database
# DELETE FROM permissions WHERE name = 'unknown.permission';
```

### Issue 4: System Role with Admin Permissions

**Problem:** System role (parser_bot, worker_bot) has admin permissions

**Fix:**
```sql
-- Find the violation
SELECT r.name, p.name
FROM roles r
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE r.name IN ('parser_bot', 'worker_bot')
  AND p.name LIKE 'admin.%';

-- Remove the admin permissions from system roles
DELETE FROM role_permissions
WHERE role_id IN (SELECT id FROM roles WHERE name IN ('parser_bot', 'worker_bot'))
  AND permission_id IN (SELECT id FROM permissions WHERE name LIKE 'admin.%');
```

### Issue 5: Duplicate Entries

**Problem:** Duplicate role-permission mappings

**Fix:**
```sql
-- Keep only the oldest entry for each unique role-permission pair
DELETE FROM role_permissions rp1
USING role_permissions rp2
WHERE rp1.id > rp2.id
  AND rp1.role_id = rp2.role_id
  AND rp1.permission_id = rp2.permission_id;
```

---

## Verification Queries


Use these SQL queries to audit the live database:


### Query 1: Find Legacy Permissions
```sql
SELECT name, resource, action
FROM permissions
WHERE name LIKE '%:%'
ORDER BY name;
```

### Query 2: Find Wildcard Permissions
```sql
SELECT name, resource, action
FROM permissions
WHERE name LIKE '%*'
   OR name LIKE '%.*'
   OR name LIKE '%:*'
ORDER BY name;
```

### Query 3: Find Unknown Permissions
```sql
-- This requires checking against the contract manually
SELECT name FROM permissions ORDER BY name;
```

### Query 4: Find Roles Without Permissions
```sql
SELECT r.name, r.is_system
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
WHERE rp.id IS NULL
ORDER BY r.name;
```

### Query 5: Find Permissions Without Roles
```sql
SELECT p.name, p.resource, p.action
FROM permissions p
LEFT JOIN role_permissions rp ON p.id = rp.permission_id
WHERE rp.id IS NULL
ORDER BY p.name;
```

### Query 6: Check System Roles for Admin Permissions
```sql
SELECT r.name as role, p.name as permission
FROM roles r
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE r.name IN ('parser_bot', 'worker_bot')
  AND p.name LIKE 'admin.%'
ORDER BY r.name, p.name;
```

### Query 7: Find Duplicate Role-Permission Mappings
```sql
SELECT role_id, permission_id, COUNT(*)
FROM role_permissions
GROUP BY role_id, permission_id
HAVING COUNT(*) > 1;
```

### Query 8: Compare DB Permissions vs Contract
```sql
-- Get all role-permission mappings
SELECT 
    r.name as role,
    array_agg(p.name ORDER BY p.name) as permissions
FROM roles r
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
GROUP BY r.name
ORDER BY r.name;
```

---

## Risk Assessment


### HIGH RISK Issues (Immediate Action Required)

1. **Wildcard Permissions** - Security violation, must be removed
2. **System Roles with Admin Permissions** - Privilege escalation risk
3. **Unknown Permissions Not in Contract** - Undefined behavior

### MEDIUM RISK Issues (Should Be Fixed)

1. **Legacy Colon Format** - May cause parsing errors
2. **Unknown Roles** - Not aligned with contract
3. **Missing Contract Permissions in DB** - Features may not work

### LOW RISK Issues (Nice to Clean Up)

1. **Duplicate Entries** - Just noise, safe to remove
2. **Orphaned Permissions** - No functional impact
3. **Users Without Roles** - May be intentional

---

## Next Steps


1. **Run Against Live Database:** Execute the verification queries against your production database
2. **Document Findings:** Record all discovered issues in detail
3. **Prioritize Fixes:** Address HIGH RISK issues first
4. **Create Backup:** Before any changes: `pg_dump kitsu > backup_pre_cleanup.sql`
5. **Execute Cleanup Plan:** Use the SQL cleanup plan (REFACTOR-03_CLEANUP_PLAN.sql)
6. **Verify Results:** Re-run verification queries after cleanup
7. **Test Application:** Thoroughly test all RBAC-dependent features
8. **Proceed to REFACTOR-04:** Controlled execution with approval workflow

---

## Conclusion


This audit template provides a comprehensive framework for ensuring database
consistency with the RBAC contract. The contract is well-defined with clear
security invariants and role-permission mappings.

**Key Takeaways:**
- ✅ Contract is complete and well-structured
- ✅ All permissions are explicit (no wildcards in contract)
- ✅ System and user roles are properly segregated
- ✅ Admin permissions are NOT assigned to system roles in contract

**When running against live database, focus on:**
1. Eliminating wildcard permissions
2. Converting legacy colon format to dot format
3. Removing unknown/orphaned entries
4. Enforcing actor type segregation