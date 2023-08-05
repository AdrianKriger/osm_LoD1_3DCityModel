---
layout: default
title: Triangulation
nav_order: 3
---

# Triangulation
{: .no_toc }  

The 3D Model is based on a [triangulated irregular network](https://en.wikipedia.org/wiki/Triangulated_irregular_network) (TIN) data-structure. A TIN is a collection of connected 3D triangles that form a continuous closed surface. [`osm_LoD1_3DCityModel`](https://github.com/AdrianKriger/osm_LoD1_3DCityModel) creates a TIN with Jonathan Richard Shewchuk's [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) and uses a special algorithm called a [Constrained Delaunay triangulation](https://en.wikipedia.org/wiki/Constrained_Delaunay_triangulation).  
&nbsp;&nbsp;

<figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/fp01.png" alt="alt text" width="450" height="250">
  <figcaption>Fig.1 - illustrates the typical constrained Delaunay triangulation with holes (buildings) removed. _Note: courtyards remain._</figcaption>
</center></figure> 

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Quality Checks

<!--[PyVista](https://www.pyvista.org/) is built-in and will execute after the triangulation; before the 3D City Model is created. This is to visualize the terrain and allow the user to perform two quality checks.-->

<!--### Building Footprints-->

Before a City Model is created the user will be presented with a basic `matplotlib` figure *[saved to the `data folder`]* and a choice; to iether continue (with `Enter`) or exit (with `Esc`).  Topological errors *(crossing buildings)* are highlight and the user is encouraged to fix the challanges at the source. i.e.: [edit OpenStreetMap](https://www.openstreetmap.org/about).

<!-- <p align="center">
  <img src="{{site.baseurl | prepend: site.url}}/img/ue.png" alt="alt text" width="350" height="350">  <img src="{{site.baseurl | prepend: site.url}}/img/ue-error.png" alt="alt text" width="350" height="350">
</p> 
<p align="center">
    Fig 2. - left illustrates an area with no topological challenges . - right shows the same area with errors that need investigation.
</p> --> 
 <figure><center>
  <img src="{{site.baseurl | prepend: site.url}}/img/ue.png" alt="alt text" width="350" height="350">  <img src="{{site.baseurl | prepend: site.url}}/img/ue-error.png" alt="alt text" width="350" height="350">
  <figcaption>Fig 2. - left illustrates an area with no topological challenges . - right shows the same area with errors that need investigation.</figcaption>
</center></figure>

<!--### Spikes

An additional quality check is for a spike or two. Generally the root of this challenge are buildings crossing each other ~ Fig.2. The [constrained Delaunay triangulation](https://rufat.be/triangle/definitions.html) knows there are lines (walls) and expects a vertex where they intersect. There is none and the result is a spike. **Open an [osm editor](https://wiki.openstreetmap.org/wiki/Editors) and correct the topology please**. *We are transforming volunteered public data into a value-added product. Alchemy is a process. Please be patient.<sup>*</sup>*

<p align="center">
  <img src="{{site.baseurl | prepend: site.url}}/img/sp01.png" alt="alt text" width="350" height="250">  <img src="{{site.baseurl | prepend: site.url}}/img/sp02.png" alt="alt text" width="350" height="250">
</p> 
<p align="center">
    Fig 2. - left illustrates a spike. - right traces the challenge to the root.
</p>
-->
<sup>* ***if [osm_LoD1_3DCityModel](https://github.com/AdrianKriger/osm_LoD1_3DCityModel) completely fails in your area have a look at [osm_LoD13DCityModel Walkthorugh](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/extra/osm_LoD13DCityModel-walkthrough.ipynb).***

## Licencing

While this workflow is released under an [MIT Licence](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/LICENSE.txt) be aware Shewchuck's [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) may not be sold or included in commercial products without a license. <!-- [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) is freely available but I cannot give it to you. I can tell you about it and where to find it but I cannot include it in a package. Like PenStreetMap it requires you to act, to participate. -->
