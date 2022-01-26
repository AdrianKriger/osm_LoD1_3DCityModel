---
layout: default
title: osm_LoD1_3DCityModel
nav_order: 2
---

# osm_LoD1_3DCityModel
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## What does it do?

## What do I need?

## Processing Strategies

### village/campus

### district

## `param.json`

<!-- ## Restrictions and Considerations -->

### Area-of-Interest

### raster DEM

### crs

```json
"crs": "EPSG:32733",
``` 
defines the 
Coordinate Reference System (crs) of the City Model. The workflow will project the osm vector and raster DEM into a local coordinate system. [EPSG code](https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset)'s are supported.

### Timing Considerations

The advantage of `python` is its breadth, scope and utility. The disadvantage is speed. A few timing metrics are available.

**village/campus**
[university campus: 50 buildings](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/extra/osm3Dcput_param.json) runtime: 0:00:32.762952
[rural village: population 9 000](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3Dmamre_param.json) runtime: 0:16:30.662577

