---
layout: default
title: Attributes
parent: CityJSON
nav_order: 1
---

# CityJSON Attributes
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Address
<!-- {: .d-inline-block } -->

A selection of [osm tags](https://wiki.openstreetmap.org/wiki/Map_features#Building) are simply copied to the 3D Building Models verbatim; with the exception of the address. To reduce the complexty of the osm [Key:addr](https://wiki.openstreetmap.org/wiki/Key:addr#Detailed_subkeys) each component is concatenated into one [string](https://en.wikibooks.org/wiki/Python_Programming/Variables_and_Strings#String) following, as closely as possible, the [ISO 19160-1:2015(en) Addressing](https://www.iso.org/obp/ui/#iso:std:iso:19160:-1:ed-1:v1:en) standard. A typical address will thus read: `housenumber street suburb postalcode city province`. If the [Key:addr:flats](https://wiki.openstreetmap.org/wiki/Key:addr:flats) is present the unit range will prepend the address.

<p align="center">
<img src="{{site.baseurl | prepend: site.url}}/img/CityJSON_Ninja_mamre_semantics.png" style="width: 650px; height: 350px; border: 0px">
</p>
<p align="center">
    The typical semantic data connected to the 3D City Model.
</p>

## Google Plus Codes

Google ['plus codes'](https://maps.google.com/pluscodes/) are included at a precision of [11 characters - 3.5-meter block size](https://en.wikipedia.org/wiki/Open_Location_Code) (e.g. 4FRW3J9R+892Q); referenced to the [`representative_point()`](https://shapely.readthedocs.io/en/stable/manual.html) of buildings.
