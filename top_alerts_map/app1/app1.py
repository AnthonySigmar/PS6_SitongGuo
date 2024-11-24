from shiny import App, ui, render
from shinywidgets import render_altair, output_widget
import pandas as pd
import altair as alt
import json
import tempfile

# Load data
file_path = "C:/Users/RedthinkerDantler/Documents/GitHub/DPPP2/PS6_SitongGuo/top_alerts_map/top_alerts_map.csv"
aggregated_df = pd.read_csv(file_path)

# Define the UI
app_ui = ui.page_fluid(
    ui.panel_title("Top Alerts Map"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "alert_choice",
                "Select Alert Type and Subtype:",
                sorted([
                    f"{row['updated_type']} - {row['updated_subtype']}"
                    for _, row in aggregated_df.iterrows()
                ]),
                selected="Jam - Heavy Traffic",
            )
        ),
        output_widget("map_plot")
    ),
)

def server(input, output, session):
    @output
    @render_altair
    def map_plot():
        # Filter data for the selected type and subtype
        selected_data = (
            aggregated_df[
                (aggregated_df["updated_type"] + " - " + aggregated_df["updated_subtype"])
                == input.alert_choice()
            ]
            .nlargest(10, "alert count")
            .reset_index(drop=True)
        )

        # Scatter Plot
        scatter = (
            alt.Chart(selected_data)
            .mark_circle(size=200)
            .encode(
                longitude='longitude:Q',
                latitude='latitude:Q',
                size=alt.Size('alert count:Q', scale=alt.Scale(range=[50, 500])),  
                color=alt.Color('alert count:Q', scale=alt.Scale(scheme='reds')),  
                tooltip=['latitude', 'longitude', 'alert count']
            )
        )

        # Load and prepare the Chicago map, 
        chicago_geojson_path = "C:/Users/RedthinkerDantler/Documents/GitHub/DPPP2/PS6_SitongGuo/top_alerts_map/chicago-boundaries.geojson"
        with open(chicago_geojson_path) as f:
            chicago_geojson = json.load(f)

        geo_data = alt.Data(values=chicago_geojson["features"])

        chicago_map = (
            alt.Chart(geo_data).mark_geoshape(fill="lightgray", stroke="white")
            .encode()
            .properties(width=800, height=600)
            .project(type="equirectangular")
        )

        # Combine the map and scatter plot
        # Set axis domains for alignment
        lat_min, lat_max = selected_data['latitude'].min() - 0.01, selected_data['latitude'].max() + 0.01
        lon_min, lon_max = selected_data['longitude'].min() - 0.01, selected_data['longitude'].max() + 0.01

        # Combine the layers!!
        combined_plot = (chicago_map + scatter).configure_view(
            stroke=None   
            # Remove the default borders around the map
        ).properties(
            width=550,
            height=400
        ).configure_title(
            fontSize=16,
            anchor="start"
        ).encode(
            x=alt.X('longitude:Q', scale=alt.Scale(domain=[lon_min, lon_max]), title="Longitude"),
            y=alt.Y('latitude:Q', scale=alt.Scale(domain=[lat_min, lat_max]), title="Latitude")
        )
        return combined_plot

app = App(app_ui, server)
