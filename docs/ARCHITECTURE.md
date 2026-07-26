# Architecture

## Pipeline (data flow)

```mermaid
flowchart LR
    subgraph Raw
        A1[Top Indian Places to Visit.csv]
        A2[temperatureData.csv]
        A3[Expanded_Destinations.csv]
        A4[Reviews.csv]
        A5[UserHistory.csv]
        A6[Users.csv]
    end

    A1 & A2 & A3 & A4 & A5 & A6 --> S1[01_ingest.py]
    S1 --> S2[02_profile.py]
    S2 --> S3[03_clean.py]
    S3 --> S4[04_standardize.py]
    S4 --> S5[05_merge.py]
    S5 --> S6[06_feature_engineering.py]
    S6 --> S7[07_quality_checks.py]
    S7 -->|pass| S8[08_generate_database.py]
    S7 -->|fail| X[Pipeline halts]
    S8 --> S9[09_export.py]
    S9 --> S10[10_build_documentation.py]

    S8 --> DB[(indian_itinerary.db)]
    S9 --> CSV[final_dataset/*.csv]
    S10 --> DOCS[docs/*.md]
```

## Entity-relationship model

```mermaid
erDiagram
    STATES ||--o{ CITIES : contains
    CITIES ||--o| WEATHER : has
    CITIES ||--o{ ATTRACTIONS : contains
    ATTRACTIONS ||--o{ DESTINATION_TAGS : tagged_with
    TAGS ||--o{ DESTINATION_TAGS : applied_to
    STATES ||--o{ SIM_DESTINATIONS : "loosely linked by state name only"
    SIM_DESTINATIONS ||--o{ SIM_REVIEWS : receives
    SIM_USERS ||--o{ SIM_REVIEWS : writes
    SIM_USERS ||--o{ SIM_USER_HISTORY : has
    SIM_DESTINATIONS ||--o{ SIM_USER_HISTORY : visited_in

    STATES {
        uuid state_id PK
        text state_name
        text zone
    }
    CITIES {
        uuid city_id PK
        text city_name
        uuid state_id FK
    }
    ATTRACTIONS {
        uuid attraction_id PK
        uuid city_id FK
        text attraction_name
        text attraction_type
        int  google_rating
        int  entrance_fee_inr
        text budget_category
        text popularity_tier
    }
    WEATHER {
        uuid weather_id PK
        uuid city_id FK
        text summer_suitability
        text winter_suitability
        text monsoon_suitability
    }
    TAGS {
        uuid tag_id PK
        text tag_name
    }
    DESTINATION_TAGS {
        uuid attraction_id FK
        uuid tag_id FK
    }
    SIM_DESTINATIONS {
        int  sim_destination_id PK
        text destination_name
        uuid state_id FK
    }
    SIM_USERS {
        int sim_user_id PK
        text email
    }
    SIM_REVIEWS {
        int sim_review_id PK
        int sim_destination_id FK
        int sim_user_id FK
    }
    SIM_USER_HISTORY {
        int sim_history_id PK
        int sim_user_id FK
        int sim_destination_id FK
    }
```

## Why two domains instead of one merged dataset

`attractions` (real, 323 rows after cleaning) and `sim_destinations` (synthetic,
1,000 rows) describe different things at different granularities and cannot be
honestly joined 1:1 — see `docs/DATASET_UNDERSTANDING.md` for the evidence.
Faking that join would look impressive for about five minutes until someone
queried it. Keeping them separate, with the *only* real link being `state_id`,
is the correct data-modeling call and is the kind of judgment call a senior
analytics engineer is expected to make and document.

## Future scalability (not built now, architected for)

```mermaid
flowchart TB
    DB[(PostgreSQL / Supabase)] --> API[FastAPI REST layer]
    API --> WEB[React web app]
    API --> MOBILE[Flutter mobile app]
    DB --> VEC[Vector DB embeddings]
    VEC --> RAG[LLM RAG / chatbot]
    API --> RAG
```

The schema already uses UUID primary keys and a normalized structure so it
can be loaded into PostgreSQL/Supabase unchanged, fronted by a FastAPI
service, and used as the retrieval layer for a travel-recommendation RAG
system without a redesign.
