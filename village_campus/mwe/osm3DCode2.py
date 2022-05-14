# -*- coding: utf-8 -*-
# env/osm3D_vc-env
#########################
# code to create LoD1 3D City Model from volunteered public data (OpenStreetMap) with elevation via a raster DEM.

# author: arkriger - May 2022
# github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel

# script credit:
#    - building height from osm building:level: https://github.com/ualsg/hdb3d-code/blob/master/hdb2d.py - Filip Biljecki <filip@nus.edu.sg>
#    - polygon to lines without duplicate edges: https://gis.stackexchange.com/questions/236903/converting-polygon-to-lines-without-duplicate-edges
#    - gdal raster query: https://gis.stackexchange.com/questions/269603/extract-raster-values-from-point-using-gdal
#    - geopandas snap routine: https://gis.stackexchange.com/questions/290092/how-to-do-snapping-in-geopandas
#    - extruder: https://github.com/cityjson/misc-example-code/blob/master/extruder/extruder.py - Hugo Ledoux <h.ledoux@tudelft.nl>

#additional thanks:
#    - OpenStreetMap help: https://help.openstreetmap.org/users/19716/arkriger
#    - cityjson community: https://github.com/cityjson
#########################
import os
from itertools import chain
from math import floor
import struct

import requests
import overpass
import osm2geojson

import numpy as np
import pandas as pd
import geopandas as gpd

import shapely
#shapely.speedups.disable()
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
#from rasterstats import zonal_stats, point_query

#import pydeck as pdk

import pyvista as pv
import triangle as tr

import matplotlib.pyplot as plt

import time
from datetime import timedelta

def requestOsmBld(jparams):
    """
    request osm for building footprints - save
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
    gj = osm2geojson.json2geojson(r.json())
    
    #-- store the data as GeoJSON
    with open(jparams['ori-gjson_out'], 'w') as outfile:
        json.dump(gj, outfile)
        
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
    request osm area - save
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
    area = osm2geojson.json2geojson(r.json())
    #-- store the data as GeoJSON
    with open(jparams['aoi'], 'w') as outfile:
        json.dump(area, outfile)
        
    return area

def prepareDEM(extent, jparams):
    """
    gdal.Warp to reproject and clip raster dem
    """
    OutTile = gdal.Warp(jparams['projClip_raster'], 
                        #'/vsimem/proj.tif',
                        jparams['in_raster'], 
                        dstSRS=jparams['crs'],
                        srcNodata = jparams['nodata'],
                        #dstNodata = 0,
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
                         format = 'XYZ')#,
                         #noData = float(0))
    xyz = None
    
def rasterQuery(geom, gt_forward, rb):
    
    mx = geom.representative_point().x
    my = geom.representative_point().y
    
    px = int((mx - gt_forward[0]) / gt_forward[1])
    py = int((my - gt_forward[3]) / gt_forward[5])

    intval = rb.ReadAsArray(px, py, 1, 1)
    
    return intval[0][0]

def assignZ(vfname, gt_forward, rb): # rfname,
    """
    assign a height attribute - mean ground - to the osm vector 
    ~ .representative_point() used instead of .centroid
    """
    ts = gpd.read_file(vfname)
    
    #-- skywalk --bridge
    ts['bld'] = ts['tags'].apply(lambda x: x.get('building'))
    skywalk = ts[ts['bld'] == 'bridge'].copy()
    ts.drop(ts.index[ts['bld'] == 'bridge'], inplace = True)
    if len(skywalk) > 0:
        skywalk['mean'] = skywalk.apply(lambda row: rasterQuery(row.geometry, gt_forward, rb), axis = 1)
    
    ts['mean'] = ts.apply(lambda row : rasterQuery(row.geometry, gt_forward, rb), axis = 1)
    
    return ts, skywalk
    
def writegjson(ts, jparams):#, fname):
    """
    read the gdal geojson and create new attributes in osm vector
    ~ ground height, relative building height and roof height.
    write the result to file.
    """
    # take care of non-Polygon LineString's 
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
        # at a minimum we only want building:levels tagged
        #if row.tags['building:levels'] != row.tags['building:levels'].astype(str): #'building:levels' in row.tags and 
        #if row['type'] != 'node' and 'tags' in row is not None and 'building:levels' in row['tags'] and type(row['tags']['building:levels']) is not str:
        if row['type'] != 'node' and row['tags'] != None and 'building:levels' in row['tags']:#\
    
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
                for poly in osm_shape:
                    osm_shape = Polygon(poly)#[0])
                    #-- convert the shapely object to geojson
            
            wgs84 = pyproj.CRS('EPSG:4326')
            utm = pyproj.CRS(jparams['crs'])
            p = osm_shape.representative_point()
            project = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform
            wgs_point = transform(project, p)
            f["properties"]["plus_code"] = olc.encode(wgs_point.y, wgs_point.x, 11)
                
            f["geometry"] = mapping(osm_shape)
    
            #-- finally calculate the height and store it as an attribute
            # if row["mean"] == None:
            #     z = float(0)
            # if row["mean"] != None:
            #     z = round(row["mean"], 2)
            
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
    with open(jparams['gjson-z_out'], 'w') as outfile:
        json.dump(footprints, outfile)

def write_Skygjson(bridge, jparams):#, fname):
    """
    read the gdal skywalk geojson and create new attributes in osm vector
    ~ ground height, relative building min_height and roof/max height.
    write the result to file.
    """
    # take care of non-Polygon LineString's 
    for i, row in bridge.iterrows():
        if row.geometry.type == 'LineString' and len(row.geometry.coords) < 3:
            bridge = bridge.drop(bridge.index[i])
    
    storeyheight = 2.8
    #-- iterate through the list of buildings and create GeoJSON features rich in attributes
    skyprints = {
        "type": "FeatureCollection",
        "features": []
        }
    
    for i, row in bridge.iterrows():
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
            for poly in osm_shape:
                osm_shape = Polygon(poly)#[0])
                #-- convert the shapely object to geojson
                
        f["geometry"] = mapping(osm_shape)

        
        f["properties"]['ground_height'] = round(row["mean"], 2)
        f["properties"]['building_height'] = round(float(row.tags['building:levels']) * storeyheight, 2)
        f["properties"]['min_height'] = round((float(row.tags['building:min_level']) * storeyheight) + row["mean"], 2)
        f["properties"]['max_height'] = round(f["properties"]['building_height'] + row["mean"], 2)
        skyprints['features'].append(f)
                     
    #-- store the data as GeoJSON
    with open(jparams['SKYwalk_gjson-z_out'], 'w') as outfile:
        json.dump(skyprints, outfile)

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
                     
    #gdf['z'] = gdf['z'].replace('None', float(0))
    gdf = gdf[gdf['z'] != jparams['nodata']]
    #gdf['z'].fillna(value=0, inplace=True)
    gdf = gdf.round(2)
    gdf.reset_index(drop=True, inplace=True)
    
    return gdf

def getosmBld(jparams):
    """
    read osm buildings to gdf, extract the representative_point() for each polygon
    and create a basic xyz_df;
    """
    dis = gpd.read_file(jparams['gjson-z_out'])
    dis.set_crs(epsg=int(jparams['crs'][-5:]), inplace=True, allow_override=True)
 
    # remove duplicate vertices within tolerance 0.2 
    for index, row in dis.iterrows():
        tmp_gdf = dis.copy()
        tmp_gdf['distance'] = tmp_gdf.distance(row['geometry'])
        closest_geom = list(tmp_gdf.sort_values('distance')['geometry'])[1]
        # I took 1 because index 0 would be the row itself
        snapped_geom = snap(row['geometry'], closest_geom, 0.2)
        dis.loc[index, 'geometry'] = snapped_geom
    
     # - the following is left for reference
     #-- this serves two functions:
     #               i)  verify footprints removed
     #               ii) remove `outline` that overwrite `building:parts` 
     #                   - how does https://3dbuildings.com/data/#17.59/-33.932156/18.638025/131.2/60
     #                   - and https://demo.f4map.com/#lat=-33.9319930&lon=18.6386228&zoom=19&camera.theta=69.973&camera.phi=-126.624
     #                   - display the form correctly?      
    #dis = dis.loc[(dis.osm_id != 13076003) & (dis.osm_id != 12405081)] 
     #-- save
    #dis.to_file(jparams['gjson-z_out'], driver='GeoJSON')
    
    # create a point representing the hole within each building  
    dis['x'] = dis.representative_point().x
    dis['y'] = dis.representative_point().y
    hs = dis[['x', 'y', 'ground_height']].copy()
    
    return dis, hs

def getosmArea(filen, b_type, crs):
    """
    read osm area to gdf and buffer
    - get the extent for the cityjson
    """
    aoi = gpd.read_file(filen)
    
    # when relations return may areas
    if b_type == 'relation' and len(aoi) > 1:
        for i, row in aoi.iterrows():
            if row.tags != None and 'place' in row.tags:
                focus = row
            
        trim = pd.DataFrame(focus)
        trim = trim.T
        aoi = gpd.GeoDataFrame(trim, geometry = trim['geometry'])
        
    aoi = aoi.set_crs(crs)
                        
    buffer = gpd.GeoDataFrame(aoi, geometry = aoi.geometry)
    buffer['geometry'] = aoi.buffer(150, cap_style = 2, join_style = 2)
    
    extent = [buffer.total_bounds[0] - 250, buffer.total_bounds[1] - 250, 
              buffer.total_bounds[2] + 250, buffer.total_bounds[3] + 250]
    
    return aoi, extent

def getBldVertices(dis):
    """
    retrieve vertices from building footprints ~ without duplicates 
    - these vertices already have a z attribute
    """
    all_coords = []
    dps = 2
    segs = {}
    geoms = {}
    
    for ids, row in dis.iterrows():
        oring, z = list(row.geometry.exterior.coords), row['ground_height']
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
        
    return ac, c

def rasterQuery2(mx, my, gt_forward, rb):
    
    px = int((mx - gt_forward[0]) / gt_forward[1])
    py = int((my - gt_forward[3]) / gt_forward[5])

    intval = rb.ReadAsArray(px, py, 1, 1)

    return intval[0][0]

def getAOIVertices(aoi, gt_forward, rb): #fname,
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
            # if z == None:
            #     rounded_z = float(0)
            # if z != None:
            #     rounded_z = round(z, 2)
    
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
    
    for i, row in c.iterrows():
        frx, fry = row.coords[0], row.coords[1]
        tox, toy = row.coords[2], row.coords[3]

        [index_f] = (ac[(ac['x'] == frx) & (ac['y'] == fry)].index.values)
        [index_t] = (ac[(ac['x'] == tox) & (ac['y'] == toy)].index.values)
        idx.append([l + index_f, l + index_t])
    
    return idx

def executeDelaunay(hs, df3, idx):
    """
    perform Triangle ~ constrained Delaunay with concavitities removed
    - return the simplices: indices of vertices that create the triangles
    """      
    holes = hs[['x', 'y']].round(3).values.tolist()
    pts = df3[['x', 'y']].values #, 'z']].values
        
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
    
def output_cityjson(extent, minz, maxz, T, pts, jparams, skywalk):
    """
    basic function to produce LoD1 City Model
    - buildings and terrain
    """
     ##- open building ---fiona object
    c = fiona.open(jparams['gjson-z_out'])
    lsgeom = [] #-- list of the geometries
    lsattributes = [] #-- list of the attributes
    for each in c:
        lsgeom.append(shape(each['geometry'])) #-- geom are cast to Fiona's 
        lsattributes.append(each['properties'])
        
    ##- open skywalk ---fiona object
    if len(skywalk) > 0:
        sky = fiona.open(jparams['SKYwalk_gjson-z_out'])
        skywgeom = [] #-- list of the geometries
        skywgeomattributes = [] #-- list of the attributes
        for each in sky:
            skywgeom.append(shape(each['geometry'])) #-- geom are casted to Fiona's 
            skywgeomattributes.append(each['properties'])
            
        cm = doVcBndGeom(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams, skywgeom,
                        skywgeomattributes)    
        json_str = json.dumps(cm, indent=2)
        fout = open(jparams['cjsn_out'], "w")
        fout.write(json_str)  
         ##- close fiona object
        c.close()
    else: 
        cm = doVcBndGeom(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams, skywgeom=None,
                         skywgeomattributes=None)    
        json_str = json.dumps(cm, indent=2)
        fout = open(jparams['cjsn_out'], "w")
        fout.write(json_str)  
         ##- close fiona object
        c.close()
    
    #clean cityjson
    cm = cityjson.load(jparams['cjsn_out'])
    cm.remove_duplicate_vertices()
    cityjson.save(cm, jparams['cjsn_CleanOut'])

def doVcBndGeom(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams, skywgeom=None,
                    skywgeomattributes=None): 
    #-- create the JSON data structure for the City Model
    cm = {}
    cm["type"] = "CityJSON"
    cm["version"] = "1.1"
    # cm["transform"] = {
    #     "scale": [0.0, 0.0, 0.0],
    #     "translate": [1.0, 1.0, 1.0]
    #     },
    cm["CityObjects"] = {}
    cm["vertices"] = []
    #-- Metadata is added manually
    cm["metadata"] = {
    "title": jparams['cjsn_title'],
    "referenceDate": jparams['cjsn_referenceDate'],
    #"dataSource": jparams['cjsn_source'],
    #"geographicLocation": jparams['cjsn_Locatn'],
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
    #"metadataStandard": jparams['metaStan'],
    #"metadataStandardVersion": jparams['metaStanV']
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
    allsurfaces = [] #-- list of surfaces
    add_terrain_b(T, allsurfaces)
    g['boundaries'] = allsurfaces
      #-- add the geom 
    grd['geometry'].append(g)
      #-- insert the terrain as one new city object
    cm['CityObjects']['terrain01'] = grd
    
     #-- then buildings
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
        extrude_walls(oring, lsattributes[i]['roof_height'], lsattributes[i]['ground_height'],
                      allsurfaces, cm)
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
            extrude_walls(iring, lsattributes[i]['roof_height'], lsattributes[i]['ground_height'],
                          allsurfaces, cm)
        #-- top-bottom surfaces
        extrude_roof_ground(oring, irings, lsattributes[i]['roof_height'], 
                            False, allsurfaces, cm)
        extrude_roof_ground(oring, irings, lsattributes[i]['ground_height'], 
                            True, allsurfaces, cm)
        #-- add the extruded geometry to the geometry
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
            #-- one building
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

    return cm

def add_terrain_v(pts, cm):
    #cm['vertices'] = pts
    for p in pts:
        cm['vertices'].append([p[0], p[1], p[2]])
    
def add_terrain_b(T, allsurfaces):
    for i in T:
        allsurfaces.append([[i[0], i[1], i[2]]]) 
    
def extrude_roof_ground(orng, irngs, height, reverse, allsurfaces, cm):
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

def extrude_walls(ring, height, ground, allsurfaces, cm):
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
    
def write275obj(jparams):
    """
    export 2.75D wavefront.obj surface
    """
    
    cm1 = cityjson.load(jparams['cjsn_out'])
    with open(jparams['obj-2_75D'], 'w+') as f:
        re = cm1.export2obj()
        f.write(re.getvalue())
    
