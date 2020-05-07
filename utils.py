import geopandas as gpd
import pysal as ps


def getPolyCoords(row, geom, coord_type):
    """Returns the coordinates ('x' or 'y') of edges of a Polygon exterior"""

    # Parse the exterior of the coordinate
    try:
        exterior = row[geom].exterior
        if coord_type == 'x':
        # Get the x coordinates of the exterior
            return list( exterior.coords.xy[0] )
        elif coord_type == 'y':
        # Get the y coordinates of the exterior
            return list( exterior.coords.xy[1] )
    except:
        result_list = []
        for shape in row[geom]:
            exterior = shape.exterior
            if coord_type == 'x':
                result_list += list( exterior.coords.xy[0] )
            elif coord_type == 'y':
                result_list += list( exterior.coords.xy[1] )
        return result_list

def getPointCoords(row, geom, coord_type):
    """Calculates coordinates ('x' or 'y') of a Point geometry"""
    if coord_type == 'x':
        return row[geom].x
    elif coord_type == 'y':
        return row[geom].y

def getLineCoords(row, geom, coord_type):
    """Returns a list of coordinates ('x' or 'y') of a LineString geometry"""
    if coord_type == 'x':
        return list( row[geom].coords.xy[0] )
    elif coord_type == 'y':
        return list( row[geom].coords.xy[1] )