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

Starting with a clean slate [osm3Ddistricts_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/osm3Ddistricts_param.json) will download a country-level.osm.pbf, extract a region via `osmconvert` and a `.poly` to generate a LoD1 City Model for one census ward / tract with a population of 30 000 (1750 buildings with levels [tagged](https://wiki.openstreetmap.org/wiki/Key:building:levels)): `runtime: 0:54:25.24275`

As a direct comparison; [osm3DdistrictsCity_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/extra/osm3DdistrictsCity_param.json) will do the same via a city-level.osm.pbf, with no `trim` necessary, for the same census ward / tract: `runtime: 0:24:17.938542`

## Many Census Wards


## Many Census Wards with many raster DEM
