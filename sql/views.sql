-- Reusable analytical views. All compatible with PostgreSQL; SQLite users can
-- run these too (CREATE VIEW syntax is identical).

CREATE VIEW vw_attractions_full AS
SELECT
    a.*,
    c.city_name,
    s.state_name,
    s.zone AS state_zone,
    w.avg_max_temp_c,
    w.avg_min_temp_c,
    w.summer_suitability,
    w.winter_suitability,
    w.monsoon_suitability
FROM attractions a
LEFT JOIN cities c ON a.city_id = c.city_id
LEFT JOIN states s ON c.state_id = s.state_id
LEFT JOIN weather w ON c.city_id = w.city_id;

CREATE VIEW vw_state_summary AS
SELECT
    s.state_name,
    COUNT(a.attraction_id)                      AS attraction_count,
    ROUND(AVG(a.google_rating)::numeric, 2)     AS avg_rating,
    ROUND(AVG(a.entrance_fee_inr)::numeric, 0)  AS avg_entrance_fee_inr,
    SUM(CASE WHEN a.heritage_indicator THEN 1 ELSE 0 END) AS heritage_site_count,
    SUM(CASE WHEN a.wildlife_indicator THEN 1 ELSE 0 END) AS wildlife_site_count
FROM states s
LEFT JOIN cities c ON c.state_id = s.state_id
LEFT JOIN attractions a ON a.city_id = c.city_id
GROUP BY s.state_name;

CREATE VIEW vw_destination_tag_map AS
SELECT
    a.attraction_id,
    a.attraction_name,
    t.tag_name
FROM destination_tags dt
JOIN attractions a ON a.attraction_id = dt.attraction_id
JOIN tags t ON t.tag_id = dt.tag_id;

CREATE VIEW vw_sim_destination_ratings AS
SELECT
    d.sim_destination_id,
    d.destination_name,
    d.destination_type,
    d.popularity_score,
    ROUND(AVG(r.rating)::numeric, 2) AS avg_review_rating,
    COUNT(r.sim_review_id)            AS review_count
FROM sim_destinations d
LEFT JOIN sim_reviews r ON r.sim_destination_id = d.sim_destination_id
GROUP BY d.sim_destination_id, d.destination_name, d.destination_type, d.popularity_score;
