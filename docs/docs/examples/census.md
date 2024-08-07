---
layout: default
title: Census Tract/Ward
parent: Examples
nav_order: 5
---

# Census Tract/Ward *[on hold]*
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## One Census Ward

Starting with a clean slate [osm3Ddistricts_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/osm3Ddistricts_param.json) will download a `country-level.osm.pbf`, extract a region via `osmconvert` and a `.poly` to generate a LoD1 City Model for one census ward / tract with 2550 `buildings:levels` [tagged](https://wiki.openstreetmap.org/wiki/Key:building:levels): `runtime: 1:34:21.201458`

<!-- As a direct comparison [osm3DdistrictsCity_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/extra/osm3DdistrictsCity_param.json) will do the same via a `city-level.osm.pbf`, with no `trim` necessary, for the same census ward / tract with 1390 `buildings:levels` [tagged](https://wiki.openstreetmap.org/wiki/Key:building:levels): `runtime: 0:38:40.708790`.

 Geofabrik generates fresh extracts daily. BBBike ---*where this particular city-level.osm.pbf was harvested from*--- less frequently. -->
Similarly *(`country-level.osm.pbf` to region via `osmconvert` and a `.poly`)* [districts interactiveOnly.ipynb](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/interactiveOnly.ipynb) will produce a dynamic `.html`. 

## Many Census Wards with many raster DEM

[osm3DdistrictsKaya_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/extra/osm3DdistrictsKaya_param.json) combines the 12 adjacent census wards / tracts of [Khayelitsha](https://en.wikipedia.org/wiki/Khayelitsha) along with the mosaic, clip and reprojection of 2 raster DEM.

The `param.json` will use an existing `.osm.pbf` (the `extract.osm.pbf` created in the previous, **One Census Ward**, example: `"CapeTown-extract.osm.pbf"`). `runtime` is at `0:08:00.895749` due to the low number of [building:level](https://wiki.openstreetmap.org/wiki/Key:building:levels) tags (57 buildings). 

With the same rationale; [interactiveOnlyMany.ipynb](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/extra/interactiveOnlyMany.ipynb) will reuse an `-extract.osm.pbf` and harvest more than one adjacent [`boundary=administrative`](https://wiki.openstreetmap.org/wiki/Tag:boundary%3Dadministrative).

## Extra

Its possible to `trim` a different region from the same `country-level.osm.pbf` (as **One Census Ward**) with a different `.poly`. [osm3DdistrictsTshwane_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/extra/osm3DdistrictsTshwane_param.json). `runtime: 0:06:20.492880` to produce a LoD1 City Model of one census ward / tract; 32 `buildings:levels` [tagged](https://wiki.openstreetmap.org/wiki/Key:building:levels) in another part of a country.
