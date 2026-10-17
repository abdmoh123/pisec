# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Mise start task now works like it used to
- Switched to PyJWT to fix python-jose vulnerability
- Switched from deprecated regex to pattern arguments in pydantic models

## [0.1.0] - 2026-10-10

### Added

- Initial release of pisec-server
- Manages the storage and access of videos recorded by security cameras
- Users can create camera credentials to become owners of cameras
- A camera can use a credential to register to the server
- Camera owners can subscribe and unsubscribe other users to their cameras
- Non-owners can unsubscribe cameras from themselves
- Users can download videos from any camera they own or are subscribed to
- Admin permissions (access everything) for the first user
- Endpoints for user clients and camera clients
- OAuth 2.0 authentication and authorization
- GET endpoints support pagination and sorting
- REST-like api endpoints
