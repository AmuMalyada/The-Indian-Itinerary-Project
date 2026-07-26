# Visual specifications

## Page 1 — Executive Overview

Purpose: executive summary of destination health and tourism opportunity.

- KPI cards: Total Attractions, Total Cities, Total States, Average Rating, Average Daily Cost, Average Visit Duration, Popularity Index.
- Visuals:
  - Filled map of India by state with attraction count.
  - Top states bar chart.
  - Category distribution donut chart.
  - Rating distribution histogram.
  - Executive summary text box with key insights.
- Filters: State, Budget Category, Travel Complexity, Popularity Tier.
- Interaction: map selection filters all other visuals.

## Page 2 — Destination Explorer

Purpose: allow users to search and understand a single destination.

- Slicers: State, City, Attraction Type, Budget Category, Popularity Tier.
- Table: destination name, city, state, rating, budget, duration, best time to visit, seasonal note.
- Cards: rating, budget, best time, travel complexity.
- Visuals: weather summary, tag summary, attraction profile narrative.
- Interaction: selection from the table updates cards and supporting visuals.

## Page 3 — Budget Intelligence

Purpose: explain price sensitivity and cost-performance trade-offs.

- Visuals:
  - Stacked column chart: average budget by state.
  - Scatter plot: rating vs budget by attraction type.
  - Histogram: cost distribution.
  - Box plot: cost dispersion by category.
  - Outlier callout for high-cost or unusually cheap destinations.
- Filters: Budget Category, State, Attraction Type.

## Page 4 — Season & Climate

Purpose: show where climate and timing make travel attractive.

- Visuals:
  - Heatmap of seasonal suitability by state.
  - Line chart for monthly temperature trends.
  - Matrix of state vs season suitability.
  - Recommended visit months table.
- Filters: State, Season, Temperature band.

## Page 5 — Tourism Insights

Purpose: highlight what is driving attention and interest.

- Visuals:
  - Treemap of attraction types by review volume.
  - Bar chart of top-rated attractions.
  - Line chart of rating trend by state.
  - Ranking table for top destinations by popularity and rating.
- Filters: Category, State, Popularity Tier.

## Page 6 — Recommendation Explorer

Purpose: show traveler-specific suitability.

- Visuals:
  - Cards for Family Friendly, Solo Friendly, Couple Friendly, Adventure, Nature, Culture, Backpacker.
  - Scatter plot of popularity vs budget by traveler profile.
  - Matrix of traveler persona vs attraction category.
- Filters: Budget, Travel Complexity, State.

## Page 7 — Data Quality Dashboard

Purpose: prove the data foundation is trustworthy.

- Visuals:
  - KPI cards: coverage, missing values, duplicate counts, validation pass rate.
  - Bar chart: missing values by column.
  - Area chart: pipeline validation trend.
  - Feature engineering summary table.
- Filters: Data source, validation status.
