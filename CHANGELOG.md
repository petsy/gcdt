# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [0.0.34] - 2016-08-tbd
### Added
- FIX: refactored yugen structure to yugen_main and yugen_core
- FIX: improved yugen testability and test coverage
- FIX: further improved ramuda test coverage
- FEATURE: ramuda clean

## [0.0.33] - 2016-08-18
### Added
- FIX: refactored tenkai structure to tenkai_main and tenkai_core
- FIX: improved tenkai testability and test coverage
- FIX: refactored ramuda structure to ramuda_main and ramuda_core
- FIX: improved ramuda testability and test coverage
- FEATURE: gcdt pull request builder

## [0.0.30] - 2016-08-02
### Added
- FIX: refactored kumo structure to kumo_main and kumo_core
- FIX: improved kumo testability and test coverage
- FIX: Rate limiting when preview with empty changeset (#48)
### Removed
- FEATURE: kumo validate
- FEATURE: kumo scaffold

## [0.0.29] - 2016-07-21
### Added
- FEATURE: bump glomex-utils to 0.0.11
- FIX: create_stack was broken

## [0.0.26] - 2016-07-19
### Added
- FEATURE: kumo now supports stack policies, see README for details
- FEATURE: kumo now displays changes in CloudFormation template parameters
- FIX: prettify output
- FIX: removed debug output
- FIX: removed some unnecessary import validations
- FIX: kumo will now exit when importing a cloudformation.py not from your current working directory
