---
layout: default
title: Census Tract/Ward
parent: Examples
nav_order: 5
---

# Census Tract/Ward
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## One Census Ward

Starting with a clean slate at a country-level [osm3Ddistricts_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/osm3Ddistricts_param.json) will download an osm.pbf, extract a region via `osmconvert` and a `.poly` to generate a LoD1 City Model for one census ward / tract with a population of 30 000 (1750 buildings with levels [tagged](https://wiki.openstreetmap.org/wiki/Key:building:levels)): `runtime: 0:54:25.24275`

A direct comparison with a city-level.pbf of the same census ward / tract: 

## Many Census Wards

## Many Census Wards with many raster DEM
