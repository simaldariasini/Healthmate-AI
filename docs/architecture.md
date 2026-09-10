# Architecture

```text
User context -> condition IDs -> approved knowledge retrieval -> meal filtering -> AI explanation -> safety validation -> response + sources
```

FastAPI owns data access and output acceptance. SQLAlchemy maps the health conditions, sources, claims, links, review log, and meals. SQLite is the local default; PostgreSQL is the target deployment database.

The React/Vite client presents approved knowledge and source attribution directly. It does not contain medical condition claims in prompts or business logic.
