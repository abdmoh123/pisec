# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Docker image release

### Changed

- Video and photo directories are set by DATA_DIR environment variable by default
- OpenCV now headless
- Updated to python 3.14 and uv 0.13.5

## [0.1.0] - 2026-10-10

### Added

- Initial release of pisec-camera
- FSM based algorithm with interchangeable parts
- Frame difference motion detection algorithm that's easy to swap out
- Keeps a list/buffer of video files and automatically deletes when limit is reached
- Ability to send data to the pisec-server or work standalone without network access
- Feature flags to customise the behaviour of the app (e.g. video list/buffer size)
- OAuth 2.0 authentication with automatic retries
- Easy to use CLI with help outputs
