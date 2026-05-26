# Backlog: SmartNote src layout migration

## Summary
Align SmartNote with the repository convention by moving the package to `src/smartnote`.

## Why
- Enforces the established `src/{projectname}` structure across packages.
- Prevents import ambiguity between local modules and installed packages.

## Scope
### In scope
- Move SmartNote Python package to `smartnote/src/smartnote`.
- Update packaging and test configuration for the src layout.

### Out of scope
- Any functional feature changes or refactors.
- Documentation rewrites beyond path alignment.

## Dependencies
- None beyond existing SmartNote package structure.

## Expected outcomes
- SmartNote imports resolve from `src/smartnote`.
- Packaging and tests work with src layout.

## Full Report
- **Summary**: Migrated SmartNote to the `src/smartnote` layout and updated packaging/test paths.
- **Implementation**:
  - Added `smartnote/src/smartnote` and recreated all package modules under the src tree.
  - Updated `smartnote/pyproject.toml` to set `package-dir` and `packages.find` to `src`.
  - Adjusted `smartnote/tests/conftest.py` to include `smartnote/src` on `sys.path`.
  - Removed the old `smartnote/smartnote` module files after migration.
- **Tests**: Not run (not requested).
