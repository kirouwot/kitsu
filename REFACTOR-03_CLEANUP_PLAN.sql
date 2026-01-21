-- ============================================================================
-- REFACTOR-03: Database Cleanup Plan (Template)
-- Generated: 2026-01-21T06:59:20.265726Z
-- Status: DRY-RUN TEMPLATE (DO NOT EXECUTE WITHOUT REVIEW)
-- ============================================================================

-- THIS SCRIPT IS A TEMPLATE FOR REVIEW
-- Modify queries based on actual database findings
-- Each statement should be reviewed, approved, and executed individually

-- ============================================================================
-- PRE-EXECUTION CHECKLIST
-- ============================================================================
-- [ ] Database backup created: pg_dump kitsu > backup_$(date +%Y%m%d_%H%M%S).sql
-- [ ] Audit report reviewed and findings documented
-- [ ] Cleanup plan approved by security team
-- [ ] Test environment validated first
-- [ ] Rollback procedure tested

BEGIN;

-- ============================================================================
-- STEP 1: DELETE WILDCARD PERMISSIONS (CRITICAL)
-- ============================================================================
-- RISK: HIGH - These are security violations
-- BREAKING: YES - Code using these permissions will fail
-- DATA LOSS: Intentional - wildcards are forbidden

-- Find wildcard permissions
-- SELECT * FROM permissions
-- WHERE name LIKE '%*' OR name LIKE '%.*' OR name LIKE '%:*';

-- Delete wildcard permissions
-- DELETE FROM permissions
-- WHERE name LIKE '%*' OR name LIKE '%.*' OR name LIKE '%:*';

-- ============================================================================
-- STEP 2: CONVERT LEGACY COLON FORMAT TO DOT FORMAT
-- ============================================================================
-- RISK: MEDIUM - Old format may be in use
-- BREAKING: NO if renamed, YES if deleted
-- DATA LOSS: NO if renamed

-- Find legacy permissions
-- SELECT * FROM permissions WHERE name LIKE '%:%';

-- Example conversions (uncomment and modify based on findings):
-- UPDATE permissions SET name = 'admin.parser.settings' WHERE name = 'admin:parser.settings';
-- UPDATE permissions SET name = 'admin.parser.logs' WHERE name = 'admin:parser.logs';
-- UPDATE permissions SET name = 'admin.parser.emergency' WHERE name = 'admin:parser.emergency';

-- If no valid dot-format equivalent exists, delete:
-- DELETE FROM permissions WHERE name LIKE '%:%';

-- ============================================================================
-- STEP 3: DELETE UNKNOWN PERMISSIONS (Not in Contract)
-- ============================================================================
-- RISK: MEDIUM-HIGH - Permissions not defined in contract
-- BREAKING: YES - Code using these permissions will fail
-- DATA LOSS: YES - Review carefully before deletion

-- List all permissions for manual review
-- SELECT name FROM permissions ORDER BY name;

-- Expected permissions (from contract): 26 total
-- ✓ admin.parser.emergency
-- ✓ admin.parser.logs
-- ✓ admin.parser.settings
-- ✓ admin.roles.manage
-- ✓ admin.statistics.view
-- ✓ admin.users.manage
-- ✓ admin.users.view
-- ✓ anime.create
-- ✓ anime.delete
-- ✓ anime.edit
-- ✓ anime.lock
-- ✓ anime.publish
-- ✓ anime.unlock
-- ✓ anime.view
-- ✓ audit.view
-- ✓ episode.create
-- ✓ episode.delete
-- ✓ episode.edit
-- ✓ episode.lock
-- ✓ episode.unlock
-- ✓ episode.view
-- ✓ parser.configure
-- ✓ parser.override_lock
-- ✓ parser.run
-- ✓ security.ban.ip
-- ✓ security.unban.ip

-- Delete unknown permissions (modify based on actual findings):
-- DELETE FROM permissions WHERE name NOT IN (
--   'admin.parser.emergency',
--   'admin.parser.logs',
--   'admin.parser.settings',
--   'admin.roles.manage',
--   'admin.statistics.view',
--   'admin.users.manage',
--   'admin.users.view',
--   'anime.create',
--   'anime.delete',
--   'anime.edit',
--   'anime.lock',
--   'anime.publish',
--   'anime.unlock',
--   'anime.view',
--   'audit.view',
--   'episode.create',
--   'episode.delete',
--   'episode.edit',
--   'episode.lock',
--   'episode.unlock',
--   'episode.view',
--   'parser.configure',
--   'parser.override_lock',
--   'parser.run',
--   'security.ban.ip',
--   'security.unban.ip'
-- );

-- ============================================================================
-- STEP 4: DELETE UNKNOWN ROLES (Not in Contract)
-- ============================================================================
-- RISK: HIGH - Roles not defined in contract
-- BREAKING: YES - Users with these roles will lose access
-- DATA LOSS: YES - Review carefully before deletion

-- List all roles for manual review
-- SELECT name, is_system FROM roles ORDER BY name;

-- Expected roles (from contract): 8 total
-- ✓ admin (user)
-- ✓ editor (user)
-- ✓ moderator (user)
-- ✓ parser_bot (system)
-- ✓ super_admin (user)
-- ✓ support (user)
-- ✓ user (user)
-- ✓ worker_bot (system)

-- Delete unknown roles (modify based on actual findings):
-- DELETE FROM roles WHERE name NOT IN (
--   'admin',
--   'editor',
--   'moderator',
--   'parser_bot',
--   'super_admin',
--   'support',
--   'user',
--   'worker_bot'
-- );

-- ============================================================================
-- STEP 5: REMOVE ADMIN PERMISSIONS FROM SYSTEM ROLES (CRITICAL)
-- ============================================================================
-- RISK: CRITICAL - Security violation (Parser ≠ Admin)
-- BREAKING: YES for system roles trying to use admin functions
-- DATA LOSS: Intentional - system roles must not have admin permissions

-- Find violations
-- SELECT r.name as role, p.name as permission
-- FROM roles r
-- JOIN role_permissions rp ON r.id = rp.role_id
-- JOIN permissions p ON rp.permission_id = p.id
-- WHERE r.name IN ('parser_bot', 'worker_bot')
--   AND p.name LIKE 'admin.%';

-- Remove admin permissions from system roles
-- DELETE FROM role_permissions
-- WHERE role_id IN (
--   SELECT id FROM roles WHERE name IN ('parser_bot', 'worker_bot')
-- )
-- AND permission_id IN (
--   SELECT id FROM permissions WHERE name LIKE 'admin.%'
-- );

-- ============================================================================
-- STEP 6: DELETE DUPLICATE ROLE-PERMISSION MAPPINGS
-- ============================================================================
-- RISK: LOW - Duplicates are just noise
-- BREAKING: NO
-- DATA LOSS: NO functional impact

-- Find duplicates
-- SELECT role_id, permission_id, COUNT(*)
-- FROM role_permissions
-- GROUP BY role_id, permission_id
-- HAVING COUNT(*) > 1;

-- Delete duplicates (keep oldest)
-- DELETE FROM role_permissions rp1
-- USING role_permissions rp2
-- WHERE rp1.id > rp2.id
--   AND rp1.role_id = rp2.role_id
--   AND rp1.permission_id = rp2.permission_id;

-- ============================================================================
-- STEP 7: CLEAN UP ORPHANED PERMISSIONS (OPTIONAL)
-- ============================================================================
-- RISK: LOW - Orphaned permissions have no functional impact
-- BREAKING: NO
-- DATA LOSS: Permissions not assigned to any role

-- Find orphaned permissions
-- SELECT p.name
-- FROM permissions p
-- LEFT JOIN role_permissions rp ON p.id = rp.permission_id
-- WHERE rp.id IS NULL;

-- Delete orphaned permissions (optional)
-- DELETE FROM permissions p
-- WHERE NOT EXISTS (
--   SELECT 1 FROM role_permissions rp WHERE rp.permission_id = p.id
-- );

-- ============================================================================
-- STEP 8: VERIFY CONTRACT COMPLIANCE
-- ============================================================================
-- After cleanup, verify the database matches the contract

-- Verify no wildcard permissions
-- SELECT * FROM permissions WHERE name LIKE '%*';
-- Expected: 0 rows

-- Verify no legacy colon format
-- SELECT * FROM permissions WHERE name LIKE '%:%';
-- Expected: 0 rows

-- Verify all permissions are in contract
-- SELECT name FROM permissions
-- WHERE name NOT IN (
--   'admin.parser.emergency',
--   'admin.parser.logs',
--   'admin.parser.settings',
--   'admin.roles.manage',
--   'admin.statistics.view',
--   'admin.users.manage',
--   'admin.users.view',
--   'anime.create',
--   'anime.delete',
--   'anime.edit',
--   'anime.lock',
--   'anime.publish',
--   'anime.unlock',
--   'anime.view',
--   'audit.view',
--   'episode.create',
--   'episode.delete',
--   'episode.edit',
--   'episode.lock',
--   'episode.unlock',
--   'episode.view',
--   'parser.configure',
--   'parser.override_lock',
--   'parser.run',
--   'security.ban.ip',
--   'security.unban.ip'
-- );
-- Expected: 0 rows

-- Verify all roles are in contract
-- SELECT name FROM roles
-- WHERE name NOT IN (
--   'admin',
--   'editor',
--   'moderator',
--   'parser_bot',
--   'super_admin',
--   'support',
--   'user',
--   'worker_bot'
-- );
-- Expected: 0 rows

-- Verify system roles don't have admin permissions
-- SELECT r.name, p.name
-- FROM roles r
-- JOIN role_permissions rp ON r.id = rp.role_id
-- JOIN permissions p ON rp.permission_id = p.id
-- WHERE r.name IN ('parser_bot', 'worker_bot')
--   AND p.name LIKE 'admin.%';
-- Expected: 0 rows

-- ============================================================================
-- ROLLBACK STRATEGY
-- ============================================================================
-- To rollback all changes:
ROLLBACK;

-- To commit changes (ONLY after thorough review and testing):
-- COMMIT;

-- Recommended execution process:
-- 1. Create backup: pg_dump -U kitsu -d kitsu > backup_$(date +%Y%m%d_%H%M%S).sql
-- 2. Start transaction: BEGIN;
-- 3. Execute one step at a time
-- 4. Verify results after each step
-- 5. If something wrong: ROLLBACK;
-- 6. If all good: COMMIT;
-- 7. Test application thoroughly
-- 8. Keep backup for 30 days

-- ============================================================================
-- END OF CLEANUP PLAN
-- ============================================================================