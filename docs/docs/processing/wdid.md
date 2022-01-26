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

An extremely well documented way of producing 3D Models is through extrusion. With extrusion; 2D features are *lifted* from an existing surface creating a volumetric 3D object. osm_LoD1_3DCityModel inferes the height with which to *lift* 2D features from osm contributions. 

The osm tag `building:level` is taken as a [proxy for the height of a building](https://wiki.openstreetmap.org/wiki/Key:building:levels). The calculation is simply `building:level * 2.8 + 1.3`. If a structure does not have a `building:level` tag no LoD1 model is created.
 &nbsp; &nbsp;

<p align="center">
  <img src="{{site.baseurl | prepend: site.url}}/img/extrusion_tuDelft.png" alt="alt text" width="650" height="350">
</p> 
<p align="center">
    Fig 1. The osm_LoD1_3DCityModel process. --image TUDelft.
</p>

Fig 1 illustrates the process where the osm *proxy `building:level` height*  is added to the raster DEM to create a 3D topologically connected surface ~ containing all 2D polygons as 3D objects.

The resulting LoD1 City Model, while basic, offers many advantages over 2D datasets. These may be used for shadow analyses, line of sight predictions and advanced flood simulation. Challenges do exist. Of primary concern is errors in the source data that propagate to the generated 3D model. Care must be taken to ensure the quality of both the vector building outlines and raster DEM.

## osm_LoD1_3DCityModel output
&nbsp;&nbsp;
osm_LoD1_3DCityModel creates two products:

### Trianglated MultiSurfaces

MultiSurface outputs are the walls and roof's of buildings, along with the terrain surface, as a connected collection of triangles. These are created in the 2.75D Wavefront OBJ format. 

### Solids

Solid objects are walls and roof's stored as rectangular surfaces. In the CityJSON format these are seperate Building and TINRelief CityObjects that enabling spatial analyses and the structuring of objects.
