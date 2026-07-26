# DAX measure library

The following measures are designed for an executive-style Power BI report using the existing attraction exports.

## Core KPI measures

```DAX
// Total number of attractions in the current filter context.
Total Attractions = COUNTROWS(Attractions)
```

```DAX
// Total number of cities represented in the current context.
Total Cities = COUNTROWS(Cities)
```

```DAX
// Total number of states represented in the current context.
Total States = COUNTROWS(States)
```

```DAX
// Average Google rating across the filtered attractions.
Average Rating = AVERAGE(Attractions[google_rating])
```

```DAX
// Average daily cost estimate in INR.
Average Daily Cost = AVERAGE(Attractions[estimated_daily_cost_inr])
```

```DAX
// Average visit duration in hours.
Average Visit Duration = AVERAGE(Attractions[visit_duration_hrs])
```

## Popularity and value measures

```DAX
// Normalized popularity proxy using rating and review volume.
Popularity Index =
VAR RatingScore = DIVIDE(AVERAGE(Attractions[google_rating]), 5)
VAR ReviewScore = DIVIDE(AVERAGE(Attractions[google_review_count_lakhs]), 10)
RETURN ROUND((RatingScore * 0.7) + (ReviewScore * 0.3), 2)
```

```DAX
// Share of attractions represented by a selected segment.
Attraction Share % =
DIVIDE([Total Attractions], CALCULATE([Total Attractions], ALL(Attractions)))
```

## Budget measures

```DAX
// Count of attractions in the free or low-cost tier.
Budget Friendly Count =
CALCULATE([Total Attractions], Attractions[budget_category] IN {"Free", "Low"})
```

```DAX
// Percentage of attractions within a budget-friendly tier.
Budget Friendly % = DIVIDE([Budget Friendly Count], [Total Attractions])
```

## Ranking and context measures

```DAX
// Rank attractions within the current filter context by rating.
Attraction Rating Rank =
RANKX(ALL(Attractions[attraction_name]), [Average Rating],, DESC)
```

```DAX
// Dynamic title for any selected state or category.
Selection Summary =
VAR SelectedState = SELECTEDVALUE(States[state_name], "All States")
VAR SelectedCategory = SELECTEDVALUE(Attractions[attraction_type], "All Categories")
RETURN SelectedState & " • " & SelectedCategory
```

## Season and traveler measures

```DAX
// Count of attractions recommended for a traveler profile.
Traveler Match Count =
CALCULATE([Total Attractions], Attractions[family_score] >= 8)
```

```DAX
// Count of attractions suitable for a seasonal recommendation.
Season Ready Count =
CALCULATE([Total Attractions], Attractions[suggested_season_note] <> "Unknown")
```

## Best-practice guidance

- Use measures rather than calculated columns for aggregations.
- Keep measures readable and explainable to business users.
- Prefer simple, transparent formulas over overly complex logic.
- Use `SELECTEDVALUE` for clean titles and summaries.
