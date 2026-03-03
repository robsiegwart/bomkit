# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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


[Unreleased]: https://github.com/robsiegwart/bomkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/robsiegwart/bomkit/releases/tag/v0.1.0
