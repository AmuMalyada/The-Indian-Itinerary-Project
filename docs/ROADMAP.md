# Roadmap

## v1.0 (current)
- [x] Ingest, clean, standardize, merge three Kaggle sources
- [x] Normalized relational schema (Postgres DDL + SQLite build)
- [x] Feature engineering (30+ analytics columns)
- [x] Automated quality checks + pytest suite
- [x] Power BI-ready flattened export
- [x] Jupyter EDA notebook
- [x] Full documentation set

## v1.1 (near-term)
- [ ] Enrich `attractions` with real lat/long (currently absent from source
      data — plan is a one-time, rate-limited geocoding pass against a public
      geocoder, cached to `raw_data/geocode_cache.json`, not fabricated)
- [ ] Expand weather coverage beyond the 64/213 matched cities using a public
      climate-normals API
- [ ] Add `Travel_Seasons` and `Best_Visit_Window` tables derived from the
      weather-suitability columns already computed

## v2.0 (mid-term)
- [ ] FastAPI service on top of a Postgres load of `sql/schema.sql`
- [ ] `Suggested_Itineraries` table: rule-based multi-day itinerary generator
      using existing scores (adventure/nature/heritage/etc.)
- [ ] Embeddings of `review_text` + attraction descriptions for a RAG-based
      travel chatbot (vector DB: pgvector or a managed alternative)

## v3.0 (long-term / stretch)
- [ ] React web front-end and/or Flutter mobile app on the API
- [ ] User accounts, saved itineraries, personalization from `sim_users`
      preference patterns (with real data collection replacing synthetic once live)
- [ ] Cloud deployment (Supabase + serverless API)

## Explicitly out of scope for now
- Presenting `sim_destinations` as real-world attraction data
- Fabricating coordinates, prices, or ratings not present in source data
