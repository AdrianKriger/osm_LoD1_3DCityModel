---
layout: default
title: param.json
parent: osm_LoD1_3DCityModel
nav_order: 4
---

# `param.json`
{: .no_toc }

To produce a City Model; necessary information that defines your area-of-interest (aoi) and coordinate reference system are parsed through a basic `param.json`. These are elaborated on below.

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

### Area-of-Interest

Due to the nature of the processing strategies aoi's are defined differently

#### village/campus
```json
    "LargeArea": "Western Cape",
    "FocusArea": "Mamre",
    "osm_type": "relation",
 ```
With the village/campus strategy an aoi is defined `Large area -> focus area` or `State (Province) -> village / campus`. The area must exist in osm as either a [way or relation](https://wiki.openstreetmap.org/wiki/Elements). A number of variations are available as [Examples](https://adriankriger.github.io/osm_LoD1_3DCityModel/docs/docs/examples)

<!--#### district
```json
    "osm-pbf": "South Africa",
    "update": "True",
    "pbf_directory": "data",
    
    "trim": "yes",
    "osmconvert": "osmconvert64",
    "osm_poly": "cape-town_western-cape.poly",
    "trim_pbf": "CapeTown-extract.osm.pbf",
    
    "FocusArea": "Cape Town Ward 57",
```
In an attempt to make the solution available to the broadest possible audience we start with national [.osm.pbf](https://wiki.openstreetmap.org/wiki/PBF_Format) and trim with a [osm.poly](https://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format) via [osmconvert](https://wiki.openstreetmap.org/wiki/Osmconvert). 

[Pyrosm](https://pyrosm.readthedocs.io/en/latest/) harvests [osm.pbf](https://wiki.openstreetmap.org/wiki/PBF_Format) from [GeoFabrik](http://download.geofabrik.de/) and [BBBike](https://download.bbbike.org/osm/bbbike/). City level osm.pbf extracts are available for a number of regions and are listed on the respective [GeoFabrik](http://download.geofabrik.de/) and [BBBike](https://download.bbbike.org/osm/bbbike/) websites. If your Area-of-Interest (aoi) does not need to a less substantial [osm.pbf](https://wiki.openstreetmap.org/wiki/PBF_Format); set `"trim": 'no'` and leave the osm.pbf as is. `"trim": 'yes'` otherwise. 

An extensive range of [osm.poly](https://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format) files can be accessed at James Chevalier's [GitHub](https://github.com/JamesChevalier/cities). 

`"FocusArea"` must exist in osm as a defined [`boundary=administrative`](https://wiki.openstreetmap.org/wiki/Tag:boundary%3Dadministrative). It can be one or comma seperated (e.g.: `"FocusArea": "Cape Town Ward 18,Cape Town Ward 87,Cape Town Ward 86",`).

`"update": "True"` to access a fresh `osm.pbf`. `"False"` will use an existing `osm.pbf`.-->

A number of `param.json` are available as [Examples](https://adriankriger.github.io/osm_LoD1_3DCityModel/docs/docs/examples) to illustrate its usage.

### crs

```json
"crs": "EPSG:32733",
``` 
defines the 
Coordinate Reference System (crs) of the City Model. The workflow will project the osm vector and raster DEM into a local coordinate system. [EPSG code](https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset)'s are supported.

### raster DEM
```json
    "in_raster": "./raster/LO19_050M_3318DC.tif",
    "nodata": 3.402823466385289e+38,
    "projClip_raster": "./raster/3318DC_clip_utm34s.tif",
```
One raster DEM will be enough for the [village/campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus) strategy. Larger areas might require more.
&nbsp;

The [districts](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts) ```"in_raster"``` parameter will accept one or many (e.g.: ```"in_raster": "./raster/LO19_050M_3418BA.tif ./raster/LO19_050M_3318DC.tif",```). `NoData` values are recommend and the workflow will mosaic where necessary, clip and project an input raster DEM to the defined crs.

#### NoData

While [village/campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus) and [districts](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts) `interactive.ipynb` should execute successfully in any area; the [CityJSON](https://www.cityjson.org/) will not when an aoi extend's into `NoData` (typically the ocean). This means [these types of areas](https://www.openstreetmap.org/relation/2034620#map=14/-33.9128/18.4430) will fail to produce a LoD1 3D City Model while [these](https://www.openstreetmap.org/way/689159965) will pass. 

### CityJSON
```json
    "cjsn_out": "./result/citjsn_cput3d.json",
    ...
    "cjsn_CleanOut": "./result/citjsnClean_cput3d.json"<!--,
    "obj-2_75D": "./result/obj275D_cput3d.obj"-->
```
The `"cjsn_out"` City Model is parsed through a basic cleaning operation to remove duplicate and orphan vertices. `"cjsn_CleanOut"` thus has no superfluous features.   

