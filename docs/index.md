---
layout: default
title: Home
nav_order: 1
description: "A python-based workflow for creation of Level-of-Detail 1 3D Models."
permalink: /
---

#  Level-of-Detail 1 (LoD1) 3D Models
{: .fs-9 }

[osm_LoD1_3DCityModel]() is a python-based workflow for the creation of LoD1 3D City Models (buildings and terrain) from OpenStreetMap (osm) contributions with elevation from a raster Digital Elevation Model (DEM). The workflow aims for simplicity. It takes 2D osm vector contributions (building outlines) with [`building:level`](https://wiki.openstreetmap.org/wiki/Key:building:levels) tagged and extrudes the polygon from the raster DEM (terrain). {: .fs-6 .fw-300 }

<p align="center">There are two procesing strategies</p>

| [Village/Campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus) | [District](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts)  |
| :-----: | :-----: |
| If your Area-of-Interest (aoi) has a population of 10 000 or less you are welcome to choose [village/campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus)| Please choose [District](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts) should you aoi have a population of more than 10 000|

---

**Input** a raster DEM. Script will call for the [osm contributions](https://www.openstreetmap.org/about#:~:text=OpenStreetMap%20is%20built%20by%20a,more%2C%20all%20over%20the%20world.).  
**Output** includes:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;i. a 2.75D surface mesh *(buildings connected to terrain)*;  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ii. a semantically rich LoD1 City Model *(information rich building models seperate from the ground; but when connected to the terrain   form a water-tight surface<sup>*</sup>)*; and  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;iii. an interactive .html which you can navigate and query.

<sup>*</sup> *the goal is a topologically correct surface. I have not tested this for all possibilities. If the result you achieve is not; you are welcome to raise an issue. I depend on you to help me improve.* 
