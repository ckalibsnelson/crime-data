import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
from dotenv import load_dotenv

# To run:
# python -m streamlit run charlottesville_crime_data.py

st.set_page_config(page_title="Charlottesville: Crime Data", layout="wide")

# Load environment variables from .env (for local development)
load_dotenv()

# First, try to use secrets from the .streamlit/secrets.toml file in the working directory
try:
    secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        st.secrets = st.secrets.from_toml(secrets_path)
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        WORKING_DIR = st.secrets["WORKING_DIR"]
    else:
        raise FileNotFoundError
except Exception as e:
    GOOGLE_API_KEY = None
    WORKING_DIR = None

# If not found, try to use st.secrets from Streamlit Cloud
if GOOGLE_API_KEY is None or WORKING_DIR is None:
    try:
        secrets = st.secrets["general"]
        GOOGLE_API_KEY = secrets["GOOGLE_API_KEY"]
        WORKING_DIR = secrets["WORKING_DIR"]
    except Exception as e:
        st.warning(f"Error accessing st.secrets: {e}")
        GOOGLE_API_KEY = None
        WORKING_DIR = None

#######################################
# Data Loading with Caching & Refresh Option
#######################################

@st.cache_data(ttl=60)
def load_data(file_mtime):
    # Use WORKING_DIR from secrets
    working_dir = WORKING_DIR
    if working_dir:
        excel_path = os.path.join(working_dir, "data", "charlottesville_crime_incidents.xlsx")
    else:
        st.error("WORKING_DIR is not set. Please check your configuration.")
        return pd.DataFrame(), None

    if not excel_path.endswith('.xlsx'):
        st.error(f"File at {excel_path} is not a valid Excel file.")
        return pd.DataFrame(), excel_path

    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        st.error(f"Error reading Excel file at {excel_path}: {e}. Make sure 'openpyxl' is installed.")
        return pd.DataFrame(), excel_path

    df["zip"] = df["zip"].astype(str)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    else:
        st.error("The 'Date' column is missing from the data. Please check your data source.")
        return pd.DataFrame(), excel_path

    return df, excel_path

# Determine the path and get its modification time
data_file = os.path.join(WORKING_DIR, "data", "charlottesville_crime_incidents.xlsx")
file_mtime = os.path.getmtime(data_file)

# Add a refresh button to force a reload of the data
if st.button("Refresh Data"):
    load_data.clear()  # Clear the cached data
    file_mtime = os.path.getmtime(data_file)
    df, csv_path = load_data(file_mtime)
else:
    df, csv_path = load_data(file_mtime)

# Check if 'Date' column exists
if 'Date' not in df.columns:
    st.error("The 'Date' column is missing from the data. Please check the file.")
    st.stop()  # Stop further execution

# Calculate the latest refresh date
latest_refresh_date = df["Date"].max().date()
dashboard_refresh_date = datetime.datetime.now().date()

#######################################
# Title, Data Source, and Summary
#######################################

st.title("Charlottesville: Crime Data")
st.markdown("""
**Data Source:** [https://opendata.charlottesville.org/datasets/charlottesville::crime-data/about](https://opendata.charlottesville.org/datasets/charlottesville::crime-data/about)
""")

# Check if the DataFrame is empty or missing the 'Date' column
if df.empty or 'Date' not in df.columns:
    st.error("Data could not be loaded or the 'Date' column is missing. Please check your file path and data source.")
    st.stop()  # Stop further execution

# Calculate the latest refresh date
latest_refresh_date = df["Date"].max().date()
st.markdown(f"**Most Recent Date from Data Source:** {latest_refresh_date}")

# Add a date for when the dashboard was last refreshed
dashboard_refresh_date = datetime.datetime.now().date()
st.markdown(f"**Dashboard Last Refreshed:** {dashboard_refresh_date}")

st.markdown("""
**Please Note:** When selecting filters, please be patient as the dashboard may take a moment to load. The "Running" symbol at the top right corner of the app indicates that the dashboard is processing your selection.
""")

st.markdown("""
**Summary:**         
*Crime data represents the initial information that is provided by individuals calling for police assistance. Please note that the dataset only contains the last 5 years.  Remaining information is often amended for accuracy after an Officer arrives and investigates the reported incident. Most often, the changes are made to more accurately reflect the official legal definition of the crimes reported. An example of this is for someone to report that they have been "robbed," when their home was broken into while they were away. The official definition of "robbery" is to take something by force.  An unoccupied home being broken into, is actually defined as a "burglary," or a "breaking and entering." While there are mechanisms in place to make each initial call as accurate as possible, some events require evaluation upon arrival.  
Caution should be used when making assumptions based solely on the data provided, as they may not represent the official crime reports.*
""")

#######################################
# Sidebar with Filters
#######################################

st.sidebar.title("Filters")

def get_options(col, df):
    """
    Return sorted unique values (as strings) for the given column.
    This includes "N/A" values so that the default view includes all data.
    """
    return sorted(df[col].astype(str).dropna().unique())

with st.sidebar.expander("Color Palette", expanded=False):
    color_palettes = {
        "Plotly": px.colors.qualitative.Plotly,
        "Blues": px.colors.sequential.Blues,
        "Inferno": px.colors.sequential.Inferno,
        "Viridis": px.colors.sequential.Viridis,
        "Plasma": px.colors.sequential.Plasma,
        "Rainbow": px.colors.sequential.Rainbow
    }
    selected_palette = st.selectbox("Select a Color Palette", list(color_palettes.keys()), index=0)

with st.sidebar.expander("Date Range", expanded=False):
    min_date = df["Date"].dropna().min().date()
    max_date = df["Date"].dropna().max().date()
    start_date = st.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)

with st.sidebar.expander("Neighborhood", expanded=False):
    neighborhood_options = get_options("neighborhood", df)
    select_all_neighborhoods = st.checkbox("Select All Neighborhoods", value=True)
    if select_all_neighborhoods:
        selected_neighborhood = st.multiselect("Select Neighborhood(s)", options=neighborhood_options, default=neighborhood_options)
    else:
        selected_neighborhood = st.multiselect("Select Neighborhood(s)", options=neighborhood_options)

# Filter the DataFrame based on the selected neighborhood(s)
if selected_neighborhood:
    filtered_df = df[df["neighborhood"].astype(str).isin(selected_neighborhood)]
else:
    filtered_df = df

with st.sidebar.expander("Zip", expanded=False):
    zip_options = get_options("zip", filtered_df)
    select_all_zips = st.checkbox("Select All Zips", value=True)
    if select_all_zips:
        selected_zip = st.multiselect("Select Zip(s)", options=zip_options, default=zip_options)
    else:
        selected_zip = st.multiselect("Select Zip(s)", options=zip_options)

with st.sidebar.expander("FullStreet", expanded=False):
    fullstreet_options = get_options("FullStreet", filtered_df)
    select_all_fullstreets = st.checkbox("Select All FullStreets", value=True)
    if select_all_fullstreets:
        selected_fullstreet = st.multiselect("Select FullStreet(s)", options=fullstreet_options, default=fullstreet_options)
    else:
        selected_fullstreet = st.multiselect("Select FullStreet(s)", options=fullstreet_options)

with st.sidebar.expander("Season", expanded=False):
    season_options = get_options("Season", filtered_df)
    select_all_seasons = st.checkbox("Select All Seasons", value=True)
    if select_all_seasons:
        selected_season = st.multiselect("Select Season(s)", options=season_options, default=season_options)
    else:
        selected_season = st.multiselect("Select Season(s)", options=season_options)

with st.sidebar.expander("Weekend", expanded=False):
    weekend_options = [True, False]
    select_all_weekends = st.checkbox("Select All Weekends", value=True)
    if select_all_weekends:
        selected_weekend = st.multiselect("Select Weekend/Not Weekend", options=weekend_options, default=weekend_options)
    else:
        selected_weekend = st.multiselect("Select Weekend/Not Weekend", options=weekend_options)

with st.sidebar.expander("Day of Week", expanded=False):
    dow_options = get_options("DayOfWeek", filtered_df)
    select_all_days = st.checkbox("Select All Days", value=True)
    if select_all_days:
        selected_dayofweek = st.multiselect("Select Day(s)", options=dow_options, default=dow_options)
    else:
        selected_dayofweek = st.multiselect("Select Day(s)", options=dow_options)

with st.sidebar.expander("Time of Day", expanded=False):
    tod_options = get_options("TimeOfDay", filtered_df)
    select_all_times = st.checkbox("Select All Times", value=True)
    if select_all_times:
        selected_tod = st.multiselect("Select Time of Day", options=tod_options, default=tod_options)
    else:
        selected_tod = st.multiselect("Select Time of Day", options=tod_options)

with st.sidebar.expander("Agency", expanded=False):
    agency_options = get_options("Agency", filtered_df)
    select_all_agencies = st.checkbox("Select All Agencies", value=True)
    if select_all_agencies:
        selected_agency = st.multiselect("Select Agency", options=agency_options, default=agency_options)
    else:
        selected_agency = st.multiselect("Select Agency", options=agency_options)

with st.sidebar.expander("Offense", expanded=False):
    offense_options = get_options("Offense", filtered_df)
    select_all_offenses = st.checkbox("Select All Offenses", value=True)
    if select_all_offenses:
        selected_offense = st.multiselect("Select Offense(s)", options=offense_options, default=offense_options)
    else:
        selected_offense = st.multiselect("Select Offense(s)", options=offense_options)

with st.sidebar.expander("Reporting Officer", expanded=False):
    reporting_options = get_options("ReportingOfficer", filtered_df)
    select_all_reporting = st.checkbox("Select All Reporting Officers", value=True)
    if select_all_reporting:
        selected_reporting = st.multiselect("Select Reporting Officer(s)", options=reporting_options, default=reporting_options)
    else:
        selected_reporting = st.multiselect("Select Reporting Officer(s)", options=reporting_options)

#######################################
# Filter Data Based on Selections
#######################################

filtered_df = filtered_df[
    (filtered_df["Date"].dt.date >= start_date) &
    (filtered_df["Date"].dt.date <= end_date) &
    (filtered_df["Offense"].isin(selected_offense)) &
    (filtered_df["ReportingOfficer"].astype(str).isin(selected_reporting)) &
    (filtered_df["Agency"].isin(selected_agency)) &
    (filtered_df["TimeOfDay"].isin(selected_tod)) &
    (filtered_df["DayOfWeek"].isin(selected_dayofweek)) &
    (filtered_df["Weekend"].isin(selected_weekend)) &
    (filtered_df["Season"].isin(selected_season)) &
    (filtered_df["FullStreet"].isin(selected_fullstreet)) &
    (filtered_df["zip"].isin(selected_zip)) &
    (filtered_df["neighborhood"].astype(str).isin(selected_neighborhood))
]

#######################################
# Metrics Section (New Layout: 6 Metrics per Row)
#######################################

# Calculate the total number of incidents for percentage calculation
total_incidents = filtered_df["IncidentID"].nunique()

st.header("Metrics")

current_date = pd.to_datetime("today").normalize()
current_year = current_date.year
current_month = current_date.month

# Existing metrics calculations
incidents_last7days = filtered_df[filtered_df["Date"].dt.date >= (current_date - pd.Timedelta(days=7)).date()]["IncidentID"].nunique()
df_this_year = filtered_df[filtered_df["Date"].dt.year == current_year]
df_this_month = df_this_year[df_this_year["Date"].dt.month == current_month]
incidents_last_month = df_this_year[
    (df_this_year["Date"] >= (current_date.replace(day=1) - pd.Timedelta(days=1)).replace(day=1)) &
    (df_this_year["Date"] < current_date.replace(day=1))
]["IncidentID"].nunique()
incidents_this_month = df_this_month["IncidentID"].nunique()
incidents_this_year = df_this_year["IncidentID"].nunique()

# Update deprecated frequency string 'M' to 'ME'
monthly_counts = df_this_year.groupby(pd.Grouper(key="Date", freq="ME"))["IncidentID"].nunique()
if len(monthly_counts) >= 2 and monthly_counts.iloc[-2] != 0:
    mom_growth = ((monthly_counts.iloc[-1] - monthly_counts.iloc[-2]) / monthly_counts.iloc[-2]) * 100
    mom_growth_str = f"{mom_growth:.1f}%"
else:
    mom_growth_str = "N/A"

start_ytd = datetime.date(current_year, 1, 1)
end_ytd = current_date.date()
current_ytd = df_this_year[(df_this_year["Date"].dt.date >= start_ytd) & (df_this_year["Date"].dt.date <= end_ytd)]["IncidentID"].nunique()

start_last_year = datetime.date(current_year - 1, 1, 1)
end_last_year = datetime.date(current_year - 1, current_date.month, current_date.day)
last_year_data = df[df["Date"].dt.year == current_year - 1]
last_year_ytd = last_year_data[(last_year_data["Date"].dt.date >= start_last_year) & (last_year_data["Date"].dt.date <= end_last_year)]["IncidentID"].nunique()
if last_year_ytd != 0:
    yoy_growth = ((current_ytd - last_year_ytd) / last_year_ytd) * 100
    yoy_growth_str = f"{yoy_growth:.1f}%"
else:
    yoy_growth_str = "N/A"

# New metrics for the first row
incidents_last3days = filtered_df[filtered_df["Date"].dt.date >= (current_date - pd.Timedelta(days=3)).date()]["IncidentID"].nunique()
incidents_last2weeks = filtered_df[filtered_df["Date"].dt.date >= (current_date - pd.Timedelta(days=14)).date()]["IncidentID"].nunique()

# New metrics for the second row: Week over week growth and Quarter over quarter growth.
# Week over Week Growth:
last_week_start = (current_date - pd.Timedelta(days=7)).date()
last_week_end = (current_date - pd.Timedelta(days=1)).date()
previous_week_start = (current_date - pd.Timedelta(days=14)).date()
previous_week_end = (current_date - pd.Timedelta(days=8)).date()
last_week_count = filtered_df[(filtered_df["Date"].dt.date >= last_week_start) & (filtered_df["Date"].dt.date <= last_week_end)]["IncidentID"].nunique()
previous_week_count = filtered_df[(filtered_df["Date"].dt.date >= previous_week_start) & (filtered_df["Date"].dt.date <= previous_week_end)]["IncidentID"].nunique()
if previous_week_count != 0:
    wow_growth = ((last_week_count - previous_week_count) / previous_week_count) * 100
    wow_growth_str = f"{wow_growth:.1f}%"
else:
    wow_growth_str = "N/A"

# Quarter over Quarter Growth:
current_quarter = ((current_month - 1) // 3) + 1
quarter_start = datetime.date(current_year, (current_quarter - 1) * 3 + 1, 1)
current_quarter_count = filtered_df[(filtered_df["Date"].dt.date >= quarter_start) & (filtered_df["Date"].dt.date <= current_date.date())]["IncidentID"].nunique()

if current_quarter == 1:
    prev_year = current_year - 1
    prev_quarter = 4
    quarter_start_prev = datetime.date(prev_year, 10, 1)
    quarter_end_prev = datetime.date(prev_year, 12, 31)
else:
    prev_quarter = current_quarter - 1
    quarter_start_prev = datetime.date(current_year, (prev_quarter - 1) * 3 + 1, 1)
    quarter_end_prev = (datetime.date(current_year, prev_quarter * 3 + 1, 1) - pd.Timedelta(days=1)).date()

previous_quarter_count = filtered_df[(filtered_df["Date"].dt.date >= quarter_start_prev) & (filtered_df["Date"].dt.date <= quarter_end_prev)]["IncidentID"].nunique()
if previous_quarter_count != 0:
    qoq_growth = ((current_quarter_count - previous_quarter_count) / previous_quarter_count) * 100
    qoq_growth_str = f"{qoq_growth:.1f}%"
else:
    qoq_growth_str = "N/A"

# Calculate Most Frequent Offense.
offense_counts = (
    filtered_df.groupby("Offense")["IncidentID"]
    .nunique()
    .reset_index(name="Count")
    .sort_values("Count", ascending=False)
)
if not offense_counts.empty:
    most_freq_offense = offense_counts.iloc[0]["Offense"]
    most_freq_count = offense_counts.iloc[0]["Count"]
    total_offense_counts = offense_counts["Count"].sum()
    offense_percent = (most_freq_count / total_offense_counts) * 100
    offense_percent_str = f"{offense_percent:.1f}%"
else:
    most_freq_offense = "N/A"
    most_freq_count = 0
    offense_percent_str = "N/A"

# Layout for first row of metrics (6 metrics)
row1 = st.columns(6)
row1[0].metric("Total Incidents", total_incidents)
row1[1].metric("Incidents Last Month", incidents_last_month)
row1[2].metric("Incidents This Month", incidents_this_month)
row1[3].metric("Incidents Last 2 Weeks", incidents_last2weeks)
row1[4].metric("Incidents Last 7 Days", incidents_last7days)
row1[5].metric("Incidents Last 3 Days", incidents_last3days)

# Layout for second row of metrics (6 metrics)

# Conditional coloring for growth metrics
def get_color(value):
    if value == "N/A":
        return "off"
    return "inverse" if float(value[:-1]) < 0 else "normal"

row2 = st.columns(6)
row2[0].metric("Incidents This Year", incidents_this_year)
row2[1].metric("YoY Growth %", yoy_growth_str, delta_color=get_color(yoy_growth_str))
row2[2].metric("QoQ Growth %", qoq_growth_str, delta_color=get_color(qoq_growth_str))
row2[3].metric("MoM Growth %", mom_growth_str, delta_color=get_color(mom_growth_str))
row2[4].metric("WoW Growth %", wow_growth_str, delta_color=get_color(wow_growth_str))
# For Most Frequent Offense, display the percentage without the arrow.
row2[5].metric("Most Frequent Offense", f"{most_freq_offense} ({offense_percent_str})")

#######################################
# First Visualization: Incidents Over Time (Full Width)
#######################################

st.subheader("Incidents Over Time")

# Add "Yearly" as a resolution option.
resolution = st.selectbox("Select Resolution", ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"], index=0)

if resolution == "Daily":
    time_series = (
        filtered_df.groupby(filtered_df["Date"].dt.date)["IncidentID"]
        .nunique()
        .reset_index(name="Count")
    )
elif resolution == "Weekly":
    time_series = (
        filtered_df.groupby(pd.Grouper(key="Date", freq="W"))["IncidentID"]
        .nunique()
        .reset_index(name="Count")
    )
elif resolution == "Monthly":
    time_series = (
        filtered_df.groupby(pd.Grouper(key="Date", freq="M"))["IncidentID"]
        .nunique()
        .reset_index(name="Count")
    )
elif resolution == "Quarterly":
    time_series = (
        filtered_df.groupby(pd.Grouper(key="Date", freq="Q"))["IncidentID"]
        .nunique()
        .reset_index(name="Count")
    )
elif resolution == "Yearly":
    time_series = (
        filtered_df.groupby(pd.Grouper(key="Date", freq="Y"))["IncidentID"]
        .nunique()
        .reset_index(name="Count")
    )

# Use a bar chart instead of a line chart.
fig_time_series = px.bar(
    time_series,
    x="Date",
    y="Count",
    title=f"Incidents Over Time ({resolution} View)",
    color_discrete_sequence=[px.colors.qualitative.Plotly[0]]
)

# Update hover template to show percentage of total incidents
fig_time_series.update_traces(
    hovertemplate="<b>Date:</b> %{x}<br>" +
                  "<b>Incident Count:</b> %{y}<br>" +
                  "<b>Percent of Total Incidents:</b> %{customdata:.1%}<extra></extra>",
    customdata=time_series["Count"] / total_incidents
)

fig_time_series.update_layout(xaxis_title="Date", yaxis_title="Unique Incidents")
st.plotly_chart(fig_time_series, use_container_width=True)

#######################################
# Detailed Visualizations (Side by Side)
#######################################

st.subheader("Detailed Visualizations")
palette = color_palettes[selected_palette]

# Row 1: By Season, By Weekend, By Day of Week, By Time of Day
col1, col2, col3, col4 = st.columns(4)

# By Season – order seasons in natural order.
season_order = ["Winter", "Spring", "Summer", "Autumn"]
freq_season = (
    filtered_df.groupby("Season")["IncidentID"]
    .nunique()
    .reset_index(name="Frequency")
)
freq_season["PercentTotal"] = (freq_season["Frequency"] / total_incidents) * 100
fig_season = px.bar(
    freq_season, 
    x="Season", 
    y="PercentTotal", 
    title="By Season",
    color_discrete_sequence=palette, 
    text_auto=True,
    category_orders={"Season": season_order}
)
fig_season.update_traces(
    texttemplate='%{y:.1f}%',
    hovertemplate="<b>Season:</b> %{x}<br><b>Percent of Total:</b> %{y:.1f}%<extra></extra>"
)
col1.plotly_chart(fig_season, use_container_width=True)

# By Weekend
freq_weekend = (
    filtered_df.groupby("Weekend")["IncidentID"]
    .nunique()
    .reset_index(name="Frequency")
)
freq_weekend["PercentTotal"] = (freq_weekend["Frequency"] / total_incidents) * 100
fig_weekend = px.bar(
    freq_weekend, 
    x="Weekend", 
    y="PercentTotal", 
    title="By Weekend",
    color_discrete_sequence=palette, 
    text_auto=True
)
fig_weekend.update_traces(
    texttemplate='%{y:.1f}%',
    hovertemplate="<b>Weekend:</b> %{x}<br><b>Percent of Total:</b> %{y:.1f}%<extra></extra>"
)
col2.plotly_chart(fig_weekend, use_container_width=True)

# By Day of Week – order starting with Sunday.
weekday_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
freq_day = (
    filtered_df.groupby("DayOfWeek")["IncidentID"]
    .nunique()
    .reset_index(name="Frequency")
)
freq_day["PercentTotal"] = (freq_day["Frequency"] / total_incidents) * 100
freq_day["DayOfWeek"] = pd.Categorical(freq_day["DayOfWeek"], categories=weekday_order, ordered=True)
freq_day = freq_day.sort_values("DayOfWeek")
fig_day = px.bar(
    freq_day, 
    x="DayOfWeek", 
    y="PercentTotal", 
    title="By Day of Week",
    color_discrete_sequence=palette, 
    text_auto=True,
    category_orders={"DayOfWeek": weekday_order}
)
fig_day.update_traces(
    texttemplate='%{y:.1f}%',
    hovertemplate="<b>Day of Week:</b> %{x}<br><b>Percent of Total:</b> %{y:.1f}%<extra></extra>"
)
col3.plotly_chart(fig_day, use_container_width=True)

# By Time of Day – order by the natural occurrence.
time_order = ["Early Morning", "Morning", "Afternoon", "Evening", "Night"]
freq_tod = (
    filtered_df.groupby("TimeOfDay")["IncidentID"]
    .nunique()
    .reset_index(name="Frequency")
)
freq_tod["PercentTotal"] = (freq_tod["Frequency"] / total_incidents) * 100
freq_tod["TimeOfDay"] = pd.Categorical(freq_tod["TimeOfDay"], categories=time_order, ordered=True)
freq_tod = freq_tod.sort_values("TimeOfDay")
fig_tod = px.bar(
    freq_tod, 
    x="TimeOfDay", 
    y="PercentTotal", 
    title="By Time of Day",
    color_discrete_sequence=palette, 
    text_auto=True,
    category_orders={"TimeOfDay": time_order}
)
fig_tod.update_traces(
    texttemplate='%{y:.1f}%',
    hovertemplate="<b>Time of Day:</b> %{x}<br><b>Percent of Total:</b> %{y:.1f}%<extra></extra>"
)
col4.plotly_chart(fig_tod, use_container_width=True)

#######################################
# Offense & Reporting Officer Visualizations
#######################################

st.subheader("Offense & Reporting Officer Visualizations")

# Offense Visualizations: Top 10 and Bottom 10 Offenses
col_off_top, col_off_bottom = st.columns(2)

offense_counts_filtered = (
    filtered_df.groupby("Offense")["IncidentID"]
    .nunique()
    .reset_index(name="Count")
)

top10_offenses = offense_counts_filtered.sort_values("Count", ascending=False).head(10)
top10_offenses["PercentTotal"] = (top10_offenses["Count"] / total_incidents) * 100
fig_top10_offenses = px.bar(
    top10_offenses, 
    x="Offense", 
    y="PercentTotal", 
    title="Top 10 Offenses",
    color_discrete_sequence=palette, 
    text_auto=True
)
fig_top10_offenses.update_traces(
    texttemplate='%{y:.1f}%',
    hovertemplate="<b>Offense:</b> %{x}<br><b>Percent of Total:</b> %{y:.1f}%<extra></extra>"
)
col_off_top.plotly_chart(fig_top10_offenses, use_container_width=True)

bottom10_offenses = offense_counts_filtered.sort_values("Count", ascending=True).head(10)
bottom10_offenses["PercentTotal"] = (bottom10_offenses["Count"] / total_incidents) * 100
fig_bottom10_offenses = px.bar(
    bottom10_offenses, 
    x="Offense", 
    y="PercentTotal", 
    title="Bottom 10 Offenses",
    color_discrete_sequence=palette, 
    text_auto=True
)
fig_bottom10_offenses.update_traces(
    texttemplate='%{y:.1f}%',
    hovertemplate="<b>Offense:</b> %{x}<br><b>Percent of Total:</b> %{y:.1f}%<extra></extra>"
)
col_off_bottom.plotly_chart(fig_bottom10_offenses, use_container_width=True)

# Reporting Officer Visualization – sort in descending order.
st.subheader("Reporting Officer Visualization")
reporting_counts = (
    filtered_df.groupby("ReportingOfficer")["IncidentID"]
    .nunique()
    .reset_index(name="Count")
)
reporting_counts["PercentTotal"] = (reporting_counts["Count"] / total_incidents) * 100
reporting_counts = reporting_counts.sort_values("Count", ascending=False)
fig_reporting = px.bar(
    reporting_counts, 
    x="ReportingOfficer", 
    y="PercentTotal", 
    title="Reporting Officer Breakdown",
    color_discrete_sequence=palette, 
    text_auto=True
)
fig_reporting.update_traces(
    texttemplate='%{y:.1f}%',
    hovertemplate="<b>Reporting Officer:</b> %{x}<br><b>Percent of Total:</b> %{y:.1f}%<extra></extra>"
)
st.plotly_chart(fig_reporting, use_container_width=True)

#######################################
# Location Distributions (Pie Charts)
#######################################

st.subheader("Location Distributions")

# First row: Zip Distribution and Neighborhood Distribution
col_zip, col_nb = st.columns(2)

# Zip Distribution (All) – same size as others.
zip_counts = (
    filtered_df.groupby("zip")["IncidentID"]
    .nunique()
    .reset_index(name="Count")
)
total_zip = zip_counts["Count"].sum()
zip_counts["PercentTotal"] = zip_counts["Count"] / total_incidents * 100
fig_zip = px.pie(
    zip_counts,
    names="zip",
    values="Count",
    title="Zip Distribution (All)",
    hole=0.3,
    color_discrete_sequence=palette
)
fig_zip.update_traces(
    text=[f"{pct:.1f}%" for pct in zip_counts["PercentTotal"]],
    textinfo="text",
    textposition="inside",
    hovertemplate="<b>%{label}</b><br>Percentage: %{text}<extra></extra>"
)
fig_zip.update_layout(height=800, width=800)
col_zip.plotly_chart(fig_zip, use_container_width=True)

# Neighborhood Distribution (All)
nb_counts = (
    filtered_df.groupby("neighborhood")["IncidentID"]
    .nunique()
    .reset_index(name="Count")
)
total_nb = nb_counts["Count"].sum()
nb_counts["PercentTotal"] = nb_counts["Count"] / total_nb * 100
fig_nb = px.pie(
    nb_counts,
    names="neighborhood",
    values="Count",
    title="Neighborhood Distribution (All)",
    hole=0.3,
    color_discrete_sequence=palette
)
fig_nb.update_traces(
    text=[f"{pct:.1f}%" for pct in nb_counts["PercentTotal"]],
    textinfo="text",
    textposition="inside",
    hovertemplate="<b>%{label}</b><br>Percentage: %{text}<extra></extra>"
)
fig_nb.update_layout(height=800, width=800)
col_nb.plotly_chart(fig_nb, use_container_width=True)

# Second row: FullStreet Distribution and Offense Distribution
col_fs, col_offense = st.columns(2)

# FullStreet Distribution (Top 25)
fs_counts = (
    filtered_df.groupby("FullStreet")["IncidentID"]
    .nunique()
    .reset_index(name="Count")
)
total_fs = fs_counts["Count"].sum()
top25_fs = fs_counts.sort_values("Count", ascending=False).head(25)
top25_fs["PercentTotal"] = top25_fs["Count"] / total_fs * 100
fig_fs = px.pie(
    top25_fs,
    names="FullStreet",
    values="Count",
    title="FullStreet Distribution (Top 25)",
    hole=0.3,
    color_discrete_sequence=palette
)
fig_fs.update_traces(
    text=[f"{pct:.1f}%" for pct in top25_fs["PercentTotal"]],
    textinfo="text",
    textposition="inside",
    hovertemplate="<b>%{label}</b><br>Percentage: %{text}<extra></extra>"
)
fig_fs.update_layout(height=800, width=800)
col_fs.plotly_chart(fig_fs, use_container_width=True)

# Offense Distribution (Top 25)
offense_counts = (
    filtered_df.groupby("Offense")["IncidentID"]
    .nunique()
    .reset_index(name="Count")
)
total_offense = offense_counts["Count"].sum()
top25_offense = offense_counts.sort_values("Count", ascending=False).head(25)
top25_offense["PercentTotal"] = top25_offense["Count"] / total_offense * 100
fig_offense = px.pie(
    top25_offense,
    names="Offense",
    values="Count",
    title="Offense Distribution (Top 25)",
    hole=0.3,
    color_discrete_sequence=palette
)
fig_offense.update_traces(
    text=[f"{pct:.1f}%" for pct in top25_offense["PercentTotal"]],
    textinfo="text",
    textposition="inside",
    hovertemplate="<b>%{label}</b><br>Percentage: %{text}"
)
fig_offense.update_layout(height=800, width=800)
col_offense.plotly_chart(fig_offense, use_container_width=True)

#######################################
# Geographic Visualization (Heat Map)
#######################################

st.subheader("Geographic Visualization")

# Create a column to represent the intensity of incidents per location
filtered_df["IncidentCount"] = filtered_df.groupby(["lat", "lon"])["IncidentID"].transform("count")

# Use density_mapbox for geographic visualization
fig_geo = px.density_mapbox(
    filtered_df,
    lat="lat",
    lon="lon",
    z="IncidentCount",  # use the new column for intensity
    radius=10,
    center=dict(lat=38.0293, lon=-78.4767),  # approximate center of Charlottesville
    zoom=14,
    mapbox_style="open-street-map",
    title="Incident Frequency by Geography"
)
fig_geo.update_layout(height=1200, width=1200)

# Calculate the total number of incidents for percentage calculation
total_incidents_geo = filtered_df["IncidentID"].nunique()

# Update hover template to show neighborhood, zip code, and percentage of total incidents
fig_geo.update_traces(
    hovertemplate="<b>Location:</b> %{lat}, %{lon}<br>" +
                  "<b>Neighborhood:</b> %{customdata[0]}<br>" +
                  "<b>Zip Code:</b> %{customdata[1]}<br>" +
                  "<b>Incident Count:</b> %{z}<br>" +
                  "<b>Percent of Total Incidents:</b> %{customdata[2]:.1%}<extra></extra>",
    customdata=filtered_df[["neighborhood", "zip", "IncidentCount"]].apply(lambda row: (row["neighborhood"], row["zip"], row["IncidentCount"] / total_incidents_geo), axis=1)
)

st.plotly_chart(fig_geo, use_container_width=True)

#######################################
# Interactive Table of Recent Incidents
#######################################

st.subheader("Recent 100 Incidents")
st.dataframe(filtered_df.sort_values(by="Date", ascending=False).head(100), use_container_width=True)

#######################################
# Data Dictionary & Metric Definitions
#######################################

st.subheader("Data Dictionary & Metric Definitions")
st.markdown("""
**Data Dictionary:**

- **RecordID:** Unique record identifier.
- **Offense:** Type/category of crime reported.
- **IncidentID:** Unique incident identifier.
- **Agency:** The agency handling the incident.
- **ReportingOfficer:** The officer who initially reported the incident.
- **TimeOfDay:** Categorical time of day (e.g., "Morning", "Afternoon").
- **Date:** Reported date and time.
- **DayOfWeek:** Day of the week when the incident occurred.
- **Weekend:** Boolean indicating if the incident occurred on a weekend.
- **Season:** Season during which the incident occurred.
- **FullStreet:** Block number and street name used for geocoding.
- **lat:** Latitude of the incident location.
- **lon:** Longitude of the incident location.
- **neighborhood:** Neighborhood associated with the incident.
- **zip:** Postal code for the incident location.

**Metric Definitions & Calculations:**

- **Total Incidents:** Count of unique IncidentIDs in the filtered data.
- **Incidents Last 7 Days:** Unique IncidentIDs for incidents that occurred in the past 7 days.
- **Incidents Last 3 Days:** Unique IncidentIDs for incidents that occurred in the past 3 days.
- **Incidents Yesterday:** Unique IncidentIDs for incidents that occurred yesterday.
- **Incidents Last Month:** Unique IncidentIDs from the previous month (based on filtered data).
- **Incidents This Month:** Unique IncidentIDs for the current month.
- **Incidents This Year:** Unique IncidentIDs for the current year.
- **MoM Growth %:** Month-over-Month growth percentage calculated as the percentage change in unique incidents between the last two months.
- **WoW Growth %:** Percentage change comparing the last 7-day period (excluding today) with the preceding 7-day period.
- **QoQ Growth %:** Percentage change comparing the current quarter (from its start to today) with the previous complete quarter.
- **YoY Growth %:** Year-over-Year growth percentage comparing the current year-to-date with the same period last year.
- **Most Frequent Offense:** The offense with the highest unique incident count (displayed as: offense name (count) - % of total).
""")

# Display the message about using secrets from Streamlit Cloud
#st.info("Using secrets from Streamlit Cloud")

# Print the path of the CSV file at the end
#st.write(f"Path of the CSV file: {csv_path}")

# Print the working directory at the end
# st.write(f"Current working directory: {os.getcwd()}")
