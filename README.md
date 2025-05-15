# 🚔 Charlottesville Crime Data Dashboard

An interactive dashboard built with [Streamlit](https://streamlit.io/) to explore and visualize crime data in Charlottesville, VA. This project empowers residents, researchers, and policymakers to better understand local crime patterns through engaging visuals and dynamic filtering.

🔗 **Live App**: [charlottesville-crime-data.streamlit.app](https://charlottesville-crime-data.streamlit.app/)  
📁 **Repository**: You're here!  
📊 **Powered by Open Data Charlottesville**

---

## 🔍 Features

### 🎛️ Dynamic Filters
Cascading dropdowns let you slice the data by:
- Neighborhood
- Offense type
- Agency
- Location type
- And more

Each filter updates the rest—making exploration intuitive and flexible.

### 📈 Key Metrics
Track key stats like:
- **Total Incidents**
- **Recent Activity** (e.g., last 7 days, last 30 days)
- **Growth Rates** (Week-over-Week, Month-over-Month, Year-over-Year)

### 📊 Rich Visualizations
Explore data through:
- **Line & Bar Charts** – by day, week, month, quarter, and year
- **Pie Charts** – for location type and agency breakdowns
- **Time-of-Day & Day-of-Week** charts
- **Seasonal trends**
- **Heatmap** for geospatial density

### ⚙️ Configurable Environment
The project includes a `config.py` to manage working directories and environment settings—keeping your code clean and modular.

### 🚀 Easy to Deploy & Refresh
- **Streamlit Cloud-ready**
- Set up for **daily refreshes** using GitHub Actions or built-in caching mechanisms (`st.cache_data(ttl=86400)`)

---

## 📁 Project Structure

```bash
├── .streamlit/
├── config.py
├── crime_data_dashboard.py
├── requirements.txt
├── utils/
│   ├── filters.py
│   ├── metrics.py
│   └── visualizations.py
└── README.md
