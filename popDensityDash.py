import streamlit as st
import plotly.express as px
import json
from shapely.geometry import shape
import pandas as pd

# Load GeoJSON files
with open('lad.json', 'r') as f:
    gb_geojson = json.load(f)
with open('lgd.json', 'r') as f:
    ni_geojson = json.load(f)

# Normalize property names
for feature in gb_geojson['features']:
    feature['properties']['Code'] = feature['properties']['LAD13CD']

for feature in ni_geojson['features']:
    feature['properties']['Code'] = feature['properties']['LGDCode']

# Combine features
combined_geojson = {
    "type": "FeatureCollection",
    "features": gb_geojson['features'] + ni_geojson['features']
}

# Calculate centroid latitude and longitude for each region
for feature in combined_geojson['features']:
    geometry = shape(feature['geometry'])
    centroid = geometry.centroid
    feature['properties']['Latitude'] = centroid.y
    feature['properties']['Longitude'] = centroid.x



# Load merged data
merged_df = pd.read_csv('https://drive.google.com/uc?export=download&id=1qJf_KpKh_Vg2kcwE8hxBVCepnhdgsG3s')

# Create dropdown options from unique values in 'Geography' and 'Region'
exclude_regions = ['Greater Manchester (Met County)', 'South Yorkshire (Met County)', 'West Midlands (Met County)', 'West Yorkshire (Met County)']
geography_options = [{'label': geography, 'value': geography} for geography in merged_df['Geography'].unique() if geography not in exclude_regions]
region_options = [{'label': region, 'value': region} for region in merged_df['Region'].unique() if region not in exclude_regions]
search_options = geography_options + region_options

# Define layout
st.title("UK Population Density Dashboard")

geo_grouping = st.selectbox("Select a geographic group", ['All Regions', 'Unitary Authority', 'Metropolitan District', 'Non-metropolitan District', 'London Borough', 'Council Area', 'Local Government District'])
selected_year = st.selectbox("Select year", [2022, 2011], index=0)
selected_sex = st.selectbox("Select sex", ['All Genders', 'Male', 'Female'])
selected_age = st.selectbox("Select age", ['All Ages'] + list(range(merged_df['Age'].min(), merged_df['Age'].max() + 1)), index=0)
colorscale = st.selectbox("Select a colour theme", px.colors.named_colorscales(), index=0)

fig1 = px.choropleth_mapbox(
    merged_df,
    geojson=combined_geojson,
    locations='Code',
    color='Group Population Density 2022 (per km2)' if selected_year == 2022 else 'Group Population Density 2011 (per km2)',
    hover_name='Region',
    hover_data={
        'Group Population Density 2022 (per km2)' if selected_year == 2022 else 'Group Population Density 2011 (per km2)': True,
        'Region Estimated Population mid-2022': True,
        'Region Area (sq km)': True,
        'Region Population Density 2022 (per km2)': True,
        'Region Population Density 2011 (per km2)': True,
        'Region Population Growth Rate (%)': True,
        'Code': False
    },
    featureidkey="properties.Code",
    color_continuous_scale=colorscale,
    range_color=[0, merged_df['Group Population Density 2022 (per km2)' if selected_year == 2022 else 'Group Population Density 2011 (per km2)'].max()],
    mapbox_style="carto-positron",
    zoom=4.5,
    center={"lat": 55, "lon": -3},
    opacity=0.6,
    labels={'Group Population Density 2022 (per km2)' if selected_year == 2022 else 'Group Population Density 2011 (per km2)': 'People per km2'}
)

st.plotly_chart(fig1)

search_value = st.text_input("Enter a place...")
comparison_option = st.selectbox("Select comparison option", ['Year', 'Gender', 'Age', 'Age Group', 'Region Area (sq km)', 'Region Estimated Population mid-2022', 'Region Estimated Population mid-2011', 'Region Population Growth Rate (%)'])

if comparison_option in ['Year', 'Gender', 'Age', 'Age Group']:
    fig2 = px.bar(
        merged_df,
        x='Region',
        y='Group Population Density 2022 (per km2)' if selected_year == 2022 else 'Group Population Density 2011 (per km2)',
        color='Sex' if comparison_option == 'Gender' else 'Age' if comparison_option in ['Age', 'Age Group'] else None,
        barmode='group',
        hover_data=['Region Estimated Population mid-2022', 'Region Area (sq km)', 'Region Population Growth Rate (%)'],
        labels={'Group Population Density 2022 (per km2)' if selected_year == 2022 else 'Group Population Density 2011 (per km2)': 'Population Density (per km2)'}
    )
    st.plotly_chart(fig2)
elif comparison_option in ['Region Area (sq km)', 'Region Estimated Population mid-2022', 'Region Estimated Population mid-2011', 'Region Population Growth Rate (%)']:
    fig3 = px.bar(
        merged_df.groupby('Region').agg({
            'Region Area (sq km)' if comparison_option == 'Region Area (sq km)' else 'Region Estimated Population mid-2022' if comparison_option == 'Region Estimated Population mid-2022' else 'Region Estimated Population mid-2011' if comparison_option == 'Region Estimated Population mid-2011' else 'Region Population Growth Rate (%)': 'mean'
        }).reset_index(),
        x='Region',
        y='Region Area (sq km)' if comparison_option == 'Region Area (sq km)' else 'Region Estimated Population mid-2022' if comparison_option == 'Region Estimated Population mid-2022' else 'Region Estimated Population mid-2011' if comparison_option == 'Region Estimated Population mid-2011' else 'Region Population Growth Rate (%)',
        color_discrete_sequence=['YellowGreen', 'SeaGreen', 'Teal', '#483D8B'],
        labels={'Region Area (sq km)' if comparison_option == 'Region Area (sq km)' else 'Region Estimated Population mid-2022' if comparison_option == 'Region Estimated Population mid-2022' else 'Region Estimated Population mid-2011' if comparison_option == 'Region Estimated Population mid-2011' else 'Region Population Growth Rate (%)': 'Value'}
    )
    st.plotly_chart(fig3)