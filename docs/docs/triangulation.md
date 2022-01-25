---
layout: default
title: Triangulation
nav_order: 3
---

# Triangulation
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Quality Checks

[PyVista](https://www.pyvista.org/) is built-in and will execute after the triangulation; before the 3D City Model is created. This is to visualize the terrain and allow the user to perform two quality checks.

### Building Footprints

It is necessary to verify whether the building footprints have been removed from the surface. The Fig. 1 illustrate an example were a specific vector had to be accounted for or the result would not be water-tight with no holes nor gaps.

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

While this workflow is released under a *---some licence here---* be aware Shewchuck's [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) may not be sold or included in commercial products without a license.
