# -*- coding: utf-8 -*-
# env/osm3D_vc-env
######################
# main() for osm3DCode2
# author: arkriger - July 2022
# github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel
#####################

import os
import sys
import json

from osgeo import gdal

import time
from datetime import timedelta

from osm3DCode2 import (requestOsmBld, requestOsmAoi, getosmArea, 
                        prepareDEM, createXYZ, 
                        requestOsmRoads, prepareRoads, prep_Brdgjson,
                        assignZ, writegjson, prep_Skygjson, prep_roof, getosmBld,
                        getXYZ, 
                        getBldVertices, createSgmts, appendCoords, 
                        getRdVertices, requestOsmParking, 
                        getAOIVertices, 
                        executeDelaunay, pvPlot, 
                        output_cityjsonR, 
                        output_cityjson, 
                        writeObj, write275obj)
    
def main():
    start = time.time()
    
    try:
        jparams = json.load(open('osm3Dmamre_param.json'))
    except:
        print("ERROR: something is wrong with the param.json file.")
        sys.exit()
        
    path = os.getcwd()
    d_name = 'data'
    path = os.path.join(path, d_name)
    os.makedirs(path, exist_ok=True)
    
    ts = requestOsmBld(jparams)
    aoi = requestOsmAoi(jparams)
    aoi, aoibuffer, extent = getosmArea(aoi, jparams['aoi'], jparams['osm_type'], jparams['crs'])
       
    path = os.getcwd()
    r_name = 'result'
    path = os.path.join(path, r_name)
    os.makedirs(path, exist_ok=True)

    prepareDEM(extent, jparams)
    createXYZ(jparams['xyz'], jparams['projClip_raster'])
    
    #-- read raster
    src_filename = jparams['projClip_raster']
    src_ds = gdal.Open(src_filename) 
    gt_forward = src_ds.GetGeoTransform()
    #gt_reverse=gdal.InvGeoTransform(gt_forward)
    rb = src_ds.GetRasterBand(1)
    
    if jparams['roads'] == "Yes":
        rd = requestOsmRoads(jparams)
        pk = requestOsmParking(jparams)
        one, bridge, hsr = prepareRoads(jparams, rd, pk, aoi, aoibuffer, gt_forward, rb)
        if jparams['bridge'] == 'Yes' and len(bridge) > 0:
            bridge = prep_Brdgjson(bridge, jparams)
    
    ts, skywalk, roof = assignZ(ts, gt_forward, rb) 
    writegjson(ts, jparams)
    if len(skywalk) > 0:
        skywalk = prep_Skygjson(skywalk, jparams)
    if len(roof) > 0:
        roof = prep_roof(roof, jparams)
    
    dis, hs = getosmBld(jparams)
    
    if jparams['roads'] == "Yes":
        hs2 = hs.copy()
        hs = hs.append(hsr)
        dis_c = dis.copy()
        dis_c = dis_c.append(one)
        gdf = getXYZ(dis_c, aoibuffer, jparams)
    else:
        gdf = getXYZ(dis, aoibuffer, jparams)
    
    ac, c, min_zbld = getBldVertices(dis, gt_forward, rb)
    idx = []
    idx, idx01 = createSgmts(ac, c, gdf, idx)
    df2 = appendCoords(gdf, ac)
    
    if jparams['roads'] == "Yes":
         acoi, ca = getAOIVertices(aoi, gt_forward, rb) 
         idx, idx01 = createSgmts(acoi, ca, df2, idx)
         df3 = appendCoords(df2, acoi)
         
         t_list, rd_pts, acr, cr = getRdVertices(one, idx01, acoi, hs2, gt_forward, rb)
         idx, idx01 = createSgmts(acr, cr, df3, idx)
         df4 = appendCoords(df3, acr)
    else:
        acoi, ca = getAOIVertices(aoi, gt_forward, rb)
        idx, idx01 = createSgmts(acoi, ca, df2, idx)
        df4 = appendCoords(df2, acoi)
        
    pts = df4[['x', 'y', 'z']].values
    ##-- change the dtype to 'float64'
    pts = pts.astype('float64')

    t = executeDelaunay(hs, df4, idx)
    
    ##-- check terrain with a plot
    pvPlot(t, pts, idx, hs)

    minz = df4['z'].min()
    maxz = df4['z'].max()

    #writeObj(pts, t, 'wvft_cput3d.obj') ~ this will write the terrain surface only
    if jparams['roads'] == "Yes":
        output_cityjsonR(extent, minz, maxz, t, pts, t_list, rd_pts, jparams, min_zbld,
                         bridge, skywalk, roof, acoi, gt_forward, rb)
    else: 
        output_cityjson(extent, minz, maxz, t, pts, jparams, min_zbld, skywalk, roof)
        
    src_ds = None
    
    write275obj(jparams)
        
    end = time.time()
    print('runtime:', str(timedelta(seconds=(end - start))))
    
     #-- cput runtime: 0:00:21.761134 ~ university campus: 50 buildings / with 57 roads: 0:06:35.585379
     #-- rural runtime: 0:16:30.662577 ~ rural village: population 9 000 / with 57 roads: 0:06:35.585379
     #-- neighbourhood runtime: 0:00:41.587389 ~ urban neighbourhood: population ~ 1 000, 305 buildings / with 57 roads: 0:06:17.539262

if __name__ == "__main__":
    main()