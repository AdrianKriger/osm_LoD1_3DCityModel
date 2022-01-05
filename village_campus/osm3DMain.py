# -*- coding: utf-8 -*-
# env/osm3D
"""
main() for osm3DCode
@author: arkriger - July 2021
@github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel
"""
import os
import sys
import json

import time
from datetime import timedelta

from osm3DCode import requestOsmBld, projVec, requestOsmAoi, write_interactive, \
    prepareDEM, assignZ, getosmBld, writegjson, getosmArea, getXYZ, getBldVertices, \
        getAOIVertices, appendCoords, createSgmts, executeDelaunay, pvPlot, writeObj, \
            output_citysjon, createXYZ, write275obj
    
def main():
    start = time.time()
    
    try:
        jparams = json.load(open('osm3Dcput_param.json'))
    except:
        print("ERROR: something is wrong with the param.json file.")
        sys.exit()
        
    path = os.getcwd()
    d_name = 'data'
    path = os.path.join(path, d_name)
    os.makedirs(path, exist_ok=True)
    
    requestOsmBld(jparams)
    projVec(jparams['gjson-proj_out'], jparams['ori-gjson_out'], jparams['crs'])
    area = requestOsmAoi(jparams)
    projVec(jparams['aoi_prj'], jparams['aoi'], jparams['crs'])
    buffer, extent = getosmArea(jparams['aoi_prj'])
    
    path = os.getcwd()
    r_name = 'result'
    path = os.path.join(path, r_name)
    os.makedirs(path, exist_ok=True)

    prepareDEM(extent, jparams)
    createXYZ(jparams['xyz'], jparams['projClip_raster'])
    ts = assignZ(jparams['gjson-proj_out'], jparams['projClip_raster'])
    writegjson(ts, jparams['gjson-z_out'])
    
    dis, hs = getosmBld(jparams)
    
    gdf = getXYZ(dis, buffer, jparams)
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
    output_citysjon(extent, minz, maxz, t, pts, jparams)
    write275obj(jparams)
    
    if jparams['inter'] == 'True':
        write_interactive(area, jparams)
        
    end = time.time()
    print('runtime:', str(timedelta(seconds=(end - start))))
    
     #-- cput runtime: 0:00:32.762952 ~ university campus: 50 buildings
     #-- rural runtime: 0:16:30.662577 ~ rural village: population 9 000

if __name__ == "__main__":
    main()
