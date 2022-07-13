# -*- coding: utf-8 -*-
# env/osm3D_vc-env
#########################
# code to create LoD1 3D City Model from volunteered public data (OpenStreetMap) with elevation via a raster DEM.

# author: arkriger - July 2022
# github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel

# script credit:
#    - building height from osm building:level: https://github.com/ualsg/hdb3d-code/blob/master/hdb2d.py - Filip Biljecki <filip@nus.edu.sg>
#    - polygon to lines without duplicate edges: https://gis.stackexchange.com/questions/236903/converting-polygon-to-lines-without-duplicate-edges
#    - gdal raster query: https://gis.stackexchange.com/questions/269603/extract-raster-values-from-point-using-gdal
#    - geopandas snap routine: https://gis.stackexchange.com/questions/290092/how-to-do-snapping-in-geopandas
#    - extruder: https://github.com/cityjson/misc-example-code/blob/master/extruder/extruder.py - Hugo Ledoux <h.ledoux@tudelft.nl>
#    - .obj with material: https://cjio.readthedocs.io/en/latest/_modules/cjio/cityjson.html#CityJSON.export2obj

#additional thanks:
#    - OpenStreetMap help: https://help.openstreetmap.org/users/19716/arkriger
#    - cityjson community: https://github.com/cityjson
#########################
import os
from itertools import chain

import requests
import overpass
import osm2geojson

import numpy as np
import pandas as pd
import geopandas as gpd

import shapely
import shapely.geometry as sg
from shapely.geometry import Point, LineString, Polygon, shape, mapping
from shapely.ops import snap
from shapely.ops import transform

import fiona
import copy
import json
import geojson

import pyproj

from openlocationcode import openlocationcode as olc

from cjio import cityjson

from osgeo import gdal, ogr

import pyvista as pv
import triangle as tr

import matplotlib.pyplot as plt

import time
from datetime import timedelta

def requestOsmBld(jparams):
    """
    request osm for building footprints
    """  
    query = """
    [out:json][timeout:25];
    (area[name='{0}'] ->.b;
    // -- target area ~ can be way or relation
    {1}(area.b)[name='{2}'];
    map_to_area -> .a;
        // I want all buildings ~ with levels tagged
        way['building'](area.a);
        // and relation type=multipolygon ~ to removed courtyards from buildings
        relation['building']["type"="multipolygon"](area.a);
    );
    out body;
    >;
    out skel qt;
    """.format(jparams['LargeArea'], jparams['osm_type'], jparams['FocusArea'])
    
    url = "http://overpass-api.de/api/interpreter"
    r = requests.get(url, params={'data': query})
    #rr = r.read()
    #gj = osm2geojson.json2geojson(r.json())
    shapes_with_props = osm2geojson.json2shapes(r.json())
    
    #-- store the data as GeoJSON
    #with open(jparams['ori-gjson_out'], 'w') as outfile:
        #json.dump(gj, outfile)
        
    ts = gpd.GeoDataFrame(shapes_with_props, crs="EPSG:4326").set_geometry('shape')
    ts.to_crs(crs=jparams['crs'], inplace=True)
    ts.rename_geometry('geometry', inplace=True)
    ts['type'] = ts['properties'].apply(lambda x: x.get('type'))
    ts['tags'] = ts['properties'].apply(lambda x: x.get('tags'))
    ts['id'] = ts['properties'].apply(lambda x: x.get('id'))
    ts['bld'] = ts['tags'].apply(lambda x: x.get('building'))

    return ts
        
def projVec(outfile, infile, crs):
    """
    gdal.VectorTranslate
    """
    ds = gdal.VectorTranslate(outfile, infile, 
                          format = 'GeoJSON', reproject = True, makeValid=True,
                          srcSRS='EPSG:4326', dstSRS=crs)
    # de-reference and close dataset
    del ds

def requestOsmAoi(jparams):
    """
    request osm area
    """
    query = """
    [out:json][timeout:30];
    area[name='{0}']->.a;
    //gather results
    (
    // query part for: “university”
    {1}['name'='{2}'](area.a);
    );
    //print results
    out body;
    >;
    out skel qt;
    """.format(jparams['LargeArea'], jparams['osm_type'], jparams['FocusArea'])
    
    url = "http://overpass-api.de/api/interpreter"
    r = requests.get(url, params={'data': query})
    #area = osm2geojson.json2geojson(r.json())
    area = osm2geojson.json2shapes(r.json())
    #-- store the data as GeoJSON
    #with open(jparams['aoi'], 'w') as outfile:
        #json.dump(area, outfile)
    
    aoi = gpd.GeoDataFrame(area, crs="EPSG:4326").set_geometry('shape')
    aoi.to_crs(crs=jparams['crs'], inplace=True)
    aoi['type'] = aoi['properties'].apply(lambda x: x.get('type'))
    aoi['tags'] = aoi['properties'].apply(lambda x: x.get('tags'))
    aoi['id'] = aoi['properties'].apply(lambda x: x.get('id'))
    aoi.rename_geometry('geometry', inplace=True)
    aoi = aoi.explode()
    aoi.reset_index(drop=True, inplace=True)
        
    return aoi

def requestOsmRoads(jparams):
    """
    request osm roads
    """
    query = """
    [out:json][timeout:25];
    (area[name='{0}'] ->.b;
    // -- target area ~ can be way or relation
    {1}(area.b)[name='{2}'];
    map_to_area -> .a;
        // I want all roads
        way["highway"][highway!~"^(footway|path)$"](area.a);
    );
    out body;
    >;
    out skel qt;
    """.format(jparams['LargeArea'], jparams['osm_type'], jparams['FocusArea'])
    
    url = "http://overpass-api.de/api/interpreter"
    rd = requests.get(url, params={'data': query})
    #gj_rd = osm2geojson.json2geojson(rd.json())
    rds = osm2geojson.json2shapes(rd.json())
    #-- store the data as GeoJSON
    #with open(jparams['gjson-rd'], 'w') as outfile:
        #json.dump(gj_rd, outfile)
    
    rd = gpd.GeoDataFrame(rds, crs="EPSG:4326").set_geometry('shape')
    rd.to_crs(crs=jparams['crs'], inplace=True)
    rd['type'] = rd['properties'].apply(lambda x: x.get('type'))
    rd['tags'] = rd['properties'].apply(lambda x: x.get('tags'))
    rd['id'] = rd['properties'].apply(lambda x: x.get('id'))
    rd.rename_geometry('geometry', inplace=True)
    #rd = rd.explode()
    rd.reset_index(drop=True, inplace=True)
    
    return rd 

def requestOsmParking(jparams):
    """
    request osm parking_entrance
    """
    query = """
    [out:json][timeout:25];
    (area[name='{0}'] ->.b;
    // -- target area ~ can be way or relation
    {1}(area.b)[name='{2}'];
    map_to_area -> .a;
        // I want all roads
        node["amenity"="parking_entrance"](area.a);
    );
    out body;
    >;
    out skel qt;
    """.format(jparams['LargeArea'], jparams['osm_type'], jparams['FocusArea'])
    
    url = "http://overpass-api.de/api/interpreter"
    pk = requests.get(url, params={'data': query})
    #rr = r.read()
    #gj_pk = osm2geojson.json2geojson(pk.json())
    gj_pk = osm2geojson.json2shapes(pk.json())
    #-- store the data as GeoJSON
    #with open(jparams['gjson-pk'], 'w') as outfile:
        #json.dump(gj_pk, outfile)
        
    pk = gpd.GeoDataFrame(gj_pk, crs="EPSG:4326").set_geometry('shape')
    pk.to_crs(crs=jparams['crs'], inplace=True)
    pk['type'] = pk['properties'].apply(lambda x: x.get('type'))
    pk['tags'] = pk['properties'].apply(lambda x: x.get('tags'))
    pk['id'] = pk['properties'].apply(lambda x: x.get('id'))
    pk.rename_geometry('geometry', inplace=True)
    pk = pk.explode()
    pk.reset_index(drop=True, inplace=True)
        
    return pk

# #https://stackoverflow.com/questions/50916422/python-typeerror-object-of-type-int64-is-not-json-serializable
# def np_encoder(object):
#     if isinstance(object, np.generic):
#         return object.item()

def prepareRoads(jparams, rd, pk, aoi, aoibuffer, gt_forward, rb):
    """
    process street network ---buffer with no overlap, trim back from tunnel, parking_entrance
    and under bridge --- save .geojson
    """
    from shapely.wkt import loads
    import itertools
    from scipy.spatial import Voronoi#, voronoi_plot_2d, Delaunay
    
    def segmentize(geom):
        wkt = geom.wkt  # shapely Polygon to wkt
        geom = ogr.CreateGeometryFromWkt(wkt)  # create ogr geometry
        geom.Segmentize(10)  # densify geometry (@-metre)
        wkt2 = geom.ExportToWkt()  # ogr geometry to wkt
        new = loads(wkt2)  # wkt to shapely Polygon
        return new
    
    ##-- https://stackoverflow.com/questions/33883200/pandas-how-to-fill-nan-none-values-based-on-the-other-columns
    def calc_width(row):
        if np.isnan(row['width']):
            """if nan, calculate the width based on lanes"""
            return row['lanes'] * 2.2
        else:
            return row['width']
    
    def ownbuffer(row):
        return row.geometry.buffer(round(float(row['width']) / 2, 2), cap_style=1)
    
    def ownbuffer02(row):
        return row.geometry.buffer(round(float(row['width']) / 2, 2), cap_style=2)
    
    def ownbuffer03(row):
        return row.geometry.buffer(round(float(row['width']) + 0.25 / 2, 2), cap_style=2)
       
    rd = rd.copy()
    rd.drop(rd.index[rd['type'] == 'node'], inplace = True)
    rd.dropna(subset=['tags'], inplace=True)
    #rd.set_crs(epsg=int(jparams['crs'][-5:]), inplace=True, allow_override=True)
    
    #-- extract values
    rd['lanes'] = rd['tags'].apply(lambda x: x.get('lanes'))
    rd['width'] = rd['tags'].apply(lambda x: x.get('width'))
    rd['name'] = rd['tags'].apply(lambda x: x.get('name'))# if pd.isnull(fillna(np.nan)))
    rd['ref'] = rd['tags'].apply(lambda x: x.get('ref'))
    rd['destination'] = rd['tags'].apply(lambda x: x.get('destination'))
    rd['highway'] = rd['tags'].apply(lambda x: x.get('highway'))
    rd['surface'] = rd['tags'].apply(lambda x: x.get('surface'))
    rd['oneway'] = rd['tags'].apply(lambda x: x.get('oneway'))
    
    rd['tunnel'] = rd['tags'].apply(lambda x: x.get('tunnel'))
    tunnel =  rd[rd['tunnel'].isin(['yes', 'building_passage', 'avalanche_protector'])]
    
    #-- remove pedestrian area + drop lanes with no values + 
    #-- calc width based on lanes when no width + drop width with no values
    rd = rd[rd['geometry'].type != 'Polygon']#) & (rd['lanes'] != np.nan)]
    rd['lanes'] = pd.to_numeric(rd['lanes'])
    rd['lanes'] = rd['lanes'].fillna(0)
    rd['width'] = pd.to_numeric(rd['width'])
    rd['width'] = rd.apply(calc_width, axis=1)
    #rd.dropna(subset=['width'], inplace=True)
    rd = rd[rd['width'] != 0]
    
    #-- get the bridge
    rd['bridge'] = rd['tags'].apply(lambda x: x.get('bridge'))
    rd['bridge_structure'] = rd['tags'].apply(lambda x: x.get('bridge:structure'))
    bridge = rd[rd['bridge'] == 'yes'].copy()
    #rd.drop(rd.index[rd['bridge'] == 'yes'], inplace = True)

    #-- place a vertex every x-metre
    rd['geometry'] = rd['geometry'].apply(segmentize)
    
    #-- find the rd intersections, place a point, buffer and cut from rd network
    inters = []
    for line1, line2 in itertools.combinations(rd.geometry, 2):
        if line1.intersects(line2):
            inter = line1.intersection(line2)
            if "Point" == inter.type:
                inters.append(inter)
            elif "MultiPoint" == inter.type:
                inters.extend([pt for pt in inter])
            elif "MultiLineString" == inter.type:
                multiLine = [line for line in inter]
                first_coords = multiLine[0].coords[0]
                last_coords = multiLine[len(multiLine)-1].coords[1]
                inters.append(Point(first_coords[0], first_coords[1]))
                inters.append(Point(last_coords[0], last_coords[1]))
            elif "GeometryCollection" == inter.type:
                for geom in inter:
                    if "Point" == geom.type:
                        inters.append(geom)
                    elif "MultiPoint" == geom.type:
                        inters.extend([pt for pt in geom])
                    elif "MultiLineString" == geom.type:
                        multiLine = [line for line in geom]
                        first_coords = multiLine[0].coords[0]
                        last_coords = multiLine[len(multiLine)-1].coords[1]
                        inters.append(Point(first_coords[0], first_coords[1]))
                        inters.append(Point(last_coords[0], last_coords[1]))
                        
    pnts = gpd.GeoDataFrame(crs=jparams['crs'], geometry=inters)
    p_buffer = pnts.buffer(2)
    p_buffer = gpd.GeoDataFrame(crs=jparams['crs'], geometry=p_buffer)
    
    rd_e = gpd.overlay(rd, p_buffer, how='difference')
    rd_e = rd_e.explode()
    rd_e.reset_index(drop=True, inplace=True)
    
    #-- Voronoi of all rd vertices without the intersections above + aoi 
    pt = [line.__geo_interface__['coordinates'] for line in rd_e.geometry]
    pt_array = np.array(np.concatenate(pt))
    
    po = [i for i in aoibuffer.geometry]
    x,y = po[0].exterior.coords.xy
    po = np.dstack((x,y))
    po_array = np.array(np.concatenate(po))
    pt_array = np.concatenate((pt_array, po_array), axis=0)
    
    vor = Voronoi(pt_array)
    lines = [shapely.geometry.LineString(vor.vertices[line]) for line in vor.ridge_vertices if -1 not in line]
    polys = shapely.ops.polygonize(lines)
    vo = gpd.GeoDataFrame(geometry=gpd.GeoSeries(polys), crs=jparams['crs'])
    
    # transfer the rd attributes to the voronoi
    join = gpd.sjoin(vo, rd_e, how="left", op="intersects")
    
    #-- buffer the original rd network and trim the voronoi to its extent
    rd_b = rd.copy()
    rd_b['geometry'] = rd_b.apply(ownbuffer, axis=1)
    rd_b = rd_b.dissolve()
    #rd_b = gpd.GeoDataFrame(geometry=gpd.GeoSeries([geom for geom in rd_b.unary_union.geoms]), crs=jparams['crs'])
    rd_b = rd_b.explode()
    
    #-- buffer the tunnel features and cut from the roads
    t_buffer = tunnel.buffer(0.5, cap_style=2)
    t_buffer = gpd.GeoDataFrame(crs=jparams['crs'], geometry=t_buffer)
    rd_b = gpd.overlay(rd_b, t_buffer, how='difference')
    rd_b = rd_b.explode()
    
    #-- buffer the parking entrance and cut from roads   
    pk = pk.copy()
    pk = pk[pk['geometry'].type == 'Point']
    pk.dropna(subset=['tags'], inplace=True)
    pk['entrance'] = pk['tags'].apply(lambda x: x.get('amenity'))
    pk =  pk[pk['entrance'].isin(['parking_entrance'])]
    pk_buffer = pk.buffer(2.4, cap_style=3)
    pk_buffer = pk_buffer.geometry.rotate(45)                           ### --- I don't know why???
    pk_buffer = gpd.GeoDataFrame(crs=jparams['crs'], geometry=pk_buffer)
    rd_b = gpd.overlay(rd_b, pk_buffer, how='difference')
    
    #-- remove bridges and trim back roads under bridges 
    #bridge_b = bridge.copy()
    bridge_b02 = bridge.copy()
    #bridge_b['geometry'] = bridge_b.apply(ownbuffer02, axis=1)
    bridge_b02['geometry'] = bridge_b02.apply(ownbuffer03, axis=1)
    bridge_b02 = bridge_b02.dissolve()
    rd_b = gpd.overlay(rd_b, bridge_b02, how='difference')
    rd_b = rd_b.explode()
    
    #-- trim the roads to the aoi
    rd_b = gpd.clip(rd_b, aoi)
    one = gpd.clip(join, rd_b)
    one.set_crs(epsg=int(jparams['crs'][-5:]), inplace=True, allow_override=True)
    
    #-- bridges and tunnels
    one.drop(one.index[one['bridge'] == 'yes'], inplace = True)
    one.drop(one.index[one['tunnel'].isin(['yes', 'building_passage', 'avalanche_protector'])], inplace = True) #rd[rd['tunnel'].isin(['yes', 'building_passage'])]

    #-- groupby and dissolve -> we do this so that similar features (road segments) join together
    one = one.dissolve(by=['name', 'highway', 'surface', 'oneway', 'width', 'ref', 'destination'], 
                       as_index=False, dropna=False)
    one = one.explode()
    one.reset_index(drop=True, inplace=True)
       
    #-- account for null/None values
    one.dropna(subset=['geometry'], inplace=True)
    one.loc[one["id"].isnull(), "id"] = (one["id"].isnull().cumsum()).astype(float) #"Other" + 
    one.loc[one["tags"].isnull(), "tags"] = [{'processing': 'ExtraFeature'}]
    one.reset_index(drop=True, inplace=True)
    
    one['x'] = one.geometry.representative_point().x
    one['y'] = one.geometry.representative_point().y
    one['ground_height'] = one.apply(lambda row: rasterQuery2(row.x, row.y, gt_forward, rb), axis = 1)

    roads = {
        "type": "FeatureCollection",
        "features": []
        }
    count = 1000000
    for i, row in one.iterrows():
        f = {
        "type" : "Feature"
        }
        f["properties"] = {}
                
        #-- store all OSM attributes and prefix them with osm_ 
        f["properties"]["id"] = count #row.id
        f["properties"]["osm_id"] = row.id
        for p in row.tags:
            f["properties"]["osm_%s" % p] = row.tags[p]
    
        roads['features'].append(f)
        count += 1
    #-- store the data as GeoJSON
    with open(jparams['osm_roads'], 'w') as outfile:
        json.dump(roads, outfile)#, default=np_encoder)
    
    hsr = one[['x', 'y', 'ground_height']].copy()
    
    return one, hsr 
    
def prepareDEM(extent, jparams):
    """
    gdal.Warp to reproject and clip raster dem
    """
    OutTile = gdal.Warp(jparams['projClip_raster'], 
                        jparams['in_raster'], 
                        dstSRS=jparams['crs'],
                        srcNodata = jparams['nodata'],
                        #dstNodata = 60,
                         #-- outputBounds=[minX, minY, maxX, maxY]
                        outputBounds = [extent[0], extent[1],
                                        extent[2], extent[3]])
    OutTile = None 
      
def createXYZ(fout, fin):
    """
    read raster and extract an xyz
    """
    xyz = gdal.Translate(fout,
                         fin,
                         format = 'XYZ')
    xyz = None
    
def rasterQuery(geom, gt_forward, rb):
    
    mx = geom.representative_point().x
    my = geom.representative_point().y
    
    px = int((mx - gt_forward[0]) / gt_forward[1])
    py = int((my - gt_forward[3]) / gt_forward[5])

    intval = rb.ReadAsArray(px, py, 1, 1)
    
    return intval[0][0]

def assignZ(ts, gt_forward, rb): # rfname,
    """
    assign a height attribute - mean ground - to the osm vector 
    ~ .representative_point() used instead of .centroid
    """
    ts.drop(ts.index[ts['type'] == 'node'], inplace = True)

    #-- skywalk --bridge
    skywalk = ts[ts['bld'] == 'bridge'].copy()
    ts.drop(ts.index[ts['bld'] == 'bridge'], inplace = True)
    if len(skywalk) > 0:
        skywalk['mean'] = skywalk.apply(lambda row: rasterQuery(row.geometry, gt_forward, rb), axis = 1)
    
    #-- building=roof
    roof = ts[ts['bld'] == 'roof'].copy()
    ts.drop(ts.index[ts['bld'] == 'roof'], inplace = True)
    if len(roof) > 0:
        roof['mean'] = roof.apply(lambda row: rasterQuery(row.geometry, gt_forward, rb), axis = 1)
    
    ts['mean'] = ts.apply(lambda row : rasterQuery(row.geometry, gt_forward, rb), axis = 1)
        
    return ts, skywalk, roof
    
def writegjson(ts, jparams):#, fname):
    """
    read the building gpd and create new attributes in osm vector
    ~ ground height, relative building height and roof height.
    write the result to .geojson
    """
    #-- take care of non-Polygon LineString's 
    for i, row in ts.iterrows():
        if row.geometry.type == 'LineString' and len(row.geometry.coords) < 3:
            ts = ts.drop(ts.index[i])
    
    storeyheight = 2.8
    #-- iterate through the list of buildings and create GeoJSON features rich in attributes
    footprints = {
        "type": "FeatureCollection",
        "features": []
        }
    
    for i, row in ts.iterrows():
        f = {
        "type" : "Feature"
        }
        #-- at a minimum we only want building:levels tagged
        if row['type'] != 'node' and row['tags'] != None and 'building:levels' in row['tags']:
    
            f["properties"] = {}
            
            #-- store all OSM attributes and prefix them with osm_ 
            f["properties"]["osm_id"] = row.id
            for p in row.tags:
                adr = []
                #-- transform the OSM address to string prefix with osm_
                if 'addr:flats'in row.tags:
                    adr.append(row.tags['addr:flats'])
                if 'addr:housenumber'in row.tags:
                    adr.append(row.tags['addr:housenumber'])
                if 'addr:housename'in row.tags:
                    adr.append(row.tags['addr:housename'])
                if 'addr:street' in row.tags:
                    adr.append(row.tags['addr:street'])
                if 'addr:suburb' in row.tags:
                    adr.append(row.tags['addr:suburb'])
                if 'addr:postcode' in row.tags:
                    adr.append(row.tags['addr:postcode'])
                if 'addr:city' in row.tags:
                    adr.append(row.tags['addr:city'])
                if 'addr:province' in row.tags:
                    adr.append(row.tags['addr:province'])
                #-- store other OSM attributes and prefix them with osm_
                f["properties"]["osm_%s" % p] = row.tags[p]
                
            f["properties"]["osm_address"] = " ".join(adr)
            
            osm_shape = shape(row["geometry"])
            #-- a few buildings are not polygons, rather linestrings. This converts them to polygons
            #-- rare, but if not done it breaks the code later
            if osm_shape.type == 'LineString':
                osm_shape = Polygon(osm_shape)
            #-- and multipolygons must be accounted for
            elif osm_shape.type == 'MultiPolygon':
                #osm_shape = Polygon(osm_shape[0])
                for poly in osm_shape.geoms:
                    osm_shape = Polygon(poly)#[0])
                    #-- convert the shapely object to geojson
            
            #-- google plus_code
            wgs84 = pyproj.CRS('EPSG:4326')
            utm = pyproj.CRS(jparams['crs'])
            p = osm_shape.representative_point()
            project = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform
            wgs_point = transform(project, p)
            f["properties"]["plus_code"] = olc.encode(wgs_point.y, wgs_point.x, 11)
                
            f["geometry"] = mapping(osm_shape)
               
            f["properties"]['ground_height'] = round(row["mean"], 2)
            #print('id: ', f["properties"]["osm_id"], row.tags['building:levels'])
            f["properties"]['building_height'] = round(float(row.tags['building:levels']) * storeyheight + 1.3, 2) 
            f["properties"]['roof_height'] = round(f["properties"]['building_height'] + row["mean"], 2)
            footprints['features'].append(f)
            
    for value in footprints['features']:
        if 'osm_addr:flats' in value["properties"]:
            del value["properties"]["osm_addr:flats"]
        if 'osm_addr:housenumber' in value["properties"]:
            del value["properties"]["osm_addr:housenumber"]
        if 'osm_addr:housename' in value["properties"]:
            del value["properties"]["osm_addr:housename"]
        if 'osm_addr:street' in value["properties"]:
            del value["properties"]["osm_addr:street"]
        if 'osm_addr:suburb' in value["properties"]:
            del value["properties"]["osm_addr:suburb"]
        if 'osm_addr:postcode' in value["properties"]:
            del value["properties"]["osm_addr:postcode"]
        if 'osm_addr:city' in value["properties"]:
            del value["properties"]["osm_addr:city"]
        if 'osm_addr:province' in value["properties"]:
            del value["properties"]["osm_addr:province"]
                
    #-- store the data as GeoJSON
    with open(jparams['osm_bldings'], 'w') as outfile:
        json.dump(footprints, outfile)

def prep_Skygjson(skywalk, jparams):#, fname):
    """
    read the skywalk gpd and prepare and return the .geojson - create new attributes in osm vector
    ~ ground height, relative building min_height and roof/max height.
    """
    # take care of non-Polygon LineString's 
    for i, row in skywalk.iterrows():
        if row.geometry.type == 'LineString' and len(row.geometry.coords) < 3:
            skywalk = skywalk.drop(skywalk.index[i])
    
    storeyheight = 2.8
    #-- iterate through the list of buildings and create GeoJSON features rich in attributes
    skyprints = {
        "type": "FeatureCollection",
        "features": []
        }
    
    for i, row in skywalk.iterrows():
        f = {
        "type" : "Feature"
        }
            
        f["properties"] = {}
            
        #-- store all OSM attributes and prefix them with osm_ 
        f["properties"]["osm_id"] = row.id
        for p in row.tags:
                #-- store other OSM attributes and prefix them with osm_
            f["properties"]["osm_%s" % p] = row.tags[p]
            
        osm_shape = shape(row["geometry"])
        #-- a few buildings are not polygons, rather linestrings. This converts them to polygons
        #-- rare, but if not done it breaks the code later
        if osm_shape.type == 'LineString':
            osm_shape = Polygon(osm_shape)
        #-- and multipolygons must be accounted for
        elif osm_shape.type == 'MultiPolygon':
            #osm_shape = Polygon(osm_shape[0])
            for poly in osm_shape.geoms:
                osm_shape = Polygon(poly)#[0])
                
        f["geometry"] = mapping(osm_shape)

        f["properties"]['ground_height'] = round(row["mean"], 2)
        if row.tags['min_height'] != None:
            f["properties"]['min_height'] = round((float(row.tags['min_height'])) + row["mean"], 2)
        else:
            f["properties"]['min_height'] = round((float(row.tags['building:min_level']) * storeyheight) + row["mean"], 2)
            
        f["properties"]['building_height'] = round(float(row.tags['building:levels']) * storeyheight, 2)
        f["properties"]['max_height'] = round(f["properties"]['building_height'] + row["mean"], 2)
        skyprints['features'].append(f)
                     
    #-- store the data as GeoJSON
    #with open(jparams['SKYwalk_gjson-z_out'], 'w') as outfile:
        #json.dump(skyprints, outfile)
    return skyprints
        
def prep_roof(roof, jparams):#, fname):
    """
    read the roof gpd; prepare and return the .geojson - create new attributes in osm vector
    ~ *roof_height.
    """
    storeyheight = 2.8
    #-- iterate and create GeoJSON features
    _roof = {
        "type": "FeatureCollection",
        "features": []
    }
    for i, row in roof.iterrows():
        f = {
        "type" : "Feature"
        }
        if 'building:levels' in row['tags']:

            f["properties"] = {}
                    
            #-- store all OSM attributes and prefix them with osm_ 
            f["properties"]["osm_id"] = row.id
            for p in row.tags:
                f["properties"]["osm_%s" % p] = row.tags[p]
                    
            osm_shape = shape(row["geometry"])
            #-- a few buildings are not polygons, rather linestrings. This converts them to polygons
            #-- rare, but if not done it breaks the code later
            if osm_shape.type == 'LineString':
                osm_shape = Polygon(osm_shape)
            #-- and multipolygons must be accounted for
            elif osm_shape.type == 'MultiPolygon':
                #osm_shape = Polygon(osm_shape[0])
                for poly in osm_shape.geoms:
                    osm_shape = Polygon(poly)#[0])
                        
            f["geometry"] = mapping(osm_shape)
                    
            f["properties"]['ground_height'] = round(row["mean"], 2)
            f["properties"]['bottom_roof_height'] = round(float(row.tags['building:levels']) * storeyheight + row["mean"], 2) 
            f["properties"]['top_roof_height'] = round(f["properties"]['bottom_roof_height'] + 1, 2)
            _roof['features'].append(f)
        
    #-- store the data as GeoJSON
    #with open(jparams['roof_gjson-z_out'], 'w') as outfile:
        #json.dump(_roof, outfile)
        
    return _roof

def getXYZ(dis, aoi, jparams):
    """
    read xyz to gdf
    """
    df = pd.read_csv(jparams['xyz'], 
                     delimiter = ' ', header=None,
                     names=["x", "y", "z"])
    
    geometry = [Point(xy) for xy in zip(df.x, df.y)]
    #df = df.drop(['Lon', 'Lat'], axis=1)
    gdf = gpd.GeoDataFrame(df, crs=jparams['crs'], geometry=geometry)
    
    _symdiff = gpd.overlay(aoi, dis, how='symmetric_difference')
    _mask = gdf.within(_symdiff.loc[0, 'geometry'])
    gdf = gdf.loc[_mask]
    gdf = gdf[gdf['z'] != jparams['nodata']]
    gdf = gdf.round(2)
    gdf.reset_index(drop=True, inplace=True)
    
    return gdf

def getosmBld(jparams):
    """
    read osm buildings to gdf, extract the representative_point() for each polygon
    and create a basic xyz_df;
    """
    dis = gpd.read_file(jparams['osm_bldings'])
    dis.set_crs(epsg=int(jparams['crs'][-5:]), inplace=True, allow_override=True)
    
    ##-- lets keep this for now
    ##--  remove duplicate vertices within tolerance 0.2 
    for index, row in dis.iterrows():
        tmp_gdf = dis.copy()
        tmp_gdf['distance'] = tmp_gdf.distance(row['geometry'])
        closest_geom = list(tmp_gdf.sort_values('distance')['geometry'])[1]
        # I took 1 because index 0 would be the row itself
        snapped_geom = snap(row['geometry'], closest_geom, 0.2)
        dis.loc[index, 'geometry'] = snapped_geom
    
     ##-- the following is left for reference
     ##-- this serves two functions:
     #               i)  verify footprints removed
     #               ii) remove `outline` that overwrite `building:parts` 
     #                   - how does https://3dbuildings.com/data/#17.59/-33.932156/18.638025/131.2/60
     #                   - and https://demo.f4map.com/#lat=-33.9319930&lon=18.6386228&zoom=19&camera.theta=69.973&camera.phi=-126.624
     #                   - display the form correctly?      
     #dis = dis.loc[(dis.osm_id != 13076003) & (dis.osm_id != 12405081)] 
     ##-- save
     #dis.to_file(jparams['gjson-z_out'], driver='GeoJSON')
    
    # create a point representing the hole within each building  
    dis['x'] = dis.representative_point().x
    dis['y'] = dis.representative_point().y
    hs = dis[['x', 'y', 'ground_height']].copy()
    
    return dis, hs

def getosmArea(aoi, outFile, b_type, crs):
    """
    read osm area to gdf and buffer
    - get the extent for the cityjson
    """
    
    # when areas are relations
    if b_type == 'relation' and len(aoi) > 1:
        for i, row in aoi.iterrows():
            if row.tags != None and 'place' in row.tags:
                focus = row
            
        trim = pd.DataFrame(focus)
        trim = trim.T
        aoi = gpd.GeoDataFrame(trim, geometry = trim['geometry'])
        aoi = aoi.set_crs(crs)
                        
    aoibuffer = gpd.GeoDataFrame(aoi, geometry = aoi.geometry)
    aoibuffer['geometry'] = aoi.buffer(150, cap_style = 3, join_style = 2)
    
    extent = [aoibuffer.total_bounds[0] - 250, aoibuffer.total_bounds[1] - 250, 
              aoibuffer.total_bounds[2] + 250, aoibuffer.total_bounds[3] + 250]
    
    #-- store the data as GeoJSON
    aoi.to_file(outFile, driver="GeoJSON")
    
    return aoi, aoibuffer, extent

def getBldVertices(dis, gt_forward, rb): #
    """
    retrieve vertices from building footprints ~ without duplicates 
    - these vertices already have a z attribute
    """
    all_coords = []
    dps = 2
    segs = {}
    min_zbld = []
    
    for ids, row in dis.iterrows():
        
        oring = list(row.geometry.exterior.coords)
        coords_rounded = []
        zbld = []
        for x, y in oring:
            z = rasterQuery2(x, y, gt_forward, rb)
            rounded_x = round(x, dps)
            rounded_y = round(y, dps)
            rounded_z = round(z, dps)
            zbld.append(rounded_z)
            coords_rounded.append((rounded_x, rounded_y, rounded_z))
            all_coords.append([rounded_x, rounded_y, rounded_z]) 
            
        min_zbld.append(float(min(zbld)))  ##-- the min height of the blding.
        
        for i in range(0, len(coords_rounded)-1):
            
            x1, y1, z1 = coords_rounded[i]
            x2, y2, z2 = coords_rounded[i+1]
            # deduplicate lines which overlap but go in different directions
            if (x1 < x2):
                key = (x1, y1, x2, y2)
            else:
                if (x1 == x2):
                    if (y1 < y2):
                        key = (x1, y1, x2, y2)
                    else:
                        key = (x2, y2, x1, y1)
                else:
                    key = (x2, y2, x1, y1)
            if key not in segs:
                segs[key] = 1
            else:
                segs[key] += 1
         ##-- if polygon has interior (ground in couryard)                
        for interior in row.geometry.interiors:
            oring, z = list(interior.coords), row['ground_height']
            rounded_z = round(z, dps)
            coords_rounded = []
            #po = []
            for x, y in oring:
                rounded_x = round(x, dps)
                rounded_y = round(y, dps)
                coords_rounded.append((rounded_x, rounded_y, rounded_z))
                all_coords.append([rounded_x, rounded_y, rounded_z])

            for i in range(0, len(coords_rounded)-1):
                x1, y1, z1 = coords_rounded[i]
                x2, y2, z2 = coords_rounded[i+1]
                # deduplicate lines which overlap but go in different directions
                if (x1 < x2):
                    key = (x1, y1, x2, y2)
                else:
                    if (x1 == x2):
                        if (y1 < y2):
                            key = (x1, y1, x2, y2)
                        else:
                            key = (x2, y2, x1, y1)
                    else:
                         key = (x2, y2, x1, y1)
                if key not in segs:
                    segs[key] = 1
                else:
                    segs[key] += 1
    
    c = pd.DataFrame.from_dict(segs, orient="index").reset_index()
    c.rename(columns={'index':'coords'}, inplace=True)
    
    ac = pd.DataFrame(all_coords, columns=['x', 'y', 'z'])
    ac = ac.sort_values(by = 'z', ascending=False)
    ac.drop_duplicates(subset=['x','y'], keep= 'first', inplace=True)
    ac = ac.reset_index(drop=True)
        
    return ac, c, min_zbld

def getRdVertices(one, idx01, acoi, hs, gt_forward, rb):
    r_coords = []
    r_coords02 = []
    dps = 2
    segs = {}
    segs02 = {}
    #geoms = {}
    
    idx1 = []
    arr = []
    acoi_copy = acoi.copy()
    l1 = len(acoi_copy)
    Ahsr = pd.DataFrame(columns=['x', 'y', 'ground_height']) #[]
    temp_Ahsr = pd.DataFrame(columns=['x', 'y', 'ground_height']) #[]
    t_list = []
    rd_pts = []
    idxAll = []
    
    #count = 0
    for ids, row in one.iterrows():
       
        oring = list(row.geometry.exterior.coords)
        coords_rounded = []
        #po = []
        for x, y in oring:
            z = rasterQuery2(x, y, gt_forward, rb)
 
            rounded_x = round(x, dps)
            rounded_y = round(y, dps)
            rounded_z = round(z, dps)
            coords_rounded.append((rounded_x, rounded_y, rounded_z))
            r_coords.append([rounded_x, rounded_y, rounded_z])
            r_coords02.append([rounded_x, rounded_y, rounded_z])
            
        for i in range(0, len(coords_rounded)-1):
            x1, y1, z1 = coords_rounded[i]
            x2, y2, z2 = coords_rounded[i+1]
            # deduplicate lines which overlap but go in different directions
            if (x1 < x2):
                key = (x1, y1, x2, y2)
            else:
                if (x1 == x2):
                    if (y1 < y2):
                        key = (x1, y1, x2, y2)
                    else:
                        key = (x2, y2, x1, y1)
                else:
                    key = (x2, y2, x1, y1)
            if key not in segs:
                segs[key] = 1
            else:
                segs[key] += 1
            if key not in segs02:
                segs02[key] = 1
            else:
                segs02[key] += 1
         
        arr01 = hs[['x', 'y']].round(3).values.tolist()        
        ##-- if polygon has interior (circular roads with 'islands')   
        g = row.geometry.interiors
        for i, interior in enumerate(g):

            if interior != None:
                x, y = interior.centroid.xy

                arr.append([x[0], y[0], row['ground_height']])
                ho = Ahsr.append(pd.DataFrame(arr, columns=['x', 'y', 'ground_height']))
                temp_Ahsr = hs.append(ho)
                arr = temp_Ahsr[['x', 'y']].round(3).values.tolist()

            coords_rounded = []
            for pair in list(interior.coords):
                x = pair[0]
                y = pair[1]
                z = rasterQuery2(x, y, gt_forward, rb)
                rounded_x = round(x, dps)
                rounded_y = round(y, dps)
                rounded_z = round(z, dps)
                coords_rounded.append((rounded_x, rounded_y, rounded_z))
                r_coords.append([rounded_x, rounded_y, rounded_z])
                r_coords02.append([rounded_x, rounded_y, rounded_z])
                
            for i in range(0, len(coords_rounded)-1):
                x1, y1, z1 = coords_rounded[i]
                x2, y2, z2 = coords_rounded[i+1]
               #-- deduplicate lines which overlap but go in different directions
                if (x1 < x2):
                    key = (x1, y1, x2, y2)
                else:
                    if (x1 == x2):
                        if (y1 < y2):
                            key = (x1, y1, x2, y2)
                        else:
                            key = (x2, y2, x1, y1)
                    else:
                        key = (x2, y2, x1, y1)
                if key not in segs:
                    segs[key] = 1
                else:
                    segs[key] += 1
                if key not in segs02:
                    segs02[key] = 1
                else:
                    segs02[key] += 1
                    
        
        crx = pd.DataFrame.from_dict(segs02, orient="index").reset_index()
        crx.rename(columns={'index':'coords'}, inplace=True)
        
        acrx = pd.DataFrame(r_coords02, columns=['x', 'y', 'z'])
        acrx = acrx.sort_values(by = 'z', ascending=False)
        acrx.drop_duplicates(subset=['x','y'], keep= 'first', inplace=True)
        acrx = acrx.reset_index(drop=True)
        
        acoi_copy = acoi_copy.append(acrx, ignore_index=True)
        r_pts = acoi_copy[['x', 'y', 'z']].values
        rd_pts.append(r_pts)
        pts = acoi_copy[['x', 'y']].values
    
        for i, row in crx.iterrows():
            frx, fry = row.coords[0], row.coords[1]
            tox, toy = row.coords[2], row.coords[3]
            [index_f] = (acrx[(acrx['x'] == frx) & (acrx['y'] == fry)].index.values)
            [index_t] = (acrx[(acrx['x'] == tox) & (acrx['y'] == toy)].index.values)
            idx1.append([l1 + index_f, l1 + index_t])
        idxAll.append(idx1)
        
        if len(arr) >= 1:
            A = dict(vertices=pts, segments=idx1, holes=arr)
        else:
            A = dict(vertices=pts, segments=idx1, holes=arr01)
        Tr = tr.triangulate(A, 'pVV')  # the VV will print stats in the cmd
        time.sleep(3)
        t = Tr.get('triangles').tolist()
        t_list.append(t)
        
        arr = [] 
        segs02 = {}
        r_coords02 = []
        idx1 = []
        acoi_copy = acoi.copy()
                                      
    cr = pd.DataFrame.from_dict(segs, orient="index").reset_index()
    cr.rename(columns={'index':'coords'}, inplace=True)
        
    acr = pd.DataFrame(r_coords, columns=['x', 'y', 'z'])
    acr = acr.sort_values(by = 'z', ascending=False)
    acr.drop_duplicates(subset=['x','y'], keep= 'first', inplace=True)
    acr = acr.reset_index(drop=True)
    
    return t_list, rd_pts, acr, cr
    

def rasterQuery2(mx, my, gt_forward, rb):
    
    px = int((mx - gt_forward[0]) / gt_forward[1])
    py = int((my - gt_forward[3]) / gt_forward[5])

    intval = rb.ReadAsArray(px, py, 1, 1)

    return intval[0][0]

def getAOIVertices(aoi, gt_forward, rb): 
    """
    retrieve vertices from aoi ~ without duplicates 
    - these vertices are assigned a z attribute
    """
    aoi_coords = []
    dps = 2
    segs = {}
    
    for ids, row in aoi.iterrows():
        oring = list(row.geometry.exterior.coords)
       
        coords_rounded = []
        #po = []
        for x, y in oring:
            #[z] = point_query(Point(x, y), raster=fname)#, interpolate='nearest', nodata=0)
            z = rasterQuery2(x, y, gt_forward, rb)
    
            rounded_x = round(x, dps)
            rounded_y = round(y, dps)
            rounded_z = round(z, dps)
            coords_rounded.append((rounded_x, rounded_y, rounded_z))
            aoi_coords.append([rounded_x, rounded_y, rounded_z])

        for i in range(0, len(coords_rounded)-1):
                    x1, y1, z1 = coords_rounded[i]
                    x2, y2, z2 = coords_rounded[i+1]
                    # deduplicate lines which overlap but go in different directions
                    if (x1 < x2):
                        key = (x1, y1, x2, y2)
                    else:
                        if (x1 == x2):
                            if (y1 < y2):
                                key = (x1, y1, x2, y2)
                            else:
                                key = (x2, y2, x1, y1)
                        else:
                            key = (x2, y2, x1, y1)
                    if key not in segs:
                        segs[key] = 1
                    else:
                        segs[key] += 1
                        
    ca = pd.DataFrame.from_dict(segs, orient="index").reset_index()
    ca.rename(columns={'index':'coords'}, inplace=True)
    
    acoi = pd.DataFrame(aoi_coords, columns=['x', 'y', 'z'])
  
    acoi = acoi.sort_values(by = 'z', ascending=False)
    acoi.drop_duplicates(subset=['x','y'], keep= 'first', inplace=True)
    acoi = acoi.reset_index(drop=True)
    
    return acoi, ca

def appendCoords(gdf, ac):
    df2 = gdf.append(ac, ignore_index=True)
    
    return df2

def createSgmts(ac, c, gdf, idx):
    """
    create a segment list for Triangle
    - indices of vertices [from, to]
    """
    
    l = len(gdf) #- 1
    lr = 0
    idx01 = []
    
    for i, row in c.iterrows():
        frx, fry = row.coords[0], row.coords[1]
        tox, toy = row.coords[2], row.coords[3]

        [index_f] = (ac[(ac['x'] == frx) & (ac['y'] == fry)].index.values)
        [index_t] = (ac[(ac['x'] == tox) & (ac['y'] == toy)].index.values)
        idx.append([l + index_f, l + index_t])
        idx01.append([lr + index_f, lr + index_t])
    
    return idx, idx01

def executeDelaunay(hs, df4, idx):
    """
    perform Triangle ~ constrained Delaunay with concavitities removed
    - return the simplices: indices of vertices that create the triangles
    """      
    holes = hs[['x', 'y']].round(3).values.tolist()
    pts = df4[['x', 'y']].values #, 'z']].values
        
    A = dict(vertices=pts, segments=idx, holes=holes)
    Tr = tr.triangulate(A, 'pVV')  # the VV will print stats in the cmd
    t = Tr.get('triangles').tolist()
    
     #-- matplotlib for basic 2D plot
    #plt.figure(figsize=(8, 8))
    #ax = plt.subplot(111, aspect='equal')
    #tr.plot(ax, **Tr)
    #plt.show()
      
    return t
    
def pvPlot(t, pv_pts, idx, hs):
    """
    3D plot with PyVista
    """
    l = np.vstack(idx)
    l = l.reshape([-1, 2])
    twos = np.array([[2]] * len(idx))
    lines = np.append(twos, l, axis=1)
    
    trin = pv.PolyData(pv_pts)
    polygon2 = pv.PolyData(pv_pts)
    holes = pv.PolyData()
    # Make sure it has the same points as the mesh being triangulated
    trin.points = pv_pts
    holes = hs[['x', 'y', 'ground_height']].values
    
    faces = np.insert(t, 0, np.full((1, len(t)), 3), axis=1)
    trin.faces = faces
    polygon2.lines = lines
    
    p = pv.Plotter(window_size=[750, 450], notebook=False)#, off_screen=True)
    p.add_mesh(trin, show_edges=True, color="blue", opacity=0.2)
    p.add_mesh(polygon2, color="black", opacity=0.3)#, render_points_as_spheres=True)
    p.add_mesh(holes, color="red")
    
    p.set_background('white')
    p.show()
    
def writeObj(pts, dt, obj_filename):
    """
    basic function to produce wavefront.obj
    """
    f_out = open(obj_filename, 'w')
    for p in pts:
        f_out.write("v {:.2f} {:.2f} {:.2f}\n".format(p[0], p[1], p[2]))

    for simplex in dt:
        f_out.write("f {} {} {}\n".format(simplex[0] + 1, simplex[1] + 1, 
                                          simplex[2] + 1))
    f_out.close()

def output_cityjsonR(extent, minz, maxz, T, pts, t_list, rd_pts, jparams, min_zbld, skywalk, roof, acoi):
    """
    basic function to produce LoD1 City Model
    - buildings and terrain
    """
     ##- open buildings ---fiona object
    c = fiona.open(jparams['osm_bldings'])
    lsgeom = [] #-- list of the geometries
    lsattributes = [] #-- list of the attributes
    for each in c:
        lsgeom.append(shape(each['geometry'])) #-- geom are casted to Fiona's 
        lsattributes.append(each['properties'])
    
    ##- open roads ---fiona object
    rd = fiona.open(jparams['osm_roads'])
    #rdgeom = [] #-- list of the geometries
    rdattributes = [] #-- list of the attributes
    for each in rd:
        #lsgeom.append(shape(each['geometry'])) #-- geom are casted to Fiona's 
        rdattributes.append(each['properties'])
          
    ##- open skywalk ---fiona object
    if len(skywalk) > 1: #['features']
        #sky = fiona.open(jparams['SKYwalk_gjson-z_out'])
        skywgeom = [] #-- list of the geometries
        skywgeomattributes = [] #-- list of the attributes
        #for each in sky:
        for (s, each) in enumerate(skywalk['features']):
            skywgeom.append(shape(each['geometry'])) #-- geom are casted to Fiona's 
            skywgeomattributes.append(each['properties'])
    else:
        skywgeom = None
        skywgeomattributes = None
           
    if len(roof) > 1: #['features']
        roofgeom = [] #-- list of the geometries
        roofgeomattributes = [] #-- list of the attributes
        #for each in _roof:
        for (s, each) in enumerate(roof['features']):
            roofgeom.append(shape(each['geometry'])) #-- geom are casted to Fiona's 
            roofgeomattributes.append(each['properties'])
    else:
        roofgeom = None
        roofgeomattributes = None
        
    cm = doVcBndGeomRd(lsgeom, lsattributes, rdattributes, t_list, rd_pts, extent, minz, maxz, 
                       T, pts, 
                       acoi, jparams, min_zbld, 
                       skywgeom, skywgeomattributes,  
                       roofgeom, roofgeomattributes)   
    
    json_str = json.dumps(cm, indent=2)
    fout = open(jparams['cjsn_out'], "w")
    fout.write(json_str)  
    ##-- close fiona object
    c.close() 

    ##-- clean cityjson
    cm = cityjson.load(jparams['cjsn_out'])
    cityjson.save(cm, jparams['cjsn_CleanOut'])
    
def output_cityjson(extent, minz, maxz, T, pts, jparams, min_zbld, skywalk, roof):
    """
    basic function to produce LoD1 City Model
    - buildings and terrain
    """
     ##- open building ---fiona object
    c = fiona.open(jparams['osm_bldings'])
    lsgeom = [] #-- list of the geometries
    lsattributes = [] #-- list of the attributes
    for each in c:
        lsgeom.append(shape(each['geometry'])) #-- geom are cast to Fiona's 
        lsattributes.append(each['properties'])
        
    ##- open skywalk ---fiona object
    if len(skywalk) > 1:
        skywgeom = [] #-- list of the geometries
        skywgeomattributes = [] #-- list of the attributes
        #for each in sky:
        for (s, each) in enumerate(skywalk['features']):
            skywgeom.append(shape(each['geometry'])) #-- geom are casted to Fiona's 
            skywgeomattributes.append(each['properties'])
    else:
        skywgeom = None
        skywgeomattributes = None
           
    if len(roof) > 1:
        roofgeom = [] #-- list of the geometries
        roofgeomattributes = [] #-- list of the attributes
        #for each in _roof:
        for (s, each) in enumerate(roof['features']):
            roofgeom.append(shape(each['geometry'])) #-- geom are casted to Fiona's 
            roofgeomattributes.append(each['properties'])
    else:
        roofgeom = None
        roofgeomattributes = None
        
    cm = doVcBndGeom(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams, min_zbld, 
                     skywgeom, skywgeomattributes, 
                     roofgeom, roofgeomattributes)
    
    json_str = json.dumps(cm, indent=2)
    fout = open(jparams['cjsn_out'], "w")
    fout.write(json_str)  
    ##- close fiona object
    c.close() 
    
    ##--clean cityjson
    cm = cityjson.load(jparams['cjsn_out'])
    #cm.remove_duplicate_vertices()
    cityjson.save(cm, jparams['cjsn_CleanOut'])

def doVcBndGeom(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams, min_zbld, 
                skywgeom=None, skywgeomattributes=None, 
                roofgeom=None, roofgeomattributes=None): 
    
    #-- create the JSON data structure for the City Model
    cm = {}
    cm["type"] = "CityJSON"
    cm["version"] = "1.1"
    # cm["transform"] = {
    #     "scale": [0.001, 0.001, 0.001],
    #     "translate": [extent[0], extent[0], minz]
    #     },
    cm["CityObjects"] = {}
    cm["vertices"] = []
    
    ##-- Metadata is added manually
    cm["metadata"] = {
    "title": jparams['cjsn_title'],
    "referenceDate": jparams['cjsn_referenceDate'],
    "referenceSystem": jparams['cjsn_referenceSystem'],
    "geographicalExtent": [
        extent[0],
        extent[1],
        minz ,
        extent[1],
        extent[1],
        maxz
      ],
    "datasetPointOfContact": {
        "contactName": jparams['cjsn_contactName'],
        "emailAddress": jparams['cjsn_emailAddress'],
        "contactType": jparams['cjsn_contactType'],
        "website": jparams['cjsn_website']
        },
    "+metadata-extended": {
        "lineage":
            [{"featureIDs": ["TINRelief"],
             "source": [
                 {
                     "description": jparams['cjsn_+meta-description'],
                     "sourceSpatialResolution": jparams['cjsn_+meta-sourceSpatialResolution'],
                     "sourceReferenceSystem": jparams['cjsn_+meta-sourceReferenceSystem'],
                     "sourceCitation":jparams['cjsn_+meta-sourceCitation'],
                     }],
             "processStep": {
                 "description" : "Processing of raster DEM using osm_LoD1_3DCityModel workflow",
                 "processor": {
                     "contactName": jparams['cjsn_contactName'],
                     "contactType": jparams['cjsn_contactType'],
                     "website": "https://github.com/AdrianKriger/osm_LoD1_3DCityModel"
                     }
                 }
            },
            {"featureIDs": ["Building"],
             "source": [
                 {
                     "description": "OpenStreetMap contributors",
                     "sourceReferenceSystem": "urn:ogc:def:crs:EPSG:4326",
                     "sourceCitation": "https://www.openstreetmap.org",
                 }],
             "processStep": {
                 "description" : "Processing of building vector contributions using osm_LoD1_3DCityModel workflow",
                 "processor": {
                     "contactName": jparams['cjsn_contactName'],
                     "contactType": jparams['cjsn_contactType'],
                     "website": "https://github.com/AdrianKriger/osm_LoD1_3DCityModel"
                     }
                 }
            }]
        }
    },
        
    ##-- do terrain
    add_terrain_v(pts, cm)
    grd = {}
    grd['type'] = 'TINRelief'
    grd['geometry'] = [] #-- a cityobject can have >1 
      #-- the geometry
    g = {} 
    g['type'] = 'CompositeSurface'
    g['lod'] = 1
    allsurfaces = [] #-- list of surfaces
    add_terrain_b(T, allsurfaces)
    g['boundaries'] = allsurfaces
    #-- add the geom 
    grd['geometry'].append(g)
    #-- insert the terrain as one new city object
    cm['CityObjects']['terrain01'] = grd
    
    ##-- then buildings
    for (i, geom) in enumerate(lsgeom):
        footprint = geom
        #-- one building
        oneb = {}
        oneb['type'] = 'Building'
        oneb['attributes'] = {}
        for k, v in list(lsattributes[i].items()):
            if v is None:
                del lsattributes[i][k]
            #oneb['attributes'][k] = lsattributes[i][k]
        for a in lsattributes[i]:
            oneb['attributes'][a] = lsattributes[i][a]
        
        oneb['geometry'] = [] #-- a cityobject can have > 1
        #-- the geometry
        g = {} 
        g['type'] = 'Solid'
        g['lod'] = 1
        allsurfaces = [] #-- list of surfaces forming the oshell of the solid
        #-- exterior ring of each footprint
        oring = list(footprint.exterior.coords)
        oring.pop() #-- remove last point since first==last
        if footprint.exterior.is_ccw == False:
            #-- to get proper orientation of the normals
            oring.reverse() 
        extrude_walls(oring, lsattributes[i]['roof_height'], min_zbld[i], allsurfaces, cm)
        #-- interior rings of each footprint
        irings = []
        interiors = list(footprint.interiors)
        for each in interiors:
            iring = list(each.coords)
            iring.pop() #-- remove last point since first==last
            if each.is_ccw == True:
                #-- to get proper orientation of the normals
                iring.reverse() 
            irings.append(iring)
            extrude_walls(iring, lsattributes[i]['roof_height'], min_zbld[i], allsurfaces, cm)
        #-- top-bottom surfaces
        extrude_roof_ground(oring, irings, lsattributes[i]['roof_height'], False, allsurfaces, cm)
        extrude_roof_ground(oring, irings, min_zbld[i], True, allsurfaces, cm)
        #-- add the extruded surfaces to the geometry
        g['boundaries'] = []
        g['boundaries'].append(allsurfaces)
        #g['boundaries'] = allsurfaces
        #-- add the geom to the building 
        oneb['geometry'].append(g)
        #-- insert the building as one new city object
        cm['CityObjects'][lsattributes[i]['osm_id']] = oneb
        
    #-- then sykwalk
    if skywgeom != None:
        for (i, geom) in enumerate(skywgeom):
            skyprint = geom
            #-- one skywalk
            oneb = {}
            oneb['type'] = 'Bridge'
            oneb['attributes'] = {}
            for k, v in list(skywgeomattributes[i].items()):
                if v is None:
                    del skywgeomattributes[i][k]
            for a in skywgeomattributes[i]:
                oneb['attributes'][a] = skywgeomattributes[i][a]
            
            oneb['geometry'] = [] #-- a cityobject can have > 1
            #-- the geometry
            g = {} 
            g['type'] = 'Solid'
            g['lod'] = 1
            allsurfaces = [] #-- list of surfaces forming the oshell of the solid
            #-- exterior ring of each footprint
            oring = list(skyprint.exterior.coords)
            oring.pop() #-- remove last point since first==last
            if skyprint.exterior.is_ccw == False:
                #-- to get proper orientation of the normals
                oring.reverse() 
            extrude_walls(oring, skywgeomattributes[i]['max_height'], skywgeomattributes[i]['min_height'],
                          allsurfaces, cm)
            #-- interior rings of each footprint
            irings = []
            interiors = list(skyprint.interiors)
            for each in interiors:
                iring = list(each.coords)
                iring.pop() #-- remove last point since first==last
                if each.is_ccw == True:
                    #-- to get proper orientation of the normals
                    iring.reverse() 
                irings.append(iring)
                extrude_walls(iring, skywgeomattributes[i]['max_height'], skywgeomattributes[i]['min_height'],
                              allsurfaces, cm)
            #-- top-bottom surfaces
            extrude_roof_ground(oring, irings, skywgeomattributes[i]['max_height'], 
                                False, allsurfaces, cm)
            extrude_roof_ground(oring, irings, skywgeomattributes[i]['min_height'], 
                                True, allsurfaces, cm)
            #-- add the extruded geometry to the geometry
            g['boundaries'] = []
            g['boundaries'].append(allsurfaces)
            #g['boundaries'] = allsurfaces
            #-- add the geom to the building 
            oneb['geometry'].append(g)
            #-- insert the building as one new city object
            cm['CityObjects'][skywgeomattributes[i]['osm_id']] = oneb
            
    #-- then roof
    if roofgeom != None:
        for (i, geom) in enumerate(roofgeom):
            roofprint = geom
        #-- one building=roof
            oneb = {}
            oneb['type'] = 'Building'
            oneb['attributes'] = {}
            for k, v in list(roofgeomattributes[i].items()):
                if v is None:
                    del roofgeomattributes[i][k]
            for a in roofgeomattributes[i]:
                oneb['attributes'][a] = roofgeomattributes[i][a]
        
            oneb['geometry'] = [] #-- a cityobject can have > 1
            #-- the geometry
            g = {} 
            g['type'] = 'Solid'
            g['lod'] = 1
            allsurfaces = [] #-- list of surfaces forming the oshell of the solid
            #-- exterior ring of each footprint
            oring = list(roofprint.exterior.coords)
            oring.pop() #-- remove last point since first==last
            if roofprint.exterior.is_ccw == False:
                #-- to get proper orientation of the normals
                oring.reverse() 
            extrude_walls(oring, roofgeomattributes[i]['top_roof_height'], 
                          roofgeomattributes[i]['bottom_roof_height'],
                          allsurfaces, cm)
            #-- interior rings of each footprint
            irings = []
            interiors = list(roofprint.interiors)
            for each in interiors:
                iring = list(each.coords)
                iring.pop() #-- remove last point since first==last
                if each.is_ccw == True:
                    #-- to get proper orientation of the normals
                    iring.reverse() 
                irings.append(iring)
                extrude_walls(iring, roofgeomattributes[i]['top_roof_height'], 
                              roofgeomattributes[i]['bottom_roof_height'],
                              allsurfaces, cm)
            #-- top-bottom surfaces
            extrude_roof_ground(oring, irings, roofgeomattributes[i]['top_roof_height'], 
                                False, allsurfaces, cm)
            extrude_roof_ground(oring, irings, roofgeomattributes[i]['bottom_roof_height'], 
                                True, allsurfaces, cm)
            #-- add the extruded geometry to the geometry
            g['boundaries'] = []
            g['boundaries'].append(allsurfaces)
            #g['boundaries'] = allsurfaces
            #-- add the geom to the building 
            oneb['geometry'].append(g)
            #-- insert the building as one new city object
            cm['CityObjects'][roofgeomattributes[i]['osm_id']] = oneb

    return cm

def add_terrain_v(pts, cm):
    #cm['vertices'] = pts
    for p in pts:
        cm['vertices'].append([p[0], p[1], p[2]])
    
def add_terrain_b(T, allsurfaces):
    for i in T:
        allsurfaces.append([[i[0], i[1], i[2]]]) 
    
def extrude_roof_ground(orng, irngs, height, reverse, allsurfaces, cm):#, mat):
    oring = copy.deepcopy(orng)
    irings = copy.deepcopy(irngs)
    if reverse == True:
        oring.reverse()
        for each in irings:
            each.reverse()
    for (i, pt) in enumerate(oring):
        cm['vertices'].append([pt[0], pt[1], height])
        oring[i] = (len(cm['vertices']) - 1)
    for (i, iring) in enumerate(irings):
        for (j, pt) in enumerate(iring):
            cm['vertices'].append([pt[0], pt[1], height])
            irings[i][j] = (len(cm['vertices']) - 1)
    output = []
    output.append(oring)     
    for each in irings:
        output.append(each)
    allsurfaces.append(output)

def extrude_walls(ring, height, ground, allsurfaces, cm):#, mat):
    #-- each edge become a wall, ie a rectangle
    for (j, v) in enumerate(ring[:-1]):
        #l = []
        cm['vertices'].append([ring[j][0],   ring[j][1],   ground])
        cm['vertices'].append([ring[j+1][0], ring[j+1][1], ground])
        cm['vertices'].append([ring[j+1][0], ring[j+1][1], height])
        cm['vertices'].append([ring[j][0],   ring[j][1],   height])
        t = len(cm['vertices'])
        allsurfaces.append([[t-4, t-3, t-2, t-1]])  
        
    #-- last-first edge
    #l = []
    cm['vertices'].append([ring[-1][0], ring[-1][1], ground])
    cm['vertices'].append([ring[0][0],  ring[0][1],  ground])
    cm['vertices'].append([ring[0][0],  ring[0][1],  height])
    cm['vertices'].append([ring[-1][0], ring[-1][1], height])
    t = len(cm['vertices'])
    allsurfaces.append([[t-4, t-3, t-2, t-1]])

def doVcBndGeomRd(lsgeom, lsattributes, rdattributes, t_list, rd_pts, extent, minz, maxz, 
                  T, pts, 
                  acoi, jparams, min_zbld,
                  skywgeom=None, skywgeomattributes=None, 
                  roofgeom=None, roofgeomattributes=None): 
    
    #-- create the JSON data structure for the City Model
    cm = {}
    cm["type"] = "CityJSON"
    cm["version"] = "1.1"
    #cm["transform"] = {
    #    "scale": [0.0, 0.0, 0.0],
    #    "translate": [1.0, 1.0, 1.0]
    #},
    cm["CityObjects"] = {}
    cm["vertices"] = []
    #-- Metadata is added manually
    cm["metadata"] = {
    "title": jparams['cjsn_title'],
    "referenceDate": jparams['cjsn_referenceDate'],
    "referenceSystem": jparams['cjsn_referenceSystem'],
    "geographicalExtent": [
        extent[0],
        extent[1],
        minz ,
        extent[1],
        extent[1],
        maxz
      ],
    "datasetPointOfContact": {
        "contactName": jparams['cjsn_contactName'],
        "emailAddress": jparams['cjsn_emailAddress'],
        "contactType": jparams['cjsn_contactType'],
        "website": jparams['cjsn_website']
        },
    "+metadata-extended": {
        "lineage":
            [{"featureIDs": ["TINRelief"],
             "source": [
                 {
                     "description": jparams['cjsn_+meta-description'],
                     "sourceSpatialResolution": jparams['cjsn_+meta-sourceSpatialResolution'],
                     "sourceReferenceSystem": jparams['cjsn_+meta-sourceReferenceSystem'],
                     "sourceCitation":jparams['cjsn_+meta-sourceCitation'],
                     }],
             "processStep": {
                 "description" : "Processing of raster DEM using osm_LoD1_3DCityModel workflow",
                 "processor": {
                     "contactName": jparams['cjsn_contactName'],
                     "contactType": jparams['cjsn_contactType'],
                     "website": "https://github.com/AdrianKriger/osm_LoD1_3DCityModel"
                     }
                 }
            },
            {"featureIDs": ["Building", "Road"],
             "source": [
                 {
                     "description": "OpenStreetMap contributors",
                     "sourceReferenceSystem": "urn:ogc:def:crs:EPSG:4326",
                     "sourceCitation": "https://www.openstreetmap.org",
                 }],
             "processStep": {
                 "description" : "Processing of vector contributions using osm_LoD1_3DCityModel workflow",
                 "processor": {
                     "contactName": jparams['cjsn_contactName'],
                     "contactType": jparams['cjsn_contactType'],
                     "website": "https://github.com/AdrianKriger/osm_LoD1_3DCityModel"
                     }
                 }
            }]
        }
    }
    ##-- do terrain
    add_terrain_v(pts, cm)
    grd = {}
    grd['type'] = 'TINRelief'
    grd['geometry'] = [] #-- a cityobject can have >1 
    #-- the geometry
    g = {} 
    g['type'] = 'CompositeSurface'
    g['lod'] = 1
    g['boundaries'] = []
    allsurfaces = [] #-- list of surfaces
    add_terrain_b(T, allsurfaces)
    g['boundaries'] = allsurfaces
    #print(g['boundaries'])
    #g['boundaries'].append(allsurfaces)
    #-- add the geom 
    grd['geometry'].append(g)
    #-- insert the terrain as one new city object
    cm['CityObjects']['terrain01'] = grd
    
    ##-- do roads
    for i, (rp, tinR) in enumerate(zip(rd_pts, t_list)):
        rp = rp[len(acoi):, :]
        add_rd_v(rp, cm)
        onerd = {}
        onerd['type'] = 'Road'
        onerd['geometry'] = [] #-- a cityobject can have >1 
        #-- the geometry
        g = {} 
        g['type'] = 'MultiSurface'
        g['lod'] = 1    

        g['boundaries'] = []
        allsurfaces = [] #-- list of surfaces
        add_rd_b(tinR, rp, acoi, allsurfaces, cm)
        onerd['attributes'] = {}
        for k, v in list(rdattributes[i].items()):
            if v is None:
                del rdattributes[i][k]
        for a in rdattributes[i]:
            onerd['attributes'][a] = rdattributes[i][a]
            
        g['boundaries'] = allsurfaces
        #g['boundaries'].append(allsurfaces)
        #-- add the geom 
        onerd['geometry'].append(g)
        #onerd['geometry'] = g
        #-- insert one road as one new city object
        cm['CityObjects'][rdattributes[i]['id']] = onerd
    
    ##-- then buildings
    for (i, geom) in enumerate(lsgeom):
        footprint = geom
        #-- one building
        oneb = {}
        oneb['type'] = 'Building'
        oneb['attributes'] = {}
        for k, v in list(lsattributes[i].items()):
            if v is None:
                del lsattributes[i][k]
        for a in lsattributes[i]:
            oneb['attributes'][a] = lsattributes[i][a]
        
        oneb['geometry'] = [] #-- a cityobject can have > 1
        #-- the geometry
        g = {} 
        g['type'] = 'Solid'
        g['lod'] = 1
        allsurfaces = [] #-- list of surfaces forming the oshell of the solid
        #-- exterior ring of each footprint
        oring = list(footprint.exterior.coords)
        oring.pop() #-- remove last point since first==last
        if footprint.exterior.is_ccw == False:
            #-- to get proper orientation of the normals
            oring.reverse() 
        extrude_walls(oring, lsattributes[i]['roof_height'], min_zbld[i], allsurfaces, cm)
        #-- interior rings of each footprint
        irings = []
        interiors = list(footprint.interiors)
        for each in interiors:
            iring = list(each.coords)
            iring.pop() #-- remove last point since first==last
            if each.is_ccw == True:
                #-- to get proper orientation of the normals
                iring.reverse() 
            irings.append(iring)
            extrude_walls(iring, lsattributes[i]['roof_height'], min_zbld[i], allsurfaces, cm)
        #-- top-bottom surfaces
        extrude_roof_ground(oring, irings, lsattributes[i]['roof_height'], False, allsurfaces, cm)
        extrude_roof_ground(oring, irings, min_zbld[i], True, allsurfaces, cm)
        #-- add the extruded geometry to the geometry
        g['boundaries'] = []
        g['boundaries'].append(allsurfaces)
        #g['boundaries'] = allsurfaces
        #-- add the geom to the building 
        oneb['geometry'].append(g)
        #-- insert the building as one new city object
        cm['CityObjects'][lsattributes[i]['osm_id']] = oneb
           
    ##-- then sykwalk
    if skywgeom != None:
        for (i, geom) in enumerate(skywgeom):
            skyprint = geom
            #-- one skywalk
            oneb = {}
            oneb['type'] = 'Bridge'
            oneb['attributes'] = {}
            for k, v in list(skywgeomattributes[i].items()):
                if v is None:
                    del skywgeomattributes[i][k]
            #oneb['attributes'][k] = lsattributes[i][k]
            for a in skywgeomattributes[i]:
                oneb['attributes'][a] = skywgeomattributes[i][a]
        
            oneb['geometry'] = [] #-- a cityobject can have > 1
            #-- the geometry
            g = {} 
            g['type'] = 'Solid'
            g['lod'] = 1
            allsurfaces = [] #-- list of surfaces forming the oshell of the solid
            #-- exterior ring of each footprint
            oring = list(skyprint.exterior.coords)
            oring.pop() #-- remove last point since first==last
            if skyprint.exterior.is_ccw == False:
            #-- to get proper orientation of the normals
                oring.reverse() 
            extrude_walls(oring, skywgeomattributes[i]['max_height'], skywgeomattributes[i]['min_height'],
                          allsurfaces, cm)
            #-- interior rings of each footprint
            irings = []
            interiors = list(skyprint.interiors)
            for each in interiors:
                iring = list(each.coords)
                iring.pop() #-- remove last point since first==last
                if each.is_ccw == True:
                #-- to get proper orientation of the normals
                    iring.reverse() 
                irings.append(iring)
                extrude_walls(iring, skywgeomattributes[i]['max_height'], skywgeomattributes[i]['min_height'],
                              allsurfaces, cm)
                #-- top-bottom surfaces
            extrude_roof_ground(oring, irings, skywgeomattributes[i]['max_height'], 
                                False, allsurfaces, cm)
            extrude_roof_ground(oring, irings, skywgeomattributes[i]['min_height'], 
                                True, allsurfaces, cm)
            #-- add the extruded geometry to the geometry
            g['boundaries'] = []
            g['boundaries'].append(allsurfaces)
            #g['boundaries'] = allsurfaces
            #-- add the geom to the building 
            oneb['geometry'].append(g)
            #-- insert the building as one new city object
            cm['CityObjects'][skywgeomattributes[i]['osm_id']] = oneb

    #-- then roof
    if roofgeom != None:
        for (i, geom) in enumerate(roofgeom):
            roofprint = geom
            #-- one building=roof
            oneb = {}
            oneb['type'] = 'Building'
            oneb['attributes'] = {}
            for k, v in list(roofgeomattributes[i].items()):
                if v is None:
                    del roofgeomattributes[i][k]
            #oneb['attributes'][k] = lsattributes[i][k]
            for a in roofgeomattributes[i]:
                oneb['attributes'][a] = roofgeomattributes[i][a]
        
            oneb['geometry'] = [] #-- a cityobject can have > 1
            #-- the geometry
            g = {} 
            g['type'] = 'Solid'
            g['lod'] = 1
            allsurfaces = [] #-- list of surfaces forming the oshell of the solid
            #-- exterior ring of each footprint
            oring = list(roofprint.exterior.coords)
            oring.pop() #-- remove last point since first==last
            if roofprint.exterior.is_ccw == False:
            #-- to get proper orientation of the normals
                oring.reverse() 
            extrude_walls(oring, roofgeomattributes[i]['top_roof_height'], 
                          roofgeomattributes[i]['bottom_roof_height'],
                          allsurfaces, cm)
            #-- interior rings of each footprint
            irings = []
            interiors = list(roofprint.interiors)
            for each in interiors:
                iring = list(each.coords)
                iring.pop() #-- remove last point since first==last
                if each.is_ccw == True:
                #-- to get proper orientation of the normals
                    iring.reverse() 
                irings.append(iring)
                extrude_walls(iring, roofgeomattributes[i]['top_roof_height'], 
                              roofgeomattributes[i]['bottom_roof_height'],
                              allsurfaces, cm)
                #-- top-bottom surfaces
            extrude_roof_ground(oring, irings, roofgeomattributes[i]['top_roof_height'], 
                                False, allsurfaces, cm)
            extrude_roof_ground(oring, irings, roofgeomattributes[i]['bottom_roof_height'], 
                                True, allsurfaces, cm)
            #-- add the extruded geometry to the geometry
            g['boundaries'] = []
            g['boundaries'].append(allsurfaces)
            #g['boundaries'] = allsurfaces
            #-- add the geom to the structure 
            oneb['geometry'].append(g)
            #-- insert the building as one new city object
            cm['CityObjects'][roofgeomattributes[i]['osm_id']] = oneb

    return cm
       
def add_rd_v(pts, cm):
    for p in pts:
        cm['vertices'].append([p[0], p[1], p[2]])

def add_rd_b(T, r, acoi, allsurfaces, cm):
    for i in T:
        allsurfaces.append([[i[0]+len(cm['vertices'])-len(r)-len(acoi), 
                             i[1]+len(cm['vertices'])-len(r)-len(acoi), 
                             i[2]+len(cm['vertices'])-len(r)-len(acoi)]])
        

def OwnXpt2obj(self):
    from io import StringIO
    
    self.decompress()
    out = StringIO()
    #-- reference .mlt
    out.write('mtllib osm_LoD1_3DCityModel.mtl\n')
    #-- write vertices
    for v in self.j['vertices']:
        out.write('v ' + str(v[0]) + ' ' + str(v[1]) + ' ' + str(v[2]) + '\n')
    vnp = np.array(self.j["vertices"])
    #-- translate to minx,miny
    minx = 9e9
    miny = 9e9
    for each in vnp:
        if each[0] < minx:
                minx = each[0]
        if each[1] < miny:
                miny = each[1]
    for each in vnp:
        each[0] -= minx
        each[1] -= miny
    # print ("min", minx, miny)
    # print(vnp)
    #-- start with the CO
    for theid in self.j['CityObjects']:
        for geom in self.j['CityObjects'][theid]['geometry']:
            if (self.j['CityObjects'][theid]['type'] == 'TINRelief'):
                out.write('usemtl Terrain\n')
            if (self.j['CityObjects'][theid]['type'] == 'Building'):
                out.write('usemtl Building\n')
            if (self.j['CityObjects'][theid]['type'] == 'Road'):
                out.write('usemtl Road\n')
            if (self.j['CityObjects'][theid]['type'] == 'Bridge'):
                out.write('usemtl Bridge\n')
            
            out.write('o ' + str(theid) + '\n')
            if ( (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface') ):
                for face in geom['boundaries']:
                    #re, b, n = self.triangulate_face(face, vnp)
                    re, b = self.triangulate_face(face, vnp)
                    if b == True:
                        for t in re:
                            out.write("f %d %d %d\n" % (t[0] + 1, t[1] + 1, t[2] + 1))
            elif (geom['type'] == 'Solid'):
                for shell in geom['boundaries']:
                    for i, face in enumerate(shell):
                        #re, b, n = self.triangulate_face(face, vnp)
                        re, b = self.triangulate_face(face, vnp)
                        if b == True:
                            for t in re:
                                out.write("f %d %d %d\n" % (t[0] + 1, t[1] + 1, t[2] + 1))
    return out
    
def write275obj(jparams):
    """
    export 2.75D wavefront.obj surface
    """
    cm1 = cityjson.load(jparams['cjsn_CleanOut'])
    with open(jparams['obj-2_75D'], 'w+') as f:
        re = OwnXpt2obj(cm1)
        f.write(re.getvalue())
    
