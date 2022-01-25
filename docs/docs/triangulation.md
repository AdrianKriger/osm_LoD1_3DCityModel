---
layout: default
title: Triangulation
nav_order: 2
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

You need to verify if the building footprints have been removed from the surface. The two images illustrate an example were a specific vector had to be accounted for or the result would not be topologically correct (water-tight with no holes nor gaps).

<p align="center">
  <img src="{{site.baseurl | prepend: site.url}}/img/fp01.png" alt="alt text" width="350" height="350">  <img src="{{site.baseurl | prepend: site.url}}/img/fp02.png" alt="alt text" width="350" height="350">
</p> 
<p align="center">
    Fig 2. - left illustrates the building footprint removed from the terrain. - right shows the vertices accounted for; but the ground remains.
</p>
