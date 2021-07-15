# -*- coding: utf-8 -*-
# env/osm3D
"""
Created on Tue Jul  6 14:10:33 2021

@author: arkriger
"""
import os
from itertools import chain

import requests
import overpass
import osm2geojson

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely.geometry as sg
from shapely.geometry import Point, LineString, Polygon, shape, mapping
from shapely.ops import snap
import fiona
import copy
import json
import geojson
from cjio import cityjson

from osgeo import gdal, ogr
from rasterstats import zonal_stats, point_query

import pydeck as pdk

import pyvista as pv
import triangle as tr

import matplotlib.pyplot as plt

def requestOsmBld(jparams):
    """
    request osm for building footprints - save
    """  
    query = """
    [out:json][timeout:25];
    area[name='{0}']->.b;
    // -- target area ~ can be way or relation
    {1}(area.b)[name='{2}'];
    map_to_area -> .a;
    (
      (
        // I want all buildings
        way[building](area.a);
    
        // plus every building:part
        way["building:part"](area.a);
        // and relation type=multipolygon ~ to removed courtyards from buildings
        relation["building"]["type"="multipolygon"](area.a);
      );
    -
      // excluding buildings with relation type=building role=outline
      // to remove outlines that surround building:part
      (
        // for every way in the input set select the relations of which it is an "outline" member
        rel(bw:"outline")["type"="building"];
        // back to the ways with role "outline"
        way(r:"outline");
      );
    );
    out body;
    >;
    out skel qt;
    """.format(jparams['Larea'], jparams['osm_type'], jparams['Farea'])
    
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
    #Dereference and close dataset
    del ds

def requestOsmAoi(jparams):
    """
    request osm area
    - save
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
    """.format(jparams['Larea'], jparams['osm_type'], jparams['Farea'])
    
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
                         #-- outputBounds=[minX, minY, maxX, maxY]
                        outputBounds = [extent[0], extent[1],
                                        extent[2], extent[3]])
    OutTile = None 
      
def createXYZ(fout, fin):
    """
    read raster and extract a xyz
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
    ts['mean'] = pd.DataFrame(point_query(
        vectors=ts['geometry'].representative_point(), 
        raster=rfname))#['mean']
    
    return ts
    
def writegjson(ts, fname):
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
    
    for i, row in ts.iterrows():
        f = {
        "type" : "Feature"
        }
        # at a minimum we only want building:levels tagged
        if 'building:levels' in row.tags:
            f["properties"] = {}
            
            #-- store all OSM attributes and prefix them with osm_          
            f["properties"]["osm_id"] = row.id
            f["properties"]["osm_tags"] = row.tags
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
    
            #-- finally calculate the height and store it as an attribute
            f["properties"]['g_height'] = row["mean"]
            f["properties"]['b_height'] = float(row.tags['building:levels']) * storeyheight + 1.3  
            f["properties"]['r_height'] = f["properties"]['b_height'] + row["mean"]
            footprints['features'].append(f)
                
    #-- store the data as GeoJSON
    with open(fname, 'w') as outfile:
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
    gdf = gpd.GeoDataFrame(df, crs="EPSG:32733", geometry=geometry)
    
    _symdiff = gpd.overlay(buffer, dis, how='symmetric_difference')
    _mask = gdf.within(_symdiff.loc[0, 'geometry'])
    gdf = gdf.loc[_mask]
                     
    gdf = gdf[gdf['z'] != jparams['nodata']]
    gdf = gdf.round(2)
    
    return gdf

def getosmBld(jparams):
    """
    read osm buildings to gdf, extract the representative_point() for each polygon
    and create a basic xyz_df;
    - reduce the precision of the holes
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
    
    #dis = dis[dis.osm_id != 904207929] # need to exclude one building 
    
    # create a point representing the hole within each building  
    dis['x'] = dis.representative_point().x
    dis['y'] = dis.representative_point().y
    hs = dis[['x', 'y', 'g_height']].copy()#.values.tolist()
    
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
        oring, z = list(row.geometry.exterior.coords), row['g_height']
        rounded_z = round(z, dps)
        coords_rounded = []
        #po = []
        for x, y in oring:
            rounded_x = round(x, dps)
            rounded_y = round(y, dps)
            coords_rounded.append((rounded_x, rounded_y, rounded_z))
            all_coords.append([rounded_x, rounded_y, rounded_z])
        #oring.pop()
        #for x, y in oring:
            #all_coords.append([rounded_x, rounded_y, rounded_z])
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
        #oring.pop()
        #for x, y in oring:
            #all_coords.append([rounded_x, rounded_y, rounded_z])
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
    #ac = ac.sort_values('z', 
                        #ascending=False).drop_duplicates(subset=['x','y'], keep='last')
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
    
    # matplotlib for basic 2D plot
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
    #polygon2.points = pv_pts
    holes = hs[['x', 'y', 'g_height']].values
    
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
    
def output_citysjon(extent, minz, maxz, T, pts, jparams):
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

def doVcBndGeom(lsgeom, lsattributes, extent, minz, maxz, T, pts, jparams): 
    #-- create the JSON data structure for the City Model
    cm = {}
    cm["type"] = "CityJSON"
    cm["version"] = "0.9"
    cm["CityObjects"] = {}
    cm["vertices"] = []
    #-- Metadata is added manually
    cm["metadata"] = {
    "datasetTitle": jparams['cjsn_Title'],
    "datasetReferenceDate": jparams['cjsn_RefDate'],
    "geographicLocation": jparams['cjsn_Locatn'],
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
        "linkedin": jparams['cjsn_cont'],
        "contactType": jparams['cjsn_contType'],
        "github": jparams['github']
        },
    "metadataStandard": "ISO 19115 - Geographic Information - Metadata",
    "metadataStandardVersion": "ISO 19115:2014(E)"
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
    for (i,geom) in enumerate(lsgeom):
        footprint = geom
        #-- one building
        oneb = {}
        oneb['type'] = 'Building'
        oneb['attributes'] = {}
        for a in lsattributes[i]:
            oneb['attributes'][a] = lsattributes[i][a]
        oneb['geometry'] = [] #-- a cityobject can have >1
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
        extrude_walls(oring, lsattributes[i]['r_height'], lsattributes[i]['g_height'],
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
            extrude_walls(iring, lsattributes[i]['r_height'], lsattributes[i]['g_height'],
                          allsurfaces, cm)
        #-- top-bottom surfaces
        extrude_roof_ground(oring, irings, lsattributes[i]['r_height'], 
                            False, allsurfaces, cm)
        extrude_roof_ground(oring, irings, lsattributes[i]['g_height'], 
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
    # print(oring)
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
    
def upgradecjio(jparams):
    """
    upgrade cityjson to V1.0 and export 2.75D wavefront.obj surface
    """
    #up = 'cjio {0} upgrade_version save {1}'.format(jparams['cjsn_out'],
                                                    #jparams['cjsn_UpOut'])
    #os.system(up)
    
    #obj = 'cjio {0} export --format=obj {1}'.format(jparams['cjsn_UpOut'],
                                                    #jparams['obj2_75D'])
    #os.system(obj)
    cm = cityjson.load(jparams['cjsn_out'])
    cm.upgrade_version("1.0")
    cityjson.save(cm, jparams['cjsn_UpOut'])
    
    cm1 = cityjson.load(jparams['cjsn_UpOut'])
    with open(jparams['obj2_75D'], 'w+') as f:
        re = cm1.export2obj()
        f.write(re.getvalue())
        
    #cm1 = cityjson.load(jparams['cjsn_UpOut'])
    #cityjson.export(cm1, obj, jparams['obj2_75D'])
    
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
            #print(i["properties"]['tags']['building:levels'])
            #break
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
    