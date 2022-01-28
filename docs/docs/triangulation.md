---
layout: default
title: Triangulation
nav_order: 3
---

# Triangulation
{: .no_toc }  

The 3D Model is based on a [triangulated irregular network](https://en.wikipedia.org/wiki/Triangulated_irregular_network) (TIN) data-structure. A TIN is a collection of connected 3D triangles that form a continuous closed surface. [`osm_LoD1_3DCityModel`](https://github.com/AdrianKriger/osm_LoD1_3DCityModel) creates a TIN with Jonathan Richard Shewchuk's [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) and uses a special algorithm called a [Constrained Delaunay triangulation](https://en.wikipedia.org/wiki/Constrained_Delaunay_triangulation).  
&nbsp;&nbsp;

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Quality Checks

[PyVista](https://www.pyvista.org/) is built-in and will execute after the triangulation; before the 3D City Model is created. This is to visualize the terrain and allow the user to perform two quality checks.

### Building Footprints

It is necessary to verify whether the building footprints have been removed from the surface. Fig. 1 illustrate an example were a specific vector had to be accounted for or the result would not be water-tight with no holes nor gaps.

<p align="center">
  <img src="{{site.baseurl | prepend: site.url}}/img/fp01.png" alt="alt text" width="350" height="350">  <img src="{{site.baseurl | prepend: site.url}}/img/fp02.png" alt="alt text" width="350" height="350">
</p> 
<p align="center">
    Fig 1. - left illustrates the building footprint removed from the terrain. - right shows the vertices accounted for; but the ground remains.
</p>


### Spikes

An additional quality check is for a spike or two. Generally the root of this challenge are buildings crossing each other ~ Fig.2. The [constrained Delaunay triangulation](https://rufat.be/triangle/definitions.html) knows there are lines (walls) and expects a vertex where they intersect. There is none and the result is a spike. **Open an [osm editor](https://wiki.openstreetmap.org/wiki/Editors) and correct the topology please**. *We are transforming volunteered public data into a value-added product. Alchemy is a process. Please be patient.*

<p align="center">
  <img src="{{site.baseurl | prepend: site.url}}/img/sp01.png" alt="alt text" width="350" height="250">  <img src="{{site.baseurl | prepend: site.url}}/img/sp02.png" alt="alt text" width="350" height="250">
</p> 
<p align="center">
    Fig 2. - left illustrates a spike. - right traces the challenge to the root.
</p>

## Licencing

While this workflow is released under a *---some licence here---* be aware Shewchuck's [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) may not be sold or included in commercial products without a license. <!-- [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) is freely available but I cannot give it to you. I can tell you about it and where to find it but I cannot include it in a package. Like PenStreetMap it requires you to act, to participate. -->
