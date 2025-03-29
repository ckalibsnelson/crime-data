Charlottesville Crime Data Dashboard

This project is a Streamlit-based dashboard for exploring and visualizing crime data in Charlottesville. It provides interactive charts, dynamic filters, and various metrics to help users understand trends and patterns in the city's crime data.

Features

Dynamic Filters:
Cascading filters let users select criteria (such as Neighborhood, Offense, Agency, etc.) and dynamically update the available options for all other filters.

Interactive Metrics:
Display key metrics such as Total Incidents, Incidents in various time ranges (last month, last 7 days, etc.), and growth rates (MoM, QoQ, YoY, WoW).

Multiple Visualizations:
View data trends over time (daily, weekly, monthly, quarterly, and yearly), bar charts by season, day of week, time of day, and pie charts for location distributions. A density map visualizes incident frequency geographically.

Configurable Environment:
The working directory is stored in a separate configuration file (config.py), keeping your main code clean.

Deployable & Refreshable:
The app is set up for deployment on Streamlit Cloud and can be scheduled (via GitHub Actions or Streamlit cache TTL) to refresh daily.