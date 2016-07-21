# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

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
- FIX: removed some unneccessary import validations
- FIX: kumo will now exit when importing a cloudformation.py not from your current working directory