-- Beginner-friendly sample queries for SQL practice.

-- All attractions in Rajasthan
SELECT a.attraction_name, c.city_name, a.attraction_type, a.google_rating
FROM attractions a
JOIN cities c ON a.city_id = c.city_id
JOIN states s ON c.state_id = s.state_id
WHERE s.state_name = 'Rajasthan';

-- Free attractions with a rating above 4.5
SELECT attraction_name, entrance_fee_inr, google_rating
FROM attractions
WHERE entrance_fee_inr = 0 AND google_rating > 4.5
ORDER BY google_rating DESC;

-- Count of attractions per type
SELECT attraction_type, COUNT(*) AS n
FROM attractions
GROUP BY attraction_type
ORDER BY n DESC;

-- All tags for a specific attraction
SELECT tag_name FROM vw_destination_tag_map WHERE attraction_name = 'India Gate';

-- Average entrance fee by budget category
SELECT budget_category, AVG(entrance_fee_inr) AS avg_fee
FROM attractions
GROUP BY budget_category;
