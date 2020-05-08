from flask import Flask, render_template, request
import pandas as pd
import geopandas as gpd
import sqlite3 as lite
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, LinearColorMapper, ColorBar, SingleIntervalTicker, HoverTool
from bokeh.embed import components
import math
import calendar
import utils

app = Flask(__name__)

# Options of categories, years, and months
list_cat = ['Total N2']
list_year = range(2010, 2018)
list_month = range(1, 13)

# read in the shape files
grid_fp = r"./Shapes/subs1.shp"
grid = gpd.read_file(grid_fp)
grid['x'] = grid.apply(utils.getPolyCoords, geom='geometry', coord_type='x', axis=1)
grid['y'] = grid.apply(utils.getPolyCoords, geom='geometry', coord_type='y', axis=1)
monitor_fp = r"./Shapes/monitoring_points1.shp"
monitor = gpd.read_file(monitor_fp)
monitor['x'] = monitor.apply(utils.getPointCoords, geom='geometry', coord_type='x', axis=1)
monitor['y'] = monitor.apply(utils.getPointCoords, geom='geometry', coord_type='y', axis=1)
river_fp = r"./Shapes/riv1.shp"
river = gpd.read_file(river_fp)
river['x'] = river.apply(utils.getLineCoords, geom='geometry', coord_type='x', axis=1)
river['y'] = river.apply(utils.getLineCoords, geom='geometry', coord_type='y', axis=1)
monitor_df = monitor.drop('geometry', axis=1).copy()
river_df = river.drop('geometry', axis=1).copy()


# Read subbasin data from sqlite3
def sql_query(selected_category, selected_year, selected_month):
    if selected_category == "Total N2":
        con = lite.connect(r'./database/N2data.db')
    else:
        return None
    selected_year = int(selected_year)
    selected_month = int(selected_month)
    if selected_month == 12:
        if selected_year == list_year[-1]: return None
        else:
            selected_year += 1
            selected_month = 1
    with con:
        query = '''
            SELECT
              *
            FROM Sub_Mon
            WHERE
              timestamp >= ? AND timestamp < ?
        '''
        data = pd.read_sql_query(query, con, params=(str(selected_year)+'-{0:0=2d}'.format(selected_month)+'-01',
                                                     str(selected_year)+'-{0:0=2d}'.format(selected_month+1)+'-01'))
    return data


# Create the main plot
def create_figure(selected_category, selected_year, selected_month):
    data = sql_query(selected_category, selected_year, selected_month)
    data = data.set_index('sub_num',drop=True)
    plot_df = grid.join(data, on='Subbasin',how='left')
    plot_df = plot_df.drop('geometry', axis=1)

    # Create the color mapper
    low = float(math.floor(data['TN'].min()/100) * 100)
    high = float(math.ceil(data['TN'].max()/100) * 100)
    color_mapper = LinearColorMapper(palette='RdYlGn10', low=low, high=high)
    hover = HoverTool(
        tooltips=[
            ("Subbasin", "$index"),
            ("TN", "@TN{int}"),
        ],
        names=['grid']
    )
    p = figure(title="{0} map for {1}-{2}".format(selected_category, calendar.month_name[int(selected_month)], selected_year),
               plot_width=800, match_aspect=True)
    p.add_tools(hover)
    gsource = ColumnDataSource(plot_df)
    monitor_source = ColumnDataSource(monitor_df)
    river_source = ColumnDataSource(river_df)
    # Plot grid
    p.patches('x', 'y', source=gsource,
              fill_color={'field': 'TN', 'transform': color_mapper},
              fill_alpha=1.0, line_color="black", line_width=0.05, name='grid')
    p.multi_line('x', 'y', source=river_source, color="blue", line_width=1, legend_label='river')
    p.circle('x', 'y', size=5, source=monitor_source, color="red", legend_label='monitor location')
    p.axis.visible = False
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.legend.location = "top_right"
    p.legend.click_policy = "hide"
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, border_line_color=None, location=(0, 0),
                         ticker=SingleIntervalTicker(interval=(high-low)/10))
    p.add_layout(color_bar, 'right')
    return p


# Index page
@app.route('/')
def index():
    # Determine the selected feature
    selected_category = request.args.get("category")
    selected_year = request.args.get("year")
    selected_month = request.args.get("month")
    if selected_category is None:
        selected_category = "Total N2"
    if selected_year is None:
        selected_year = 2010
    if selected_month is None:
        selected_month = 1

    # Create the plot
    plot = create_figure(selected_category, selected_year, selected_month)
    # Embed plot into HTML via Flask Render
    script, div = components(plot)

    return render_template("index.html", script=script, div=div,
                           selected_category=selected_category, selected_year=selected_year,
                           selected_month=selected_month, list_cat=list_cat, list_month=list_month, list_year=list_year)


# With debug=True, Flask server will auto-reload
# when there are code changes
if __name__ == '__main__':
    app.run(port=5000, debug=True)