# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-10-17

### Changed

- About page shows the app logo and the public facing 'Pisec' name
- No longer logged out if you lose connection to the server

### Fixed

- GUI potentially overlapping system areas (e.g. navigation buttons or rounded corners)
- Potential crashes when loading new pages (e.g. camera page)

## [1.0.0] - 2026-10-10

### Added

- Initial release of pisec-client
- Connects to the pisec server so users can view their security camera's videos
- Targets Android, Linux and Web
- Dark theme
- Users can sort cameras by ID, name or date registered
- Users can sort videos by date, name or camera
- Users can subscribe their owned cameras to other users
- Users can change their email or password
- Users can create credentials that can be saved and sent to the camera (manually)
- Users can login and register from the app
- Automatic redirection to login page (expired session or manual logout)
- Login state (e.g. token) is saved persistently and securely
