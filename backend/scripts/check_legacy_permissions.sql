-- SQL Script to Check for Legacy Permission Strings
-- REFACTOR-02.1: Security Cleanup
-- 
-- This script checks for legacy permission strings in the database.
-- Legacy formats include:
--   - admin:* (wildcard)
--   - admin:parser.* (colon-based instead of dot-based)
--   - parser:* (wildcard)
--   - system:* (wildcard)
--
-- Run this script in READ-ONLY mode to identify issues.
-- Cleanup SQL is provided but NOT automatically executed.

-- ============================================================================
-- CHECK 1: Find all permissions with colon format (admin:xxx, parser:xxx)
-- ============================================================================

SELECT 
    id,
    name,
    display_name,
    resource,
    action,
    'Legacy colon-based format' as issue
FROM permissions
WHERE name LIKE '%:%'
ORDER BY name;

-- Expected result: 0 rows
-- If rows found: These permissions use legacy colon-based format instead of dots


-- ============================================================================
-- CHECK 2: Find all wildcard permissions (admin:*, parser:*, etc)
-- ============================================================================

SELECT 
    id,
    name,
    display_name,
    resource,
    action,
    'Wildcard permission (FORBIDDEN)' as issue
FROM permissions
WHERE name LIKE '%*%'
   OR name LIKE '%.*'
   OR name LIKE '%:*'
ORDER BY name;

-- Expected result: 0 rows
-- If rows found: These permissions violate SECURITY-01 (no wildcards allowed)


-- ============================================================================
-- CHECK 3: Find permissions not in ALLOWED_PERMISSIONS list
-- ============================================================================

-- Valid permissions as of REFACTOR-02.1:
-- Anime: anime.view, anime.create, anime.edit, anime.delete, anime.publish, anime.lock, anime.unlock
-- Episode: episode.view, episode.create, episode.edit, episode.delete, episode.lock, episode.unlock
-- Parser: parser.run, parser.configure, parser.override_lock
-- Admin: admin.parser.settings, admin.parser.emergency, admin.parser.logs, admin.roles.manage, admin.users.manage, admin.users.view, admin.statistics.view
-- Audit: audit.view
-- Security: security.ban.ip, security.unban.ip

WITH allowed_permissions AS (
    SELECT unnest(ARRAY[
        'anime.view', 'anime.create', 'anime.edit', 'anime.delete', 'anime.publish', 'anime.lock', 'anime.unlock',
        'episode.view', 'episode.create', 'episode.edit', 'episode.delete', 'episode.lock', 'episode.unlock',
        'parser.run', 'parser.configure', 'parser.override_lock',
        'admin.parser.settings', 'admin.parser.emergency', 'admin.parser.logs',
        'admin.roles.manage', 'admin.users.manage', 'admin.users.view', 'admin.statistics.view',
        'audit.view',
        'security.ban.ip', 'security.unban.ip'
    ]) AS permission_name
)
SELECT 
    p.id,
    p.name,
    p.display_name,
    'Not in ALLOWED_PERMISSIONS' as issue
FROM permissions p
WHERE p.name NOT IN (SELECT permission_name FROM allowed_permissions)
ORDER BY p.name;

-- Expected result: 0 rows
-- If rows found: These permissions are not defined in rbac_contract.py


-- ============================================================================
-- CHECK 4: Find role assignments using legacy permissions
-- ============================================================================

WITH legacy_permissions AS (
    SELECT id, name
    FROM permissions
    WHERE name LIKE '%:%'
       OR name LIKE '%*%'
)
SELECT 
    r.name as role_name,
    p.name as permission_name,
    'Role has legacy permission' as issue
FROM role_permissions rp
JOIN roles r ON rp.role_id = r.id
JOIN legacy_permissions p ON rp.permission_id = p.id
ORDER BY r.name, p.name;

-- Expected result: 0 rows
-- If rows found: These role assignments use legacy permissions and must be updated


-- ============================================================================
-- CLEANUP SCRIPT (DO NOT RUN AUTOMATICALLY - REVIEW FIRST)
-- ============================================================================

-- STEP 1: Backup current state
-- CREATE TABLE permissions_backup_refactor021 AS SELECT * FROM permissions;
-- CREATE TABLE role_permissions_backup_refactor021 AS SELECT * FROM role_permissions;

-- STEP 2: Remove role assignments for legacy permissions
-- DELETE FROM role_permissions
-- WHERE permission_id IN (
--     SELECT id FROM permissions 
--     WHERE name LIKE '%:%' OR name LIKE '%*%'
-- );

-- STEP 3: Delete legacy permissions
-- DELETE FROM permissions
-- WHERE name LIKE '%:%' OR name LIKE '%*%';

-- STEP 4: Verify cleanup
-- SELECT COUNT(*) FROM permissions WHERE name LIKE '%:%' OR name LIKE '%*%';
-- Expected result: 0

-- ============================================================================
-- VERIFICATION SUMMARY
-- ============================================================================

SELECT 
    'Total permissions' as metric,
    COUNT(*) as count
FROM permissions
UNION ALL
SELECT 
    'Legacy colon-based',
    COUNT(*)
FROM permissions
WHERE name LIKE '%:%'
UNION ALL
SELECT 
    'Wildcard permissions',
    COUNT(*)
FROM permissions
WHERE name LIKE '%*%'
UNION ALL
SELECT 
    'Valid permissions',
    COUNT(*)
FROM permissions
WHERE name NOT LIKE '%:%'
  AND name NOT LIKE '%*%';

-- Expected results:
-- Total permissions: ~26 (all permissions from rbac_contract)
-- Legacy colon-based: 0
-- Wildcard permissions: 0
-- Valid permissions: ~26
