-- Analytics queries — demonstrate joins, window functions, CTEs, aggregation.
-- Run against final_dataset/indian_itinerary.db (SQLite) or a Postgres load
-- of schema.sql.

-- 1. Top 10 most iconic attractions per zone (window function)
WITH ranked AS (
    SELECT
        attraction_name, zone, google_rating, google_review_count_lakhs,
        RANK() OVER (PARTITION BY zone ORDER BY google_review_count_lakhs DESC) AS zone_rank
    FROM attractions
)
SELECT * FROM ranked WHERE zone_rank <= 10 ORDER BY zone, zone_rank;

-- 2. Budget-category distribution by state
SELECT
    s.state_name,
    a.budget_category,
    COUNT(*) AS attraction_count
FROM attractions a
JOIN cities c ON a.city_id = c.city_id
JOIN states s ON c.state_id = s.state_id
GROUP BY s.state_name, a.budget_category
ORDER BY s.state_name, attraction_count DESC;

-- 3. Best monsoon-friendly destinations with high nature score
SELECT a.attraction_name, c.city_name, s.state_name, w.monsoon_suitability, a.nature_score
FROM attractions a
JOIN cities c ON a.city_id = c.city_id
JOIN states s ON c.state_id = s.state_id
JOIN weather w ON w.city_id = c.city_id
WHERE w.monsoon_suitability = 'High' AND a.nature_score >= 6
ORDER BY a.nature_score DESC;

-- 4. State-level tourism scorecard (CTE + aggregation)
WITH state_stats AS (
    SELECT
        s.state_name,
        COUNT(a.attraction_id) AS num_attractions,
        AVG(a.google_rating) AS avg_rating,
        SUM(CASE WHEN a.entrance_fee_inr = 0 THEN 1 ELSE 0 END) AS free_attractions
    FROM states s
    LEFT JOIN cities c ON c.state_id = s.state_id
    LEFT JOIN attractions a ON a.city_id = c.city_id
    GROUP BY s.state_name
)
SELECT *, ROUND(1.0 * free_attractions / NULLIF(num_attractions,0), 2) AS pct_free
FROM state_stats
ORDER BY num_attractions DESC;

-- 5. Tag co-occurrence (which tags most frequently appear together)
SELECT
    t1.tag_name AS tag_a, t2.tag_name AS tag_b, COUNT(*) AS co_occurrences
FROM destination_tags dt1
JOIN destination_tags dt2
    ON dt1.attraction_id = dt2.attraction_id AND dt1.tag_id < dt2.tag_id
JOIN tags t1 ON t1.tag_id = dt1.tag_id
JOIN tags t2 ON t2.tag_id = dt2.tag_id
GROUP BY t1.tag_name, t2.tag_name
ORDER BY co_occurrences DESC
LIMIT 20;

-- 6. Synthetic dataset: top destinations by average review rating (min 3 reviews)
SELECT destination_name, destination_type, avg_review_rating, review_count
FROM vw_sim_destination_ratings
WHERE review_count >= 3
ORDER BY avg_review_rating DESC
LIMIT 20;

-- 7. Popularity tier vs average estimated daily cost
SELECT popularity_tier, ROUND(AVG(estimated_daily_cost_inr)) AS avg_daily_cost_inr, COUNT(*) AS n
FROM attractions
GROUP BY popularity_tier
ORDER BY avg_daily_cost_inr DESC;

-- 8. Cities with the widest seasonal temperature swing (for "avoid extreme weather" filtering)
SELECT c.city_name, s.state_name, (w.avg_max_temp_c - w.avg_min_temp_c) AS annual_range_c
FROM weather w
JOIN cities c ON c.city_id = w.city_id
JOIN states s ON s.state_id = c.state_id
WHERE w.avg_max_temp_c IS NOT NULL
ORDER BY annual_range_c DESC
LIMIT 15;
