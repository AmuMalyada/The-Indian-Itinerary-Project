-- Additional constraints not expressed inline in schema.sql
-- (kept separate so schema evolution / constraint changes are reviewable independently)

ALTER TABLE attractions
    ADD CONSTRAINT chk_visit_duration_positive CHECK (visit_duration_hrs IS NULL OR visit_duration_hrs > 0);

ALTER TABLE attractions
    ADD CONSTRAINT chk_establishment_year_range
        CHECK (establishment_year IS NULL OR (establishment_year BETWEEN 1 AND 2026));

ALTER TABLE sim_destinations
    ADD CONSTRAINT chk_popularity_range CHECK (popularity_score IS NULL OR popularity_score BETWEEN 0 AND 10);

ALTER TABLE weather
    ADD CONSTRAINT chk_temp_plausible_range CHECK (
        (jan_max_temp IS NULL OR jan_max_temp BETWEEN -10 AND 55) AND
        (jan_min_temp IS NULL OR jan_min_temp BETWEEN -10 AND 55)
    );
