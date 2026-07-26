-- Indexes — run after schema.sql and after data load.
CREATE INDEX IF NOT EXISTS idx_cities_state              ON cities(state_id);
CREATE INDEX IF NOT EXISTS idx_attractions_city           ON attractions(city_id);
CREATE INDEX IF NOT EXISTS idx_attractions_type           ON attractions(attraction_type);
CREATE INDEX IF NOT EXISTS idx_attractions_budget         ON attractions(budget_category);
CREATE INDEX IF NOT EXISTS idx_attractions_popularity     ON attractions(popularity_tier);
CREATE INDEX IF NOT EXISTS idx_weather_city                ON weather(city_id);
CREATE INDEX IF NOT EXISTS idx_climate_monthly_city        ON climate_monthly(city_id);
CREATE INDEX IF NOT EXISTS idx_destination_climate_city     ON destination_climate(city_id);
CREATE INDEX IF NOT EXISTS idx_destination_tags_attraction ON destination_tags(attraction_id);
CREATE INDEX IF NOT EXISTS idx_destination_tags_tag        ON destination_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_sim_destinations_state      ON sim_destinations(state_id);
CREATE INDEX IF NOT EXISTS idx_sim_reviews_destination     ON sim_reviews(sim_destination_id);
CREATE INDEX IF NOT EXISTS idx_sim_reviews_user            ON sim_reviews(sim_user_id);
CREATE INDEX IF NOT EXISTS idx_sim_history_user            ON sim_user_history(sim_user_id);
CREATE INDEX IF NOT EXISTS idx_sim_history_destination     ON sim_user_history(sim_destination_id);
