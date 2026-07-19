---
name: find-smells
description: Find code smells — from surface-level issues to deeper architectural ones — and make a plan to fix them.
disable-model-invocation: true
---
# Find Code Smells

Find 3 code smells that could be fixed, then make a plan to fix them.

## Steps

1. Identify 3 code smells. A code smell could be:
   - Large classes/files that need refactoring
   - Areas with low test coverage
   - Duplicated/redundant code
   - Legacy or dead code
   - Poorly-documented complex logic
   - Files/classes in the wrong place, or with misleading names
   - Debug cruft (leftover print statements, TODO/FIXME, commented-out code)
   - Violations of the project's coding conventions (loaded via plugin skills)
   - Over-engineered subsystems (YAGNI) — unnecessary abstractions, factories, or patterns
   - Opportunities where the code could use a framework feature, starter, or third-party library instead of a custom implementation
   - Deep inheritance hierarchies that should be composition
   - Blocking I/O patterns that don't leverage async/virtual thread capabilities
   - Other broad, system-level architectural concerns

2. Make a plan to fix the identified smells.

## Notes

When looking for these smells, be creative and think outside the box. Mix surface-level
and architectural smells rather than defaulting to only one kind.
