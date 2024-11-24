from shiny import App, ui, render
import pandas as pd
from shinywidgets import render_altair, output_widget
import altair as alt
import tempfile
import json

data_path = "C:/Users/RedthinkerDantler/Documents/GitHub/DPPP2/PS6_SitongGuo/top_alerts_map_byhour/top_alerts_map_byhour.csv"
data = pd.read_csv(data_path)
data['type_subtype'] = data['updated_type'] + ' - ' + data['updated_subtype']

type_subtype_choices = sorted([
    f"{row['updated_type']} - {row['updated_subtype']}"
    for _, row in data[['updated_type', 'updated_subtype']].drop_duplicates().iterrows()
])

# UI
app_ui = ui.page_fluid(
    ui.panel_title("Top Alerts Map by Hour"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "alert_choice",  
                "Select Alert Type and Subtype:",  
                type_subtype_choices,  
                selected=type_subtype_choices[0],  # Default selected value
            ),
            ui.input_slider(
                "hour_slider",  
                "Select Hour:",
                min=0,
                max=23,
                value=12,  # Default value (12:00 PM)
                step=1,
            ),
            ui.output_text("hour_label")  # To display the selected hour
        ),
            output_widget("hourly_plot")
    ),
)

# server
def server(input, output, session):
    @output
    @render.text
    def hour_label():
        return f"Displaying {input.hour_slider():02}:00"

    @output
    @render_altair
    def hourly_plot():
        selected_data = data[
            (data["type_subtype"] == input.alert_choice()) &
            (data["hour"] == f"{input.hour_slider():02}:00")
        ]
        
        scatter_layer = alt.Chart(selected_data).mark_circle().encode(
            longitude="longitude:Q",
            latitude="latitude:Q",
            size=alt.Size("alert_count:Q", scale=alt.Scale(range=[50, 500])),
            color=alt.Color("alert_count:Q", scale=alt.Scale(scheme="reds")),
            tooltip=["latitude", "longitude", "alert_count"]
        ).properties(
            width=800,
            height=600,
            title=f"Top 10 Alerts for {input.alert_choice()} at {input.hour_slider():02}:00"
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

        lat_min, lat_max = selected_data['latitude'].min() - 0.01, selected_data['latitude'].max() + 0.01
        lon_min, lon_max = selected_data['longitude'].min() - 0.01, selected_data['longitude'].max() + 0.01
        # Combine the layers!!
        combined_plot = (chicago_map + scatter_layer).configure_view(
            stroke=None   
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
