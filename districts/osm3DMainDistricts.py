# -*- coding: utf-8 -*-
# env/osm3D
######################
# main() for osm3DCode
# author: arkriger - January 2022
# github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel
#####################
import os
import sys
import json

import time
from datetime import timedelta

from osm3DCodeDistricts import getOsmPBF, projVec, prepareDEM, assignZ, getosmBld, writegjson,\
    getXYZ, getBldVertices, getAOIVertices, appendCoords, createSgmts, executeDelaunay, \
        pvPlot, writeObj, output_cityjson, createXYZ, write275obj
    
def main():
    start = time.time()
    
    try:
        jparams = json.load(open('osm3Ddistricts_param.json'))
    except:
        print("ERROR: something is wrong with the param.json file.")
        sys.exit()
        
    path = os.getcwd()
    d_name = 'data'
    path_i = os.path.join(path, d_name)
    os.makedirs(path_i, exist_ok=True)
    
    aoi_proj, buffer, extent = getOsmPBF(jparams, path)
    projVec(jparams['gjson-proj_out'], jparams['ori-gjson_out'], jparams['crs'])
    #area = requestOsmAoi(jparams)
    #projVec(jparams['aoi_prj'], jparams['aoi'], jparams['crs'])
    #buffer, extent = getosmArea(jparams['aoi_prj'])
    
    path = os.getcwd()
    r_name = 'result'
    path = os.path.join(path, r_name)
    os.makedirs(path, exist_ok=True)

    prepareDEM(extent, jparams)
    createXYZ(jparams['xyz'], jparams['projClip_raster'])
    ts = assignZ(jparams) # jparams['gjson-proj_out'], jparams['projClip_raster'])
    writegjson(ts, jparams)
    
    dis, hs = getosmBld(jparams)
    
    gdf = getXYZ(dis, aoi_proj, jparams)
    ac, c = getBldVertices(dis)
    df2 = appendCoords(gdf, ac)
    
    idx = []
    idx = createSgmts(ac, c, gdf, idx)
    
    acoi, ca = getAOIVertices(buffer, jparams['projClip_raster'])
        
    idx = createSgmts(acoi, ca, df2, idx)
    df3 = appendCoords(df2, acoi)
    pts = df3[['x', 'y', 'z']].values
    
     #-- change the dtype to 'float64'
    #pts = pts.astype('float64')

    t = executeDelaunay(hs, df3, idx)
    
     #-- check terrain with a plot
    pvPlot(t, pts, idx, hs)

    minz = df3['z'].min()
    maxz = df3['z'].max()
    #writeObj(pts, t, 'wvft_cput3d.obj') ~ this will write the terrain surface only
    output_cityjson(extent, minz, maxz, t, pts, jparams)
    write275obj(jparams)
    
    #if jparams['inter'] == 'True':
        #write_interactive(area, jparams)
        
    end = time.time()
    print('runtime:', str(timedelta(seconds=(end - start))))
    
     #-- Ward 57                - runtime: 0:30:31.895032 ~ (2332)  buildings with levels -> 1082, population ~  30 000
     #-- Khayelitsha (12 wards) - runtime: 0:08:00.895749 ~ (81770) buildings with levels ->   57, population ~ 390 000
     #-- Tshwane clipped from South Africa (1 ward) - runtime: 0:04:56.645984 ~ (1495) buildings with levels ->   32, population ~ 33 000

if __name__ == "__main__":
    main()