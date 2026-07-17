# Phase 2 API

Base prefix: `/api/v1/technology/learning`.

Read endpoints include curriculum, topics, coverage, gaps, next action, cycles, questions, candidate answers, verification reports, reviews, dataset candidates, dataset versions, evaluation sets, model candidates, and deployment recommendations.

Administrative mutation endpoints require the placeholder header `x-devmind-admin: local-admin` until real authentication is implemented. Mutations include cycle creation/start/pause/cancel, question generation, candidate generation, review actions, dataset record creation, dataset version creation/export, and model-candidate registration.
