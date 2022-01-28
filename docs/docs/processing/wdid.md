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

An extremely well documented method of producing 3D Models is through extrusion. With extrusion; 2D features are *lifted*{: style="color: red; opacity: 0.80" } from an existing surface creating a volumetric 3D object.  <code><b>osm_LoD1_3DCityModel</b></code> inferes the height with which to *lift*{: style="color: red; opacity: 0.80" } 2D features from osm contributions. 

The osm tag `building:level` is taken as a [proxy for the height of a building](https://wiki.openstreetmap.org/wiki/Key:building:levels). The calculation is simply `building:level * 2.8 + 1.3`. If a structure does not have a `building:level` tag no LoD1 model is created.
 &nbsp; &nbsp;
 <figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/extrusion_tuDelft.png" alt="alt text" width="650" height="350">
  <figcaption>Fig.1 - <code><b>The osm_LoD1_3DCityModel</b></code> process. <span style="color:blue;opacity:0.8;"><em>--image TUDelft</em></span>.</figcaption>
</center></figure>
<!--
<p align="center">
  <img src="{{site.baseurl | prepend: site.url}}/img/extrusion_tuDelft.png" alt="alt text" width="650" height="350">
 </p> 
<p align="center"> 
    Fig 1. The osm_LoD1_3DCityModel process. <span style="color:blue"><em>--image TUDelft</em></span>.
</p> -->

Fig 1 illustrates the process where the osm *proxy `building:level` height*  is added to the raster DEM to create a 3D topologically connected surface ~ containing 2D polygons as 3D objects.

### Is it useful?

The LoD1 City Model, while basic, offers many advantages over 2D datasets. These may be used for shadow analyses, line of sight predictions and advanced flood simulation. With the coming revolution in air traffic control, to accomodate newer forms of air services (delivery drones and urban air mobility), an accurate *digital* representation of the built environment will become crucial. A 3D City Model is one component for the effective air space management of the future.

Challenges do exist. Of primary concern are errors in the source data that propagate to the generated 3D model. Care must be taken to ensure the quality of both the vector building outlines and raster DEM.

## `osm_LoD1_3DCityModel` products

### Trianglated MultiSurfaces

MultiSurface outputs are the walls and rooves of buildings, along with the terrain, as a collection of connected triangles. This surface is created in the [Wavefront OBJ](https://en.wikipedia.org/wiki/Wavefront_.obj_file) format. 

<figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/objects_horizontal_view_multisurface_tuDelft.png" alt="alt text" width="650" height="350">
  <figcaption>Fig.2 - illustrates a horizontal view of the 2.75D surface with the exterior of all features together. <span style="color:blue;opacity:0.8;"><em>--image TUDelft</em></span>.</figcaption>
</center></figure>   

### Solids

Solid objects are walls and rooves stored as rectangular surfaces. In the [CityJSON](https://www.cityjson.org/) format these are seperate [Building](https://www.cityjson.org/specs/1.0.1/#building) and [TINRelief](https://www.cityjson.org/specs/1.0.1/#tinrelief) [CityObjects](https://www.cityjson.org/specs/1.0.1/#cityjson-object) that enabling spatial analyses.

<figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/objects_horizontal_view_solid_tuDelft.png" alt="alt text" width="650" height="350">
  <figcaption>Fig.3 - solid Building CityObjects's connected to the terrain. <span style="color:blue;opacity:0.8;"><em>--image TUDelft</em></span>.</figcaption>
</center></figure>

### Interactive Visualisation

A dynamic visualisation is possible through a Jupyter notebook. [Interactive Visualization](https://adriankriger.github.io/osm_LoD1_3DCityModel/docs/interactive/) discusses this further.

