# -*- coding: utf-8 -*-
# env/osm3D
#########################
# code to create LoD1 3D City Model from volunteered public data (OpenStreetMap) with elevation via a raster DEM.

# author: arkriger - January 2022
# github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel

# script credit:
#    - building height from osm building:level: https://github.com/ualsg/hdb3d-code/blob/master/hdb2d.py - Filip Biljecki <filip@nus.edu.sg>
#    - polygon to lines without duplicate edges: https://gis.stackexchange.com/questions/236903/converting-polygon-to-lines-without-duplicate-edges
#    - geopandas snap routine: https://gis.stackexchange.com/questions/290092/how-to-do-snapping-in-geopandas
#    - extruder: https://github.com/cityjson/misc-example-code/blob/master/extruder/extruder.py - Hugo Ledoux <h.ledoux@tudelft.nl>

#additional thanks:
#    - OpenStreetMap help: https://help.openstreetmap.org/users/19716/arkriger
#    - cityjson community: https://github.com/cityjson/specs/discussions/79
#########################
import os
from itertools import chain

from pyrosm import OSM, data
from pyrosm import get_data

import numpy as np
import pandas as pd
import geopandas as gpd

import shapely
shapely.speedups.disable()
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
from rasterstats import zonal_stats, point_query

import pydeck as pdk

import pyvista as pv
import triangle as tr

import matplotlib.pyplot as plt

import time
from datetime import timedelta

def getOsmPBF(jparams):
    """
    get osm.pbf and buildings
    """  
    if jparams['update'] == "False":
        fp = get_data(jparams['pbf_area'], update=False, directory=jparams['pbf_directory'])
        
     ##-- True here ...
    
    osm = OSM(fp)
    a_string = jparams['Focus_area']
    shapes = a_string.split(",") 
    
    if len(shapes) == 1:
        aoi = osm.get_boundaries(name=shapes[0])
              
    if len(shapes) > 1:
        df = pd.DataFrame()
        
        for i in shapes:
            aoi = osm.get_boundaries(name=i)
            df = df.append(aoi)
        
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        aoi = gdf.dissolve()
        
    aoi = aoi.set_crs(4326) 
    aoi_proj = aoi.to_crs(jparams['crs'])
     
    # Get the shapely geometry
    bbox_geom = aoi['geometry'].values[0]
    # Initiliaze with bounding box
    osm = OSM(fp, bounding_box=bbox_geom)
    # Retrieve buildings
    focus = osm.get_buildings()
     #-- save
    focus.to_file(jparams['ori-gjson_out'], driver='GeoJSON')
    
    buffer = gpd.GeoDataFrame(aoi_proj, geometry = aoi_proj.geometry, crs=jparams['crs'])
    buffer['geometry'] = aoi_proj.buffer(150, cap_style = 2, join_style = 2)
    
    extent = [buffer.total_bounds[0] - 250, buffer.total_bounds[1] - 250, 
              buffer.total_bounds[2] + 250, buffer.total_bounds[3] + 250]
    
    return buffer, extent

       
def projVec(outfile, infile, crs):
    """
    gdal.VectorTranslate
    """
    ds = gdal.VectorTranslate(outfile, infile, 
                          format = 'GeoJSON', reproject = True, makeValid=True,
                          srcSRS='EPSG:4326', dstSRS=crs)
    # de-reference and close dataset
    del ds

# def requestOsmAoi(jparams):
#     """
#     request osm area - save
#     """
#     query = """
#     [out:json][timeout:30];
#     area[name='{0}']->.a;
#     //gather results
#     (
#     // query part for: “university”
#     {1}['name'='{2}'](area.a);
#     );
#     //print results
#     out body;
#     >;
#     out skel qt;
#     """.format(jparams['Larea'], jparams['osm_type'], jparams['Farea'])
    
#     url = "http://overpass-api.de/api/interpreter"
#     r = requests.get(url, params={'data': query})
#     area = osm2geojson.json2geojson(r.json())
#     #-- store the data as GeoJSON
#     with open(jparams['aoi'], 'w') as outfile:
#         json.dump(area, outfile)
        
#     return area

def prepareDEM(extent, jparams):
    """
    gdal.Warp to (mosaic) reproject and clip raster dem
    """
    a_string = jparams['in_raster']
    imgs = a_string.split(",") 
    
    if len(imgs) == 1:
        OutTile = gdal.Warp(jparams['projClip_raster'], 
                            jparams['in_raster'], 
                            dstSRS=jparams['crs'],
                            #-- outputBounds=[minX, minY, maxX, maxY]
                            outputBounds = [extent[0], extent[1],
                                            extent[2], extent[3]])
        OutTile = None 
     
    if len(imgs) > 1:
        OutTile = gdal.Warp(jparams['projClip_raster'], 
                            [jparams['in_raster']],
                            resampleAlg='bilinear',
                            dstSRS=jparams['crs'],
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

def assignZ(vfname, rfname):
    """
    assign a height attribute - mean ground - to the osm vector 
    ~ .representative_point() used instead of .centroid
    """
    ts = gpd.read_file(vfname)
    
     ##-- some basic manipulation to harvest only what we want
    ts.dropna(subset=['building:levels'], inplace= True)
    ts['building:levels'] = pd.to_numeric(ts['building:levels'], downcast='integer')
    ts['building:levels'] = ts['building:levels'].astype(int)
    ts = ts[ts['building:levels'] != 0]
    
     ##-- rasterstats
    l = point_query(vectors=ts['geometry'].representative_point(), 
            raster="./raster/3318CD_clip_utm33s.tif", interpolate='bilinear', 
            nodata=3.402823466385289e+38)
    
     ##-- assign to column
    ts['mean'] = np.array(l)
    
    return ts
    
def writegjson(ts, jparams):#, fname):
    """
    read the rasterstats geojson and create new attributes in osm vector
    ~ ground height, relative building height and roof height.
    write the result to file.
    """
    storeyheight = 2.8
        #-- iterate through the list of buildings and create GeoJSON 
        # features rich in attributes
    footprints = {
        "type": "FeatureCollection",
        "features": []
        }
    columns = ts.columns   
    for i, row in ts.iterrows():
        f = {
        "type" : "Feature"
        }

        f["properties"] = {}      
            #-- store all OSM attributes and prefix them with osm_ 
        f["properties"]["osm_id"] = row.id
        #columns = ts.columns
        #for c in columns:
        adr = []
                #-- transform the OSM address to string prefix with osm_
        if 'addr:flats' in columns and row['addr:flats'] != None:
            adr.append(row['addr:flats'])
        if 'addr:housenumber' in columns and row['addr:housenumber'] != None:
            adr.append(row['addr:housenumber'])
        if 'addr:housename' in columns and row['addr:housename'] != None:
            adr.append(row['addr:housename'])
        if 'addr:street' in columns and row['addr:street'] != None:
            adr.append(row['addr:street'])
        if 'addr:suburb' in columns and row['addr:suburb'] != None:
            adr.append(row['addr:suburb'])
        if 'addr:postcode' in columns and row['addr:postcode'] != None:
            adr.append(row['addr:postcode'])
        if 'addr:city' in columns and row['addr:city'] != None:
            adr.append(row['addr:city'])
        if 'addr:province' in columns and row['addr:province'] != None:
            adr.append(row['addr:province'])
                
                #-- store other OSM attributes and prefix them with osm_
        #if ts.columns != 'geometry' or ts.columns != 'addr:flats' or ts.columns != 'addr:housenumber' or \
            #ts.columns != 'addr:housename' or ts.columns != 'addr:street' or ts.columns != 'addr:suburb'\
            #or ts.columns != 'addr:postcode' or ts.columns != 'addr:city' or ts.columns != 'addr:province' \
            #and row[i] != None:
                #f["properties"]["osm_%s" % c] = row[c]
            
        f["properties"]["osm_address"] = " ".join(adr)
            
        osm_shape = row["geometry"] # shape(row["geometry"][0])
            #-- a few buildings are not polygons, rather linestrings. This converts them to polygons
            #-- rare, but if not done it breaks the code later
        if osm_shape.type == 'LineString':
            osm_shape = Polygon(osm_shape)
            #-- and multipolygons must be accounted for
        elif osm_shape.type == 'MultiPolygon':
                #osm_shape = Polygon(osm_shape[0])
            for poly in osm_shape:
                osm_shape = Polygon(poly)#[0])
                
        wgs84 = pyproj.CRS('EPSG:4326')
        utm = pyproj.CRS("EPSG:32733")
        p = osm_shape.representative_point()
        project = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform
        wgs_point = transform(project, p)
        f["properties"]["plus_code"] = olc.encode(wgs_point.y, wgs_point.x, 11)
        
        f["geometry"] = mapping(osm_shape)
            #-- finally calculate the height and store it as an attribute
        f["properties"]['ground_height'] = round(row["mean"], 2)
        f["properties"]['building_height'] = round(float(row['building:levels']) * storeyheight + 1.3, 2) 
        f["properties"]['roof_height'] = round(f["properties"]['building_height'] + row["mean"], 2)
        footprints['features'].append(f)
                
    #-- store the data as GeoJSON
    with open(jparams['gjson-z_out'], 'w') as outfile:
        json.dump(footprints, outfile)

def getXYZ(dis, buffer, jparams):
    """
    read xyz to gdf
    """
    df = pd.read_csv(jparams['xyz'], 
                     delimiter = ' ', header=None,
                     names=["x", "y", "z"])
    
    geometry = [Point(xy) for xy in zip(df.x, df.y)]
    #df = df.drop(['Lon', 'Lat'], axis=1)
    gdf = gpd.GeoDataFrame(df, crs=jparams['crs'], geometry=geometry)
    
    _symdiff = gpd.overlay(buffer, dis, how='symmetric_difference')
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

     #-- save
    dis.to_file(jparams['gjson-z_out'], driver='GeoJSON')
    
    # create a point representing the hole within each building  
    dis['x'] = dis.representative_point().x
    dis['y'] = dis.representative_point().y
    hs = dis[['x', 'y', 'ground_height']].copy()
    
    return dis, hs

def getosmArea(filen):
    """
    read osm area to gdf and buffer
    - get the extent for the cityjson
    """
    aoi = gpd.read_file(filen)
    buffer = gpd.GeoDataFrame(aoi, geometry = aoi.geometry)
    buffer['geometry'] = aoi.buffer(150, cap_style = 2, join_style = 2)
    
    extent = [aoi.total_bounds[0] - 250, aoi.total_bounds[1] - 250, 
              aoi.total_bounds[2] + 250, aoi.total_bounds[3] + 250]
    
    return buffer, extent

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

def getAOIVertices(buffer, fname):
    """
    retrieve vertices from aoi ~ without duplicates 
    - these vertices are assigned a z attribute
    """
    aoi_coords = []
    dps = 2
    segs = {}
    
    for ids, row in buffer.iterrows():
        oring = list(row.geometry.exterior.coords)
       
        coords_rounded = []
        po = []
        for x, y in oring:
            [z] = point_query(Point(x, y), raster=fname)
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
    
def output_cityjson(extent, minz, maxz, T, pts, jparams):
    """
    basic function to produce LoD1 City Model
    - buildings and terrain
    """
     ##- open fiona object
    c = fiona.open(jparams['gjson-z_out'])
    lsgeom = [] #-- list of the geometries
    lsattributes = [] #-- list of the attributes
    for each in c:
        lsgeom.append(shape(each['geometry'])) #-- geom are casted to Fiona's 
        lsattributes.append(each['properties'])
        
    cm = doVcBndGeom(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams)    
    json_str = json.dumps(cm, indent=2)
    fout = open(jparams['cjsn_out'], "w")
    fout.write(json_str)  
     ##- close fiona object
    c.close()
    
    #clean cityjson
    cm = cityjson.load(jparams['cjsn_out'])
    cm.remove_duplicate_vertices()
    cityjson.save(cm, jparams['cjsn_ClOut'])

def doVcBndGeom(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams): 
    #-- create the JSON data structure for the City Model
    cm = {}
    cm["type"] = "CityJSON"
    cm["version"] = "1.0"
    cm["CityObjects"] = {}
    cm["vertices"] = []
    #-- Metadata is added manually
    cm["metadata"] = {
    "datasetTitle": jparams['cjsn_Title'],
    "datasetReferenceDate": jparams['cjsn_RefDate'],
    #"dataSource": jparams['cjsn_source'],
    #"geographicLocation": jparams['cjsn_Locatn'],
    "referenceSystem": jparams['cjsn_refSystm'],
    "geographicalExtent": [
        extent[0],
        extent[1],
        minz ,
        extent[1],
        extent[1],
        maxz
      ],
    "datasetPointOfContact": {
        "contactName": jparams['cjsn_contName'],
        "website": jparams['cjsn_cont'],
        "contactType": jparams['cjsn_contType'],
        #"website": jparams['github']
        },
    "+metadata-extended": {
        "lineage":
            [{"featureIDs": ["terrain01"],
             "source": [
                 {
                     "description": "Chief Directorate: National Geo-spatial Information",
                     "sourceSpatialResolution": "25 metre raster DEM",
                     "sourceReferenceSystem": "urn:ogc:def:crs:EPSG:20481"
                     }],
             "processStep": {
                 "description" : "Transform raster terrain with gdal.Translate",
                 "processor": {
                     "contactName": jparams['cjsn_contName'],
                     "contactType": jparams['cjsn_contType'],
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
        #-- add the geom to the building 
        oneb['geometry'].append(g)
        #-- insert the building as one new city object
        cm['CityObjects'][lsattributes[i]['osm_id']] = oneb

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
        l = []
        cm['vertices'].append([ring[j][0],   ring[j][1],   ground])
        cm['vertices'].append([ring[j+1][0], ring[j+1][1], ground])
        cm['vertices'].append([ring[j+1][0], ring[j+1][1], height])
        cm['vertices'].append([ring[j][0],   ring[j][1],   height])
        t = len(cm['vertices'])
        allsurfaces.append([[t-4, t-3, t-2, t-1]])    
    #-- last-first edge
    l = []
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
    with open(jparams['obj2_75D'], 'w+') as f:
        re = cm1.export2obj()
        f.write(re.getvalue())
    
def write_interactive(area, jparams):
    """
    write an interactive .html via pydeck
    """
    gdf = gpd.GeoDataFrame.from_features(area['features'])
    #gdf.set_geometry("geometry", inplace=True, crs='EPSG:4326')

    bounds = gdf.geometry.bounds
    x = gdf.centroid.x
    y = gdf.centroid.y
    
    bbox = [(bounds.minx, bounds.miny), (bounds.minx, bounds.maxy), 
            (bounds.maxx, bounds.maxy), (bounds.maxx, bounds.miny)]
    
    with open(jparams['ori-gjson_out']) as f:
        gj = geojson.load(f)
    f.close()
    
    storeyheight = 2.8

    #-- iterate through the list of buildings and create GeoJSON features rich in attributes
    footprints = {
        "type": "FeatureCollection",
        "features": []
        }
    
    for i in gj['features']:
        f = {
        "type" : "Feature"
        }
        # at a minimum we only want building:levels tagged
        if 'building:levels' in i['properties']['tags']:
            f["properties"] = {}
            
            for p in i["properties"]:

            #-- store all OSM attributes and prefix them with osm_
                f["properties"]["osm_%s" % p] = i["properties"][p]
                osm_shape = shape(i["geometry"])
                #-- a few buildings are not polygons, rather linestrings. This converts them to polygons
                #-- rare, but if not done it breaks the code later
                if osm_shape.type == 'LineString':
                    osm_shape = Polygon(osm_shape)
                    #-- and multipolygons must be accounted for
                elif osm_shape.type == 'MultiPolygon':
                    osm_shape = Polygon(osm_shape[0])
                    #-- convert the shapely object to geojson
                f["geometry"] = mapping(osm_shape)
    
        #-- finally calculate the height and store it as an attribute (extrusion of geometry 
        ## -- will be done in the next script)
                f["properties"]['height'] = float(i["properties"]['tags']['building:levels']) * storeyheight + 1.3    
                footprints['features'].append(f)
    
    #-- store the data as GeoJSON
    with open(jparams['int-gjson_out'], 'w') as outfile:
        json.dump(footprints, outfile)
    
    jsn = pd.read_json(jparams['int-gjson_out'])
    build_df = pd.DataFrame()
    
    # Parse the geometry out to Pandas
    build_df["coordinates"] = jsn["features"].apply(lambda row: row["geometry"]["coordinates"])
    build_df["height"] = round(jsn["features"].apply(lambda row: row["properties"]["height"]), 1)
    
    #we want to display data so extract values from the dictionary 
    build_df["tags"] = jsn["features"].apply(lambda row: row["properties"]["osm_tags"])
    build_df['level'] = build_df['tags'].apply(lambda x: x.get('building:levels'))
    build_df['name'] = build_df['tags'].apply(lambda x: x.get('name'))
    
    ## ~ (x, y) - bl, tl, tr, br  ~~ or ~~ sw, nw, ne, se
    #area = [[[18.4377, -33.9307], [18.4377, -33.9283], [18.4418, -33.9283], [18.4418, -33.9307]]]
    area = [[[bbox[0][0][0], bbox[0][1][0]], [bbox[1][0][0], bbox[1][1][0]], 
             [bbox[2][0][0], bbox[2][1][0]], [bbox[3][0][0], bbox[3][1][0]]]]

    ## ~ (y, x)
    view_state = pdk.ViewState(latitude=y[0], longitude=x[0], zoom=16.5, max_zoom=19, pitch=72, 
                                   bearing=80)

    land = pdk.Layer(
        "PolygonLayer",
        area,
        stroked=False,
        # processes the data as a flat longitude-latitude pair
        get_polygon="-",
        get_fill_color=[0, 0, 0, 1],
        #material = True,
        #shadowEnabled = True
    )
    
    building_layer = pdk.Layer(
        "PolygonLayer",
        build_df,
        #id="geojson",
        opacity=0.3,
        stroked=False,
        get_polygon="coordinates",
        filled=True,
        extruded=True,
        wireframe=False,
        get_elevation="height",
        get_fill_color="[255, 255, 255]", #255, 255, 255
        get_line_color=[255, 255, 255],
        #material = True, 
        #shadowEnabled = True, 
        auto_highlight=True,
        pickable=True,
    )
    
    tooltip = {"html": "<b>Levels:</b> {level} <br/> <b>Name:</b> {name}"}
    
    r = pdk.Deck(layers=[land, building_layer], 
                 #views=[{"@@type": "MapView", "controller": True}],
                 initial_view_state=view_state,
                 map_style = 'dark_no_labels', 
                 tooltip=tooltip)
    
    #save
    r.to_html(jparams["intact"])
    