---
layout: default
title: Processing Strategies
parent: osm_LoD1_3DCityModel
nav_order: 2
---

# Processing Strategies
<!-- {: .no_toc } -->
&nbsp;

<p align="center"><b>There are two procesing strategies</b></p>

<!--| [Village/Campus](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus) | [District](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts) *[on hold]*|
| :-----: | :-----: |
| [village/campus]((https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus)) is designed for extremely focused analysis at a **neighbourhood** level. These are areas <br /> with a population of no more than 10 000| For **larger** areas with populations of more <br /> than 10 000;  one or many suburbs, census wards or tracts; please execute [districts](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts).|
| [village/campus]((https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus)) harvests [osm contributions](https://www.openstreetmap.org/about) via [overpass-turbo](https://wiki.openstreetmap.org/wiki/Overpass_turbo) in [GeoJSON](https://geojson.org/) format| With more substantial volumes of data;<br />[districts]((https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts)) extracts the necessary building outlines from the [osm.pbf format](https://wiki.openstreetmap.org/wiki/PBF_Format) (Protocolbuffer Binary Format) via [Pyrosm](https://pyrosm.readthedocs.io/en/latest/)|-->

<table>
  <tr>
    <th align="center"><a href="https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus">Village/Campus</a></th>
    <th style="background: repeating-linear-gradient(-45deg, transparent, transparent 5px, rgba(0,0,0,0.2) 5px, rgba(0,0,0,0.2) 10px); text-align: center; border: 1px solid black;"><a href="https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts">District</a> <em><strong>[This is on hold]</strong></em></th>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus">village/campus</a> is designed for extremely focused analysis at a <strong>neighbourhood</strong> level. These are areas <br /> with a population of no more than 10,000</td>
    <td style="background: repeating-linear-gradient(-45deg, transparent, transparent 5px, rgba(0,0,0,0.2) 5px, rgba(0,0,0,0.2) 10px); text-align: center; border: 1px solid black;">For <strong>larger</strong> areas with populations of more <br /> than 10,000; one or many suburbs, census wards, or tracts; please execute <a href="https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts">districts</a>.</td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/village_campus">village/campus</a> harvests <a href="https://www.openstreetmap.org/about">osm contributions</a> via <a href="https://wiki.openstreetmap.org/wiki/Overpass_turbo">overpass-turbo</a> in <a href="https://geojson.org/">GeoJSON</a> format</td>
    <td style="background: repeating-linear-gradient(-45deg, transparent, transparent 5px, rgba(0,0,0,0.2) 5px, rgba(0,0,0,0.2) 10px); text-align: center; border: 1px solid black;">With more substantial volumes of data;<br /><a href="https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts">districts</a> extracts the necessary building outlines from the <a href="https://wiki.openstreetmap.org/wiki/PBF_Format">osm.pbf format</a> (Protocolbuffer Binary Format) via <a href="https://pyrosm.readthedocs.io/en/latest/">Pyrosm</a></td>
  </tr>
</table>


<!--  Table of contents
{: .no_toc .text-delta }

<!-- |<td colspan=3><b>The reason for this is</b></td> -->
<!-- ||<b>The reason for this is</b>|| 

1. TOC
{:toc}--> 

--- 

