# -*- coding: utf-8 -*-
# env/osm3D_vc-env
######################
# main() for osm3DCode
# author: arkriger - Jan 2024
# github: https://github.com/AdrianKriger/osm_LoD1_3DCityModel
#####################

import os
import sys
from pynput import keyboard
import json

from osgeo import gdal

import time
from datetime import timedelta

from osm3DCode import (requestOsmBld, requestOsmAoi, getOsmArea, 
                       prepareDEM, createXYZ, 
                       assignZ, writegjson, 
                       getXYZ, 
                       mtPlot02, getOsmBld,
                       getBldVertices, createSgmts, concatCoords, getAOIVertices, 
                       executeDelaunay, 
                       outputCityjsonB)


def on_press(key, ts, gt_forward, rb, extent, aoi, aoibuffer, jparams):
    if key == keyboard.Key.enter:
        print("\nYou pressed Enter... we continue with osm_LoD1_3DCityModel.")
        
        ts = assignZ(ts, gt_forward, rb)
        writegjson(ts, jparams)
        
        dis, hs, result = getOsmBld(jparams)

        gdf = getXYZ(dis, aoibuffer, jparams)
        
        ac, c, min_zbld = getBldVertices(dis, gt_forward, rb)
        idx = []
        idx, idx01 = createSgmts(ac, c, gdf, idx)
        df2 = concatCoords(gdf, ac)

        acoi, ca = getAOIVertices(aoi, gt_forward, rb)
        idx, idx01 = createSgmts(acoi, ca, df2, idx)
        df4 = concatCoords(df2, acoi)
                    
        pts = df4[['x', 'y', 'z']].values
        pts = pts.astype('float64')
    
        t = executeDelaunay(hs, df4, idx)
                   
        minz = df4['z'].min()
        maxz = df4['z'].max()
        
        outputCityjsonB(extent, minz, maxz, t, pts, jparams, min_zbld, result)
        
        sys.exit(0)
    

def on_release(key):
    
    if key == keyboard.Key.esc:
        # Stop listener
        return False
    
def main():
    start = time.time()
    
    try:

        #jparams = json.load(open('osm3DuEstate_param.json'))
        #jparams = json.load(open('osm3Dcput_param.json'))
        jparams = json.load(open('osm3Dmamre_param.json'))

    except Exception as e:
        print("ERROR: something is wrong with the param.json file. {e}")
        sys.exit()
        
    path = os.getcwd()
    d_name = 'data'
    path = os.path.join(path, d_name)
    os.makedirs(path, exist_ok=True)
    
    ts = requestOsmBld(jparams)
    aoi = requestOsmAoi(jparams)
    aoi, aoibuffer, extent = getOsmArea(aoi, jparams['aoi'], jparams['osm_type'], jparams['crs'])
       
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
    
    mtPlot02(ts, jparams)
    print('')
    print("Have a look at the matplotlib render that might highlight errors (red) in the 2D vectors.\n\nIf there are no challenges press 'Enter' to continue; else press 'Esc' to exit: ")

    with keyboard.Listener(
            on_press=lambda key: on_press(key, ts, gt_forward, rb, extent, aoi, aoibuffer, jparams),
            on_release=on_release) as listener:
        listener.join()


    src_ds = None      
    end = time.time()
    print('runtime:', str(timedelta(seconds=(end - start))))  
   
   #--25-meter DEM
   #-- cput runtime: 0:00:08.472202 ~ university campus: 50 buildings
   #-- rural runtime: 0:03:46.493492 ~ rural village: population 9 000, 2159 buildings
   #-- neighbourhood runtime: 0:00:13.330248 ~ urban neighbourhood: population ~ 1 000, 305 buildings 

   #--10-metre DEM
   #-- cput runtime: 0:00:15.770822 ~ university campus: 50 buildings / 
   #-- rural runtime: 0:14:55.993314 ~ rural village: population 9 000, 2159 buildings /
   #-- neighbourhood runtime: 00:00:26.079256 ~ urban neighbourhood: population ~ 1 000, 305 buildings /
   
   #--5-metre DEM -- need to redo these
   #-- cput runtime: 0:05:12.451642 ~ university campus: 50 buildings / 
   #-- rural runtime:               ~ rural village: population 9 000 /
   #-- neighbourhood runtime: 0:07:29.521754 ~ urban neighbourhood: population ~ 1 000, 305 buildings /
   

if __name__ == "__main__":
    main()