# -*- coding: utf-8 -*-
# env/osm3D_vc-env
#########################
# code to create LoD1 3D City Model from volunteered public data (OpenStreetMap) with elevation via a raster DEM.

# author: arkriger - 2023
# github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel

# script credit:
#    - building height from osm building:level: https://github.com/ualsg/hdb3d-code/blob/master/hdb2d.py - Filip Biljecki <filip@nus.edu.sg>
#    - polygon to lines without duplicate edges: https://gis.stackexchange.com/questions/236903/converting-polygon-to-lines-without-duplicate-edges
#    - gdal raster query: https://gis.stackexchange.com/questions/269603/extract-raster-values-from-point-using-gdal
#    - geopandas snap routine: https://gis.stackexchange.com/questions/290092/how-to-do-snapping-in-geopandas
#    - fill Nan: https://stackoverflow.com/questions/33883200/pandas-how-to-fill-nan-none-values-based-on-the-other-columns
#    - extruder: https://github.com/cityjson/misc-example-code/blob/master/extruder/extruder.py - Hugo Ledoux <h.ledoux@tudelft.nl>
#    - .obj with material: https://cjio.readthedocs.io/en/latest/_modules/cjio/cityjson.html#CityJSON.export2obj

# additional thanks:
#    - OpenStreetMap help: https://help.openstreetmap.org/users/19716/arkriger
#    - cityjson community: https://github.com/cityjson
#########################
import os
from itertools import chain

import requests
#import overpass
import osm2geojson

import numpy as np
import pandas as pd
import geopandas as gpd
import topojson as tp

import shapely
from shapely.geometry import shape
#import shapely.geometry as sg
from shapely.geometry import Point, LineString, Polygon, shape, mapping
#from shapely.ops import snap
from shapely.ops import transform

import fiona
import copy
import json
#import geojson

import pyproj

from openlocationcode import openlocationcode as olc

from cjio import cityjson

from osgeo import gdal, ogr

import triangle as tr

import matplotlib.pyplot as plt

#import time
#from datetime import timedelta

import warnings
warnings.filterwarnings('ignore')

def requestOsmBld(jparams):
    """
    request osm for building footprints
    """  
    query = """
    [out:json][timeout:25];
    area[name='{0}'] ->.b;
    // -- target area ~ can be way or relation
    {1}(area.b)[name='{2}'];
    map_to_area -> .a;
        // I want all buildings ~ with levels tagged
        (way['building'](area.a);
        // and relation type=multipolygon ~ to removed courtyards from buildings
        relation['building']["type"="multipolygon"](area.a);
    );
    out geom 2500;
    //out body;
    //>;
    //out skel qt;
    """.format(jparams['LargeArea'], jparams['osm_type'], jparams['FocusArea'])
    
    url = "http://overpass-api.de/api/interpreter"
    r = requests.get(url, params={'data': query})

    shapes_with_props = osm2geojson.json2shapes(r.json())

    geom = [i['shape'] for i in shapes_with_props]
    ts = gpd.GeoDataFrame(shapes_with_props, crs="EPSG:4326", geometry=geom)
    ts.to_crs(crs=jparams['crs'], inplace=True)
    ts.drop('shape', axis=1, inplace=True)
    ts['type'] = ts['properties'].apply(lambda x: x.get('type'))
    ts['tags'] = ts['properties'].apply(lambda x: x.get('tags'))
    ts['id'] = ts['properties'].apply(lambda x: x.get('id'))
    ts['bld'] = ts['tags'].apply(lambda x: x.get('building'))
    
    #-- cull points closer than 0.2 meter while preserving topology
    topo = tp.Topology(ts, prequantize=False)
    ts = topo.toposimplify(0.2).to_gdf()

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
    query ="""[out:json][timeout:30];
        area[boundary=administrative][name='{0}'] -> .a;
        (
        {1}[amenity='university'][name='{2}'](area.a);
        relation[place][place~"sub|town|city|count|state|village|borough|quarter|neighbourhood"][name='{2}'](area.a);
        );
        out geom;
        """.format(jparams['LargeArea'], jparams['osm_type'], jparams['FocusArea'])
    
    url = "http://overpass-api.de/api/interpreter"
    r = requests.get(url, params={'data': query})
    area = osm2geojson.json2shapes(r.json())

    geom = [i['shape'] for i in area]
    aoi = gpd.GeoDataFrame(area, crs="EPSG:4326", geometry=geom)
    aoi.to_crs(crs=jparams['crs'], inplace=True)
    aoi.drop('shape', axis=1, inplace=True)
    aoi['type'] = aoi['properties'].apply(lambda x: x.get('type'))
    aoi['tags'] = aoi['properties'].apply(lambda x: x.get('tags'))
    aoi['id'] = aoi['properties'].apply(lambda x: x.get('id'))
    aoi = aoi.explode()
    aoi.reset_index(drop=True, inplace=True)
        
    return aoi
    
def prepareDEM(extent, jparams):
    """
    gdal.Warp to reproject and clip raster dem
    """
    #ds = gdal.Open(jparams['in_raster'])
    #prj = ds.GetProjection()
    
    gdal.SetConfigOption("GTIFF_SRS_SOURCE", "GEOKEYS")
    
    OutTile = gdal.Warp(jparams['projClip_raster'], 
                        jparams['in_raster'], 
                        #srcSRS=prj,
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
    
def mtPlot02(blds, jparams):
    "highlight crossing rds and blds --topological errors"
    
    blds_copy = blds.copy()

    new_df1 = blds_copy.loc[blds_copy.overlaps(blds_copy.unary_union)].reset_index(drop=True)  
    
    fig, ax = plt.subplots(figsize=(11, 11))
    
    blds.plot(ax=ax, facecolor='none', edgecolor='purple', alpha=0.2)
    if len(new_df1) > 0:
        new_df1.plot(ax=ax, edgecolor='red', facecolor='none')
    
    p = './data/topologyFig.png'
    plt.savefig(p, dpi=300)
    plt.show()
    
    return new_df1
     
def assignZ(ts, gt_forward, rb): 
    """
    assign a height attribute - mean ground - to the osm vector 
    ~ .representative_point() used instead of .centroid
    """
    ts.drop(ts.index[ts['type'] == 'node'], inplace = True)
    
    ts['mean'] = ts.apply(lambda row : rasterQuery(row.geometry, gt_forward, rb), axis = 1)
        
    return ts
    
def writegjson(ts, jparams):
    """
    read the building gpd and create new attributes in osm vector
    ~ ground height, relative building height and roof height.
    write the result to .geojson
    """
    #-- take care of non-Polygon LineString's 
    for i, row in ts.iterrows():
        if row.geometry.geom_type == 'LineString' and len(row.geometry.coords) < 3:
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
                #-- store OSM attributes and prefix them with osm_
                f["properties"]["osm_%s" % p] = row.tags[p]
                #-- we dont want addresses on bridges and rooves
                if row['bld'] != 'bridge' and row['bld'] != 'roof':
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
    
                f["properties"]["osm_address"] = " ".join(adr)
            
            osm_shape = shape(row["geometry"])
            #-- a few buildings are not polygons, rather linestrings. This converts them to polygons
            #-- rare, but if not done it breaks the code later
            if osm_shape.geom_type == 'LineString':
                osm_shape = Polygon(osm_shape)
            #-- and multipolygons must be accounted for
            elif osm_shape.geom_type == 'MultiPolygon':
                polys = list(osm_shape.geoms) 
                for poly in polys:
                    osm_shape = Polygon(poly)#[0])
            
            f["geometry"] = mapping(osm_shape)
            f["properties"]["footprint"] = mapping(osm_shape)
            
            #-- google plus_code
            wgs84 = pyproj.CRS('EPSG:4326')
            utm = pyproj.CRS(jparams['crs'])
            p = osm_shape.representative_point()
            project = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform
            wgs_point = transform(project, p)
            f["properties"]["plus_code"] = olc.encode(wgs_point.y, wgs_point.x, 11)
            
            if row['bld'] == 'bridge':
                f["properties"]['ground_height'] = round(row["mean"], 2)
            #print('id: ', f["properties"]["osm_id"], row.tags['building:levels'])
                if row['tags']['min_height'] != None:
                    f["properties"]['bottom_bridge_height'] = round(float(row.tags['min_height']) + row["mean"], 2)
                else:
                    f["properties"]['bottom_bridge_height'] = round((float(row.tags['building:min_level']) * storeyheight) + row["mean"], 2)
                f["properties"]['building_height'] = round(float(row.tags['building:levels']) * storeyheight, 2)
                f["properties"]['roof_height'] = round(f["properties"]['building_height'] + row["mean"], 2)
            if row['bld'] == 'roof':
                f["properties"]['ground_height'] = round(row["mean"], 2)
                f["properties"]['bottom_roof_height'] = round(float(row.tags['building:levels']) * storeyheight + row["mean"], 2) 
                f["properties"]['roof_height'] = round(f["properties"]['bottom_roof_height'] + 1.5, 2)
            if row['bld'] != 'bridge' and row['bld'] != 'roof':
                f["properties"]['ground_height'] = round(row["mean"], 2)
                f["properties"]['building_height'] = round(float(row.tags['building:levels']) * storeyheight + 1.3, 2) 
                f["properties"]['roof_height'] = round(f["properties"]['building_height'] + row["mean"], 2)
                   
                f["properties"]['ground_height'] = round(row["mean"], 2)
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

def getOsmBld(jparams):
    """
    read osm buildings to gdf, extract the representative_point() for each polygon
    and create a basic xyz_df;
    """
    dis = gpd.read_file(jparams['osm_bldings'])
    dis.set_crs(epsg=int(jparams['crs'][-5:]), inplace=True, allow_override=True)
    
    dict_vertices = {}
    cols = [c for c in ['bottom_bridge_height', 'bottom_roof_height', 'roof_height'] if c in dis.columns]
    
    for i, row in dis.iterrows():
        oring = list(row.geometry.exterior.coords)
        if row.geometry.exterior.is_ccw == False:
            oring.reverse()
        #name = row['osm_id']
        for (j, v) in enumerate(oring[:-1]):
            vertex = (oring[j][0], oring[j][1])
            attr = [row[c] for c in cols]
            attr = [x for x in attr if not np.isnan(x)]  # Remove np.nan values
            if vertex in dict_vertices.keys():
                dict_vertices[vertex][row['osm_id']] = attr
            else:
                dict_vertices[vertex] = {row['osm_id']: attr}
    
    result = {}
    for k1, d in dict_vertices.items():
        for k2 in d:
            result.setdefault(k2, {})[k1] = sorted(list(set([j for i in d.values() for j in i])))
    
# =============================================================================
#     ##-- the topojson simplify from the very first function (line 98) does this; but lets keep it for now
#     ##--  remove duplicate vertices within tolerance 0.2 
#     for index, row in dis.iterrows():
#         tmp_gdf = dis.copy()
#         tmp_gdf['distance'] = tmp_gdf.distance(row['geometry'])
#         closest_geom = list(tmp_gdf.sort_values('distance')['geometry'])[1]
#         # I took 1 because index 0 would be the row itself
#         snapped_geom = snap(row['geometry'], closest_geom, 0.2)
#         dis.loc[index, 'geometry'] = snapped_geom
# =============================================================================
       
    dis.drop(dis.index[dis['osm_building'] == 'bridge'], inplace = True)
    dis.drop(dis.index[dis['osm_building'] == 'roof'], inplace = True)
    
    # create a point representing the hole within each building  
    dis['x'] = dis.representative_point().x
    dis['y'] = dis.representative_point().y
    hs = dis[['x', 'y', 'ground_height']].copy()
    
    return dis, hs, result

def getOsmArea(aoi, outFile, b_type, crs):
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
    min_zbld = []
    dps = 3
    segs = set()
    
    for ids, row in dis.iterrows():
        oring = list(row.geometry.exterior.coords)
        coords_rounded = [(round(x, dps), round(y, dps), round(float(rasterQuery2(x, y, gt_forward, rb)), 2)) for x, y in oring]
        all_coords.extend(coords_rounded)
        zbld = [z for x, y, z in coords_rounded]
        min_zbld.append(min(zbld))
        
        segs.update({(x1, y1, x2, y2) if (x1 < x2) else (x2, y2, x1, y1) for (x1, y1, z1), (x2, y2, z2) in zip(coords_rounded[:-1], coords_rounded[1:])})
        
        for interior in row.geometry.interiors:
            oring = list(interior.coords)
            coords_rounded = [(round(x, dps), round(y, dps), round(float(rasterQuery2(x, y, gt_forward, rb)), 2)) for x, y in oring]
            all_coords.extend(coords_rounded)
            
            segs.update({(x1, y1, x2, y2) if (x1 < x2) else (x2, y2, x1, y1) for (x1, y1, z1), (x2, y2, z2) in zip(coords_rounded[:-1], coords_rounded[1:])})
    
    c = pd.DataFrame.from_dict({"coords": list(segs)}).groupby("coords").size().reset_index(name="count")
    
    ac = pd.DataFrame(all_coords, 
                      columns=["x", "y", "z"]).sort_values(by="z", ascending=False).drop_duplicates(subset=["x", "y"]).reset_index(drop=True)
        
    return ac, c, min_zbld

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
    dps = 3
    segs = set()
    
    for ids, row in aoi.iterrows():
        oring = list(row.geometry.exterior.coords)
        coords_rounded = [(round(x, dps), round(y, dps), round(float(rasterQuery2(x, y, gt_forward, rb)), 2)) for x, y in oring]
        aoi_coords.extend(coords_rounded)
        
        segs.update({(x1, y1, x2, y2) if (x1 < x2) else (x2, y2, x1, y1) for (x1, y1, z1), (x2, y2, z2) in zip(coords_rounded[:-1], coords_rounded[1:])})
        
        for interior in row.geometry.interiors:
            oring = list(interior.coords)
            coords_rounded = [(round(x, dps), round(y, dps), round(float(rasterQuery2(x, y, gt_forward, rb)), 2)) for x, y in oring]
            aoi_coords.extend(coords_rounded)
            
            segs.update({(x1, y1, x2, y2) if (x1 < x2) else (x2, y2, x1, y1) for (x1, y1, z1), (x2, y2, z2) in zip(coords_rounded[:-1], coords_rounded[1:])})
    
    ca = pd.DataFrame.from_dict({"coords": list(segs)}).groupby("coords").size().reset_index(name="count")
    
    acoi = pd.DataFrame(aoi_coords, 
                      columns=["x", "y", "z"]).sort_values(by="z", ascending=False).drop_duplicates(subset=["x", "y"]).reset_index(drop=True)
    
    return acoi, ca

def concatCoords(gdf, ac):
    df2 = pd.concat([gdf, ac])
    
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
    #Tr = tr.triangulate(A, 'pVV')  # the VV will print stats in the cmd
    Tr = tr.triangulate(A) 
    t = Tr.get('triangles').tolist()
    
     #-- matplotlib for basic 2D plot
    #plt.figure(figsize=(8, 8))
    #ax = plt.subplot(111, aspect='equal')
    #tr.plot(ax, **Tr)
    #plt.show()
      
    return t
       
def extrudeRoofGround(orng, irngs, height, reverse, allsurfaces, cm):
    oring = copy.deepcopy(orng)
    irings = copy.deepcopy(irngs)
    if reverse == True:
        oring.reverse()
        for each in irings:
            each.reverse()
    for (i, pt) in enumerate(oring):
        cm['vertices'].append([round(pt[0], 3), round(pt[1], 3), height])
        oring[i] = (len(cm['vertices']) - 1)
    for (i, iring) in enumerate(irings):
        for (j, pt) in enumerate(iring):
            cm['vertices'].append([round(pt[0], 3), round(pt[1], 3), height])
            irings[i][j] = (len(cm['vertices']) - 1)
    output = []
    output.append(oring)
    for each in irings:
        output.append(each)
    allsurfaces.append(output)

def outputCityjsonB(extent, minz, maxz, T, pts, jparams, min_zbld, result):
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
           
    cm = doVcBndGeomB(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams, min_zbld, result)
    
    json_str = json.dumps(cm, indent=2)
    fout = open(jparams['cjsn_out'], "w")
    fout.write(json_str)  
    ##- close fiona object
    c.close() 
    
    ##--clean cityjson
    cm = cityjson.load(jparams['cjsn_out'])
    cityjson.save(cm, jparams['cjsn_solid'])

def doVcBndGeomB(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams, min_zbld, result): 
    
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
    
    count = 0
    ##-- then buildings
    for (i, geom) in enumerate(lsgeom):
        
        poly = list(result[lsattributes[i]['osm_id']].values())  #--- a list with the heights at each vertex

        
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
        
        if lsattributes[i]['osm_building'] == 'bridge':
            #--- make sure the list of heights at each vertex do not go higher than the roof height
            edges = [[ele for ele in sub if ele <= lsattributes[i]['roof_height']] for sub in poly]
            extrude_walls(oring, lsattributes[i]['roof_height'], lsattributes[i]['bottom_bridge_height'], 
                          allsurfaces, cm, edges)
            count = count + 1

        if lsattributes[i]['osm_building'] == 'roof':
            #--- make sure the list of heights at each vertex do not go higher than the roof height
            edges = [[ele for ele in sub if ele <= lsattributes[i]['roof_height']] for sub in poly]
            extrude_walls(oring, lsattributes[i]['roof_height'], lsattributes[i]['bottom_roof_height'], 
                          allsurfaces, cm, edges)
            count = count + 1

        if lsattributes[i]['osm_building'] != 'bridge' and lsattributes[i]['osm_building'] != 'roof':
            #--- make sure the list of heights at each vertex do not go higher than the roof height
            new_edges = [[ele for ele in sub if ele <= lsattributes[i]['roof_height']] for sub in poly]
            #--- add the height of the ground level to each vertex in the list
            new_edges = [[min_zbld[i-count]] + sub_list for sub_list in new_edges]
            extrude_walls(oring, lsattributes[i]['roof_height'], min_zbld[i-count], 
                          allsurfaces, cm, new_edges)
        
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
            extrude_int_walls(iring, lsattributes[i]['roof_height'], min_zbld[i-count], allsurfaces, cm)
        #-- top-bottom surfaces

        if lsattributes[i]['osm_building'] == 'bridge':
            extrude_roof_ground(oring, irings, lsattributes[i]['roof_height'], 
                                False, allsurfaces, cm)
            extrude_roof_ground(oring, irings, lsattributes[i]['bottom_bridge_height'], 
                                True, allsurfaces, cm)
        if lsattributes[i]['osm_building'] == 'roof':
            extrude_roof_ground(oring, irings, lsattributes[i]['roof_height'], 
                                False, allsurfaces, cm)
            extrude_roof_ground(oring, irings, lsattributes[i]['bottom_roof_height'], 
                                True, allsurfaces, cm)
        if lsattributes[i]['osm_building'] != 'bridge' and lsattributes[i]['osm_building'] != 'roof':
        #else:
            extrude_roof_ground(oring, irings, lsattributes[i]['roof_height'], 
                            False, allsurfaces, cm)
            extrude_roof_ground(oring, irings, min_zbld[i-count], True, allsurfaces, cm)
        
        #-- add the extruded surfaces to the geometry
        g['boundaries'] = []
        g['boundaries'].append(allsurfaces)
        #g['boundaries'] = allsurfaces
        #-- add the geom to the building 
        oneb['geometry'].append(g)
        #-- insert the building as one new city object
        cm['CityObjects'][lsattributes[i]['osm_id']] = oneb

    return cm

def add_terrain_v(pts, cm):
    for p in pts:
        cm['vertices'].append([p[0], p[1], p[2]])
    
def add_terrain_b(Terr, allsurfaces):
    for i in Terr:
        allsurfaces.append([[i[0], i[1], i[2]]]) 

def extrude_walls(ring, height, ground, allsurfaces, cm, edges): 
    dps = 3
    #-- each edge become a wall, ie a rectangle
    for (j, v) in enumerate(ring[:-1]):
        
        if len(edges[j]) > 2 or len(edges[j+1]) > 2:
            cm['vertices'].append([round(ring[j][0], dps), round(ring[j][1], dps), edges[j][0]])
            cm['vertices'].append([round(ring[j+1][0], dps), round(ring[j+1][1], dps), edges[j+1][0]])
            c = 0
            for i, o in enumerate(edges[j+1][1:]):
                cm['vertices'].append([round(ring[j+1][0], dps), round(ring[j+1][1], dps), o])
                c = c + 1
            for i in edges[j][::-1][:-1]:
                cm['vertices'].append([round(ring[j][0], dps), round(ring[j][1], dps), i])
                c = c + 1
            t = len(cm['vertices'])
            c = c + 2
            b = c
            l = []
            for i in range(c):
                l.append(t-b)
                b = b - 1 
            allsurfaces.append([l])

        if len(edges[j]) == 2 and len(edges[j+1]) == 2:
            cm['vertices'].append([round(ring[j][0], dps),   round(ring[j][1], dps),   edges[j][0]])
            cm['vertices'].append([round(ring[j+1][0], dps), round(ring[j+1][1], dps), edges[j+1][0]])
            cm['vertices'].append([round(ring[j+1][0], dps), round(ring[j+1][1], dps), edges[j+1][1]])
            cm['vertices'].append([round(ring[j][0], dps),   round(ring[j][1], dps),   edges[j][1]])
            t = len(cm['vertices'])
            allsurfaces.append([[t-4, t-3, t-2, t-1]])
            
    if len(edges[-1]) == 2 and len(edges[0]) == 2:
        cm['vertices'].append([round(ring[-1][0], dps),  round(ring[-1][1], dps), edges[-1][0]]) 
        cm['vertices'].append([round(ring[0][0], dps), round(ring[0][1], dps), edges[0][0]])
        cm['vertices'].append([round(ring[0][0], dps),  round(ring[0][1], dps),  edges[0][1]])
        cm['vertices'].append([round(ring[-1][0], dps), round(ring[-1][1], dps), edges[-1][1]])
        t = len(cm['vertices'])
        allsurfaces.append([[t-4, t-3, t-2, t-1]])
        
    if len(edges[-1]) > 2 or len(edges[0]) > 2:
        c = 0
        cm['vertices'].append([round(ring[-1][0], dps),   round(ring[-1][1], dps),   edges[-1][0]])
        cm['vertices'].append([round(ring[0][0], dps), round(ring[0][1], dps), edges[0][0]])
        for i, o in enumerate(edges[0][1:]):
            cm['vertices'].append([round(ring[0][0], dps), round(ring[0][1], dps), o])
            c = c + 1
        for i in edges[-1][::-1][:-1]:
            cm['vertices'].append([round(ring[-1][0], dps),   round(ring[-1][1], dps),   i])
            c = c + 1
        t = len(cm['vertices'])
        c = c + 2
        b = c
        l = []
        for i in range(c): 
            l.append(t-b)
            b = b - 1 
        allsurfaces.append([l])
     
def extrude_int_walls(ring, height, ground, allsurfaces, cm):
    
    dps = 3
    #-- each edge become a wall, ie a rectangle
    for (j, v) in enumerate(ring[:-1]):
        cm['vertices'].append([round(ring[j][0], dps),   round(ring[j][1], dps),   ground])
        #values.append(0)
        cm['vertices'].append([round(ring[j+1][0], dps), round(ring[j+1][1], dps), ground])
        #values.append(0)
        cm['vertices'].append([round(ring[j+1][0], dps), round(ring[j+1][1], dps), height])
        cm['vertices'].append([round(ring[j][0], dps),   round(ring[j][1], dps),   height])
        t = len(cm['vertices'])
        allsurfaces.append([[t-4, t-3, t-2, t-1]])    
    #-- last-first edge
    cm['vertices'].append([round(ring[-1][0], dps), round(ring[-1][1], dps), ground])
    #values.append(0)
    cm['vertices'].append([round(ring[0][0], dps),  round(ring[0][1], dps),  ground])
    cm['vertices'].append([round(ring[0][0], dps),  round(ring[0][1], dps),  height])
    #values.append(0)
    cm['vertices'].append([round(ring[-1][0], dps), round(ring[-1][1], dps), height])
    t = len(cm['vertices'])
    allsurfaces.append([[t-4, t-3, t-2, t-1]])
    
def extrude_roof_ground(orng, irngs, height, reverse, allsurfaces, cm):
    oring = copy.deepcopy(orng)
    irings = copy.deepcopy(irngs)
    if reverse == True:
        oring.reverse()
        for each in irings:
            each.reverse()
    for (i, pt) in enumerate(oring):
        cm['vertices'].append([round(pt[0], 3), round(pt[1], 3), height])
        oring[i] = (len(cm['vertices']) - 1)
    for (i, iring) in enumerate(irings):
        for (j, pt) in enumerate(iring):
            cm['vertices'].append([round(pt[0], 3), round(pt[1], 3), height])
            irings[i][j] = (len(cm['vertices']) - 1)
    output = []
    output.append(oring)
    for each in irings:
        output.append(each)
    allsurfaces.append(output)