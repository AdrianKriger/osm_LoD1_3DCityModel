---
layout: default
title: What do I need?
parent: osm_LoD1_3DCityModel
nav_order: 3
---

# What do I need?
<!-- {: .no_toc } -->

A necessary ingredient is a raster Digital Elevation/Terrain Model. (DEM/DTM).

Hereafter; depending of the processing strategy chosen the needs are slightly different. 

| [Village/Campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus) | [District](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts)  |
| :-----: | :-----: |
|With the [Village/Campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus) strategy nothing more than the raster DEM is necessary. osm_LoD1_3DModel will call overpass for the osm contributions| Due to the substantial amounts of data in the osm.pbf extract; [districts]((https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts)) requires a bit more.<br />&nbsp; 
osm_LoD1_3DModel uses [osmconvert](https://wiki.openstreetmap.org/wiki/Osmconvert) to make the osm.pbf more manageable. <br />It does this through selecting only the data from a specific area. [osm.poly](https://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format) files, that cover varies regions around the world, <br />are available for this very purpose.|



<!-- ## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc} -->

---
