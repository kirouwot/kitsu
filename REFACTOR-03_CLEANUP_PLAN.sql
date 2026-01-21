-- ╔════════════════════════════════════════════════════════════════════════════╗
-- ║                                                                            ║
-- ║   ⚠️  ⚠️  ⚠️   DO NOT EXECUTE THIS FILE   ⚠️  ⚠️  ⚠️                      ║
-- ║                                                                            ║
-- ║   THIS IS A NON-EXECUTABLE PLANNING TEMPLATE                               ║
-- ║   FOR REFACTOR-04 (FUTURE CONTROLLED CLEANUP PHASE)                        ║
-- ║                                                                            ║
-- ║   REFACTOR-03 = PLANNING ONLY (no database access)                         ║
-- ║   REFACTOR-04 = CONTROLLED EXECUTION (with manual approval)                ║
-- ║                                                                            ║
-- ╚════════════════════════════════════════════════════════════════════════════╝

-- ============================================================================
-- REFACTOR-03: Database Cleanup Plan (TEMPLATE ONLY - NON-EXECUTABLE)
-- Generated: 2026-01-21T06:59:20.265726Z
-- Status: PLANNING TEMPLATE (NOT FOR EXECUTION)
-- ============================================================================

-- ⛔ CRITICAL WARNING ⛔
-- This file contains NO executable SQL statements by design.
-- All potentially dangerous operations are COMMENTED OUT.
-- This is a TEMPLATE for REFACTOR-04 planning, NOT a runnable script.

-- ============================================================================
-- WHAT THIS FILE IS
-- ============================================================================
-- ✓ A planning template for future database cleanup
-- ✓ Example queries to guide REFACTOR-04 execution
-- ✓ Risk assessment for potential cleanup operations
-- ✓ Reference documentation for manual approval process

-- ============================================================================
-- WHAT THIS FILE IS NOT
-- ============================================================================
-- ✗ NOT an executable script
-- ✗ NOT ready to run against a database
-- ✗ NOT based on actual database audit (database was not accessed)
-- ✗ NOT approved for execution (requires REFACTOR-04 approval workflow)

-- ============================================================================
-- HOW TO USE THIS TEMPLATE (IN REFACTOR-04)
-- ============================================================================
-- 1. First, audit the actual database using queries from REFACTOR-03_DB_AUDIT.md
-- 2. Document real findings (not hypothetical ones)
-- 3. Adapt queries in this file based on actual findings
-- 4. Get approval for each step from security team
-- 5. Create database backup before ANY changes
-- 6. Execute ONE step at a time with verification
-- 7. Never uncomment multiple DELETE/UPDATE statements at once
-- 8. Always use transactions with tested rollback

-- ============================================================================
-- PRE-EXECUTION CHECKLIST (FOR REFACTOR-04 PHASE)
-- ============================================================================
-- This checklist is for REFACTOR-04, not REFACTOR-03
-- [ ] REFACTOR-04 task officially started
-- [ ] Actual database audit completed (real findings documented)
-- [ ] This template adapted based on actual findings
-- [ ] Database backup created: pg_dump kitsu > backup_$(date +%Y%m%d_%H%M%S).sql
-- [ ] Backup tested and verified
-- [ ] Cleanup plan approved by security team
-- [ ] Test environment validated with identical procedure
-- [ ] Rollback procedure tested in test environment
-- [ ] Approval obtained for each individual step
-- [ ] Downtime window scheduled (if required)
-- [ ] Rollback team on standby

-- ============================================================================
-- FILE STRUCTURE NOTE
-- ============================================================================
-- All SQL statements below are COMMENTED OUT
-- This ensures the file cannot be executed accidentally
-- In REFACTOR-04, specific statements will be:
--   1. Reviewed individually
--   2. Adapted to actual findings
--   3. Approved separately
--   4. Uncommented ONE AT A TIME
--   5. Executed with verification
--   6. Rolled back if issues detected

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
-- ROLLBACK STRATEGY (FOR REFACTOR-04 EXECUTION)
-- ============================================================================
-- ⚠️  These rollback instructions are for REFACTOR-04, not REFACTOR-03
-- REFACTOR-03 did not execute anything, so there is nothing to rollback

-- When executing in REFACTOR-04:
-- To rollback all changes:
-- ROLLBACK;

-- To commit changes (ONLY after thorough review and testing):
-- COMMIT;

-- Recommended REFACTOR-04 execution process:
-- 1. Create backup: pg_dump -U kitsu -d kitsu > backup_$(date +%Y%m%d_%H%M%S).sql
-- 2. Test backup restore procedure
-- 3. Start transaction: BEGIN;
-- 4. Uncomment and execute ONE step at a time
-- 5. Verify results after each step using SELECT queries
-- 6. If something wrong: ROLLBACK; and restore from backup
-- 7. If all good: COMMIT; (only after all steps verified)
-- 8. Test application thoroughly
-- 9. Monitor for 24-48 hours
-- 10. Keep backup for 30 days

-- ============================================================================
-- PHASE BOUNDARY: REFACTOR-03 vs REFACTOR-04
-- ============================================================================

-- REFACTOR-03 (THIS FILE) = PLANNING TEMPLATE
-- ✓ Template created
-- ✓ Example queries provided
-- ✓ Risk assessment documented
-- ✗ NO database accessed
-- ✗ NO queries executed
-- ✗ NO changes made

-- REFACTOR-04 (NEXT PHASE) = CONTROLLED EXECUTION
-- 🔜 Database connection established
-- 🔜 Actual audit performed
-- 🔜 Findings documented
-- 🔜 This template adapted to real findings
-- 🔜 Manual approval obtained
-- 🔜 Cleanup executed step-by-step
-- 🔜 Results verified
-- 🔜 Application tested

-- ============================================================================
-- END OF NON-EXECUTABLE TEMPLATE
-- ============================================================================
-- 
-- ⚠️  FINAL REMINDER ⚠️
-- 
-- This file is a PLANNING TEMPLATE created without database access.
-- It is NOT ready for execution and contains NO executable SQL.
-- All potentially dangerous operations are commented out by design.
-- 
-- DO NOT uncomment statements without:
--   1. Completing REFACTOR-04 actual database audit
--   2. Adapting queries based on real findings
--   3. Obtaining security team approval
--   4. Creating and testing database backup
--   5. Testing in non-production environment first
-- 
-- For execution, proceed to REFACTOR-04 with proper approval workflow.
-- 
-- ============================================================================