# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-09-06

### Added
- New "long" single-file layout: a `Parts list` tab (parts and assemblies
  together, distinguished by a `Type` column) plus a single `BOMs` tab
  holding every assembly's line items, keyed by `Assy PN`. `BOM.single_file()`
  detects this layout automatically (exactly two sheets, the second named
  `BOMs`) alongside the existing one-sheet-per-assembly layout.

### Changed
- CLI simplified to `bomkit [PATH] [action]`; single-file vs. multi-file mode
  is now inferred from whether `PATH` is a file or a directory, removing the
  `-f`/`-d`/`-b` flags
- A directory `PATH` with no `Parts list.xlsx` but exactly one `.xlsx` file
  is now treated as that single-file BOM, so `bomkit` and `bomkit .` work
  from inside a single-file project folder, not just multi-file ones
- TUI browser now works with single-file BOMs, not just multi-file folders
- `BOM.summary` now resolves `parts_db` via the tree root, so it works when
  called on any sub-assembly, not just the top-level BOM

### Fixed
- Removed a dead/broken `__init__` code path that referenced a
  non-existent `init_parts` method

## [0.1.0] - 2026-03-02
Initial public release as `bomkit` (formerly `pybom`).

### Added
- Interactive TUI browser (`--browse` mode) powered by Textual
- Initial test suite
- GitHub Actions CI workflow
- Type hints throughout `BOM.py`
- Assembly BOM name read from Excel sheet name

### Changed
- `BOM.from_file()` made private (`_from_file()`)
- `QTY` method returning Python integers


---


## Pre-release history (as `pybom`)

## 0.2.0 - 2023

### Added
- `BOM.single_file()` for single-file BOMs

## 0.1.0 - 2020

### Added
- Core `BOM`, `Item`, `ItemLink`, and `PartsDB` data model
- `BOM.from_folder()` for multi-file BOMs


[Unreleased]: https://github.com/robsiegwart/bomkit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/robsiegwart/bomkit/releases/tag/v0.2.0
[0.1.0]: https://github.com/robsiegwart/bomkit/releases/tag/v0.1.0
