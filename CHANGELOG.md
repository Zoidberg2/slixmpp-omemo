# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Emit an event when OMEMO has initialized
- Manually subscribe to device list nodes of contacts without working PEP updates (i.e. missing presence subscription)

### Fixed
- Use only strings for data form values used in pubsub publish options and node configuration
- Ignore messages without body in the echo bot example

## [1.0.0] - 26th of July, 2024

### Added
- Initial release

[Unreleased]: https://github.com/Syndace/slixmpp-omemo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Syndace/slixmpp-omemo/releases/tag/v1.0.0
