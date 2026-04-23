# Backend Module Map

Use this file when deciding where a backend change belongs.

## `analysis`

Model-facing logic:

- prompt orchestration
- OpenAI-compatible note generation
- transcription requests routed through model providers

## `config`

Configuration schema and persistence:

- default runtime config
- provider normalization
- path expansion
- API-key resolution

## `downloaders`

Source-specific media acquisition. Keep Bilibili-specific logic here instead of mixing it into note generation.

## `ingest`

Raw input collection:

- clipboard reads
- WeChat scan/export handling
- inbox file persistence

## `models`

Dataclasses shared across services. Keep these small and serializable.

## `routers`

FastAPI HTTP contracts. Routers should validate input and call services; they should not own business workflows.

## `services`

Application workflows:

- daily report building
- note generation orchestration
- settings save/load
- diagnostics
- vector indexing
- scheduler

Add short comments when a service uses a fallback path or writes state for the frontend to inspect.

## `transcription`

Audio transcription adapters. Keep provider-specific details here so note generation only calls `transcribe_audio`.
