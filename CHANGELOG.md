# Changelog

All notable changes to this project are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-06-18

### Fixed

- Require `aethexai>=1.0.1` so the `list_models` tool works against the current API. The `1.0.0` SDK's generated `ModelEntryProvider` predated the platform reporting vendor-level providers (`google`, `meta`, `xai`, `mistral`, `deepseek`, `aethex`) from `GET /models`, so `list_models` raised `'<vendor>' is not a valid ModelEntryProvider`. Pinning the resynced SDK resolves it; no MCP code changed.

## [0.1.0] - 2026-06-17

Initial public release. 32 tools across voices and text-to-speech, transcription, voice agents, agent knowledge bases, calls, conversations, and usage, all driven through the public Aethex API.
