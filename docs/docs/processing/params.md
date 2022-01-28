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

#### district

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
The [districts](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts) ```"in_raster"``` parameter will accept one or many (e.g.: ```"in_raster": "./raster/LO19_050M_3418BA.tif ./raster/LO19_050M_3318DC.tif",```). NoData values are recommend and the workflow will mosaic where necessary, clip and project an input raster DEM to the defined crs.


