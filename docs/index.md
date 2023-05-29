---
layout: default
title: Home
nav_order: 1
description: "A python-based workflow for creation of Level-of-Detail 1 3D City Models."
permalink: /
---

# Level-of-Detail 1 (LoD1) 3D City Models
{: .fs-9 }

[`osm_LoD1_3DCityModel`](https://github.com/AdrianKriger/osm_LoD1_3DCityModel) is a [python-based](https://en.wikipedia.org/wiki/Python_(programming_language)) workflow for the creation of LoD1 3D City Models (buildings and terrain) from [OpenStreetMap (osm) contributions](https://www.openstreetmap.org/about) with elevation from a raster Digital Elevation Model (DEM). The workflow aims for simplicity.  

It takes 2D osm vector contributions (building outlines) with [`building:level`](https://wiki.openstreetmap.org/wiki/Key:building:levels) tagged and extrudes the polygon from the DEM (terrain).

 <figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/CityJSON_Ninja_cputb.png" style="width: 800px; height: 400px; border: 0px">
  <figcaption>Fig.1 - LoD1 3D Model of the Cape Peninsula University of Technology (Bellville Campus). <em>---streets are in the pipeline; see <cite><a href="https://github.com/AdrianKriger/osm_LoD1_3DCityModel/issues/17"> issue #17</a></cite></em></figcaption>
</center></figure> 
<!-- <p align="center">
<img src="{{site.baseurl | prepend: site.url}}/img/CityJSON_Ninja_cput.png" style="width: 800px; height: 400px; border: 0px">
</p>
<p align="center">
    LoD1 3D Model of the Cape Peninsula University of Technology (Bellville Campus).
</p>
&nbsp;&nbsp;--> 

<p align="center"><b>There are two procesing strategies</b></p>

| [Village/Campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus) | [District](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts)  |
| :-----: | :-----: |
| If your Area-of-Interest (aoi) has a population of 10 000 or less you are welcome to choose [village/campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus)| Please choose [District](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts) should you aoi have a population of more than 10 000|

---

The purpose of this work is to provide resource constrained communities with an array of high-quality 3D products---at a much lower cost. Its participatory nature seeks to enable effective communication, community advocacy and facilitate broadly-based decision-making processes at a grassroots level. The tool can also be customized to meet basic education (citizen science, geography and coding) needs. Please see the [Discussion](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/discussions/22).

---

**Input** a raster DEM. Script will call for the [osm contributions](https://www.openstreetmap.org/about#:~:text=OpenStreetMap%20is%20built%20by%20a,more%2C%20all%20over%20the%20world.).  
**Output** includes:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;i. a 2.75D surface mesh *(buildings connected to terrain)*;  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ii. a semantically rich LoD1 City Model *(information rich building models seperate from the ground; but when connected to the terrain   form a water-tight surface<sup>*</sup>)*; and  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;iii. an interactive .html which you can navigate and query.

<sup>* ***the goal is a topologically correct surface. I have not tested this for all possibilities. If the result you achieve is not; you are welcome to raise an [issue](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/issues). I depend on you to help me improve.*** 
