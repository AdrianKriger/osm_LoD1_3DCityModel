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

### raster DEM

### crs

```json
"crs": "EPSG:32733",
``` 
defines the 
Coordinate Reference System (crs) of the City Model. The workflow will project the osm vector and raster DEM into a local coordinate system. [EPSG code](https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset)'s are supported.
