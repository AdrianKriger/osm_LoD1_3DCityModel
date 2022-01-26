---
layout: default
title: What does it do?
parent: osm_LoD1_3DCityModel
nav_order: 1
---

# What does it do?
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Extrusion

An extremely well documented way of producing 3D Models is through extrusion. With extrusion; 2D features are *lifted*{: style="color: red; opacity: 0.80" } from an existing surface creating a volumetric 3D object. **`osm_LoD1_3DCityModel`** inferes the height with which to *lift*{: style="color: red; opacity: 0.80" } 2D features from osm contributions. 

The osm tag `building:level` is taken as a [proxy for the height of a building](https://wiki.openstreetmap.org/wiki/Key:building:levels). The calculation is simply `building:level * 2.8 + 1.3`. If a structure does not have a `building:level` tag no LoD1 model is created.
 &nbsp; &nbsp;
 <figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/extrusion_tuDelft.png" alt="alt text" width="650" height="350">
  <figcaption>Fig.1 - <code><b>The osm_LoD1_3DCityModel</code></b> process. <span style="color:blue;opacity:0.8;"><em>--image TUDelft</em></span>.</figcaption>
</center></figure>
<!--
<p align="center">
  <img src="{{site.baseurl | prepend: site.url}}/img/extrusion_tuDelft.png" alt="alt text" width="650" height="350">
 </p> 
<p align="center"> 
    Fig 1. The osm_LoD1_3DCityModel process. <span style="color:blue"><em>--image TUDelft</em></span>.
</p> -->

Fig 1 illustrates the process where the osm *proxy `building:level` height*  is added to the raster DEM to create a 3D topologically connected surface ~ containing 2D polygons as 3D objects.

The resulting LoD1 City Model, while basic, offers many advantages over 2D datasets. These may be used for shadow analyses, line of sight predictions and advanced flood simulation. Challenges do exist. Of primary concern are errors in the source data that propagate to the generated 3D model. Care must be taken to ensure the quality of both the vector building outlines and raster DEM.

## osm_LoD1_3DCityModel products

### Trianglated MultiSurfaces

MultiSurface outputs are the walls and rooves of buildings, along with the terrain surface, as a connected collection of triangles. These are created in the 2.75D Wavefront OBJ format. 

<figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/objects_horizontal_view_multisurface_tuDelft.png" alt="alt text" width="650" height="350">
  <figcaption>Fig.2 - illustrates a horizontal view of the 2.75D surface with the exterior of all objects/features together. <span style="color:blue;opacity:0.8;"><em>--image TUDelft</em></span>.</figcaption>
</center></figure>

### Solids

Solid objects are walls and rooves stored as rectangular surfaces. In the [CityJSON](https://www.cityjson.org/) format these are seperate [Building](https://www.cityjson.org/specs/1.0.1/#building) and [TINRelief](https://www.cityjson.org/specs/1.0.1/#tinrelief) [CityObjects](https://www.cityjson.org/specs/1.0.1/#cityjson-object) that enabling spatial analyses.

<figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/objects_horizontal_view_solid_tuDelft.png" alt="alt text" width="650" height="350">
  <figcaption>Fig.3 - solid Building CityObjects's connected to the terrain. <span style="color:blue;opacity:0.8;"><em>--image TUDelft</em></span>.</figcaption>
</center></figure>
