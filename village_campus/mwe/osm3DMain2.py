# -*- coding: utf-8 -*-
# env/osm3D_vc-env
######################
# main() for osm3DCode2
# author: arkriger - May 2022
# github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel
#####################

import os
import sys
import json

from osgeo import gdal

import time
from datetime import timedelta

from osm3DCode2 import (requestOsmBld, projVec, requestOsmAoi, getosmArea, 
                        prepareDEM, createXYZ, 
                        requestOsmRoads, prepareRoads, 
                        assignZ, writegjson, write_Skygjson, write_roof, getosmBld,
                        getXYZ, 
                        getBldVertices, createSgmts, appendCoords, 
                        getRdVertices, requestOsmParking, 
                        getAOIVertices, 
                        executeDelaunay, pvPlot, 
                        output_cityjsonR, #doVcBndGeomRd, 
                        output_cityjson, 
                        writeObj, write275obj)
    
def main():
    start = time.time()
    
    try:
        jparams = json.load(open('osm3DuEstate_param.json'))
    except:
        print("ERROR: something is wrong with the param.json file.")
        sys.exit()
        
    path = os.getcwd()
    d_name = 'data'
    path = os.path.join(path, d_name)
    os.makedirs(path, exist_ok=True)
    
    requestOsmBld(jparams)
    projVec(jparams['gjson-proj_out'], jparams['ori-gjson_out'], jparams['crs'])
    requestOsmAoi(jparams)
    projVec(jparams['aoi_prj'], jparams['aoi'], jparams['crs'])
    aoi, aoibuffer, extent = getosmArea(jparams['aoi_prj'], jparams['osm_type'], jparams['crs'])
       
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
        requestOsmRoads(jparams)
        projVec(jparams['gjson_proj-rd'], jparams['gjson-rd'], jparams['crs'])
        requestOsmParking(jparams)
        projVec(jparams['gjson_proj-pk'], jparams['gjson-pk'], jparams['crs'])
        one, hsr = prepareRoads(jparams, aoi, aoibuffer, gt_forward, rb)
    
    ts, skywalk, roof = assignZ(jparams['gjson-proj_out'], gt_forward, rb) #jparams['projClip_raster'],
    writegjson(ts, jparams)#['gjson-z_out'])
    if len(skywalk) > 0:
        write_Skygjson(skywalk, jparams)
    if len(roof) > 0:
        write_roof(roof, jparams)
    
    dis, hs2 = getosmBld(jparams)
    
    if jparams['roads'] == "Yes":
        hs = hs2.append(hsr)
        dis_c = dis.copy()
        dis_c = dis_c.append(one)
        gdf = getXYZ(dis_c, aoibuffer, jparams)
    else:
        gdf = getXYZ(dis, aoibuffer, jparams)
    
    #gdf = getXYZ(dis, aoibuffer, jparams)
    ac, c = getBldVertices(dis)
    idx = []
    idx, idx01 = createSgmts(ac, c, gdf, idx)
    df2 = appendCoords(gdf, ac)
    
    if jparams['roads'] == "Yes":
         acoi, ca = getAOIVertices(aoi, gt_forward, rb) # jparams['projClip_raster'],
         idx, idx01 = createSgmts(acoi, ca, df2, idx)
         df3 = appendCoords(df2, acoi)
         
         t_list, rd_pts, acr, cr = getRdVertices(one, idx01, acoi, hs2, gt_forward, rb)
         idx, idx01 = createSgmts(acr, cr, df3, idx)
         df3 = appendCoords(df3, acr)
    else:
        acoi, ca = getAOIVertices(aoi, gt_forward, rb) # jparams['projClip_raster'],
        idx, idx01 = createSgmts(acoi, ca, df2, idx)
        df3 = appendCoords(df2, acoi)
        
    pts = df3[['x', 'y', 'z']].values
     #-- change the dtype to 'float64'
    pts = pts.astype('float64')

    t = executeDelaunay(hs, df3, idx)
    
      #-- check terrain with a plot
    pvPlot(t, pts, idx, hs2)

    minz = df3['z'].min()
    maxz = df3['z'].max()
    src_ds = None
    #writeObj(pts, t, 'wvft_cput3d.obj') ~ this will write the terrain surface only
    if jparams['roads'] == "Yes":
        output_cityjsonR(extent, minz, maxz, t, pts, t_list, rd_pts, jparams, skywalk, roof, acoi)
    else: 
        output_cityjson(extent, minz, maxz, t, pts, jparams, skywalk, roof)
    write275obj(jparams)
    
    # if jparams['inter'] == 'True':
    #     write_interactive(area, jparams)
        
    end = time.time()
    print('runtime:', str(timedelta(seconds=(end - start))))
    
     #-- cput runtime: 0:00:32.762952 ~ university campus: 50 buildings / with 57 roads: 0:10:57.293127
     #-- rural runtime: 0:16:30.662577 ~ rural village: population 9 000
     #-- neighbourhood runtime: 0:01:20.869754 ~ urban neighbourhood: population ~ 1 000, 305 buildings / with 29 roads: 0:06:08.407861

if __name__ == "__main__":
    main()