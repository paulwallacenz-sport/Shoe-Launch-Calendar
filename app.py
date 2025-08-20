import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Shoe Launch Calendar")

# --- Load Data ---
@st.cache_data
def load_data():
    return pd.read_csv("shoe-launch-grid-by-month.csv")

df = load_data()
df = df.rename(columns={df.columns[0]: "Brand"})

# --- Extract Year, Month Columns ---
data_cols = [col for col in df.columns if '-' in col]
years = sorted(list(set([col.split('-')[0] for col in data_cols])))
months_ordered = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
months = [m for m in months_ordered if any(col.endswith(m) for col in data_cols)]
brands = sorted(df["Brand"].unique())

# --- Sidebar/Top Filters ---
col1, col2, col3, col4 = st.columns([1,1,1,2])
with col1:
    year_filter = st.selectbox("Year", ["All"] + years)
with col2:
    month_filter = st.selectbox("Month", ["All"] + months)
with col3:
    brand_filter = st.selectbox("Brand", ["All"] + brands)
with col4:
    search_term = st.text_input("Search for a specific shoe here")  # Placeholder shown automatically

# --- Filter Columns for Year/Month ---
filtered_cols = data_cols
if year_filter != "All":
    filtered_cols = [col for col in filtered_cols if col.startswith(year_filter)]
if month_filter != "All":
    filtered_cols = [col for col in filtered_cols if col.endswith(month_filter)]

# --- Filter Rows by Brand & Search ---
data_to_show = df.copy()
if brand_filter != "All":
    data_to_show = data_to_show[data_to_show["Brand"] == brand_filter]

# Search filter (checks all visible cells)
if search_term:
    row_mask = data_to_show.apply(
        lambda row: any(search_term.lower() in str(val).lower() for val in row[filtered_cols]), axis=1)
    data_to_show = data_to_show[row_mask]

display_cols = ["Brand"] + filtered_cols

# --- Count Row at the Top ---
def cell_count(cell):
    if pd.isna(cell) or cell in ["None", "nan"]:
        return 0
    # Split on comma, ignore empty entries
    return len([x for x in str(cell).split(',') if x.strip()])

count_row = ["Count"]
for col in filtered_cols:
    count = data_to_show[col].apply(cell_count).sum()
    count_row.append(count)

data_display = pd.concat(
    [pd.DataFrame([count_row], columns=display_cols), data_to_show[display_cols]],
    ignore_index=True)

# --- Calendar Table ---
st.dataframe(data_display, use_container_width=True, hide_index=True)

# --- Prepare Data for Visualizations ---
# Long format for charts
long_rows = []
for _, row in df.iterrows():
    brand = row["Brand"]
    for col in data_cols:
        year, month = col.split('-')
        vals = [] if pd.isna(row[col]) or row[col] in ["None", "nan"] else [x.strip() for x in str(row[col]).split(',')]
        for shoe in vals:
            if shoe:
                long_rows.append({"Brand": brand, "Year": year, "Month": month, "Shoe": shoe})

long_df = pd.DataFrame(long_rows)

# Apply filters to long_df
if year_filter != "All":
    long_df = long_df[long_df["Year"] == year_filter]
if month_filter != "All":
    long_df = long_df[long_df["Month"] == month_filter]
if brand_filter != "All":
    long_df = long_df[long_df["Brand"] == brand_filter]
if search_term:
    long_df = long_df[long_df["Shoe"].str.contains(search_term, case=False, na=False)]

# --- Bar Chart: Launches by Brand (per Year) ---
st.subheader("Launches by Brand (per Year)")
if not long_df.empty:
    launches_brand_year = long_df.groupby(["Brand", "Year"]).size().unstack(fill_value=0)
    st.bar_chart(launches_brand_year)
else:
    st.info("No launches to display for current filter.")

# --- Bar Chart: Launches by Brand (per Quarter) ---
# We'll add a 'Quarter' column first
quarter_map = {'Jan':'Q1','Feb':'Q1','Mar':'Q1',
               'Apr':'Q2','May':'Q2','Jun':'Q2',
               'Jul':'Q3','Aug':'Q3','Sep':'Q3',
               'Oct':'Q4','Nov':'Q4','Dec':'Q4'}
long_df['Quarter'] = long_df['Month'].map(quarter_map)

st.subheader("Launches by Brand (per Quarter, Stacked by Year)")
if not long_df.empty:
    launches_brand_qtr = long_df.groupby(["Brand", "Year", "Quarter"]).size().reset_index(name='Count')
    pivot = launches_brand_qtr.pivot_table(index=["Brand", "Quarter"], columns="Year", values="Count", fill_value=0)
    st.dataframe(pivot)
    # Optionally, show a bar chart just for one quarter at a time:
    sel_qtr = st.selectbox("Select Quarter for Bar Chart", ['All'] + ['Q1','Q2','Q3','Q4'])
    if sel_qtr != 'All':
        chartdata = launches_brand_qtr[launches_brand_qtr['Quarter']==sel_qtr].pivot(index='Brand', columns='Year', values='Count').fillna(0)
        st.bar_chart(chartdata)
else:
    st.info("No launches to display for current filter.")

st.caption("Use the filters above to explore launches for any combination of year, month, brand or search for a shoe!")
