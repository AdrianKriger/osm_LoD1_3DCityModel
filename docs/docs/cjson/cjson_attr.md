---
layout: default
title: CityJSON Attributes
parent: CityJSON
nav_order: 1
---

# CityJSON Attributes
{: .no_toc }

---

A selection of [osm tags](https://wiki.openstreetmap.org/wiki/Map_features#Building) are simply copied to the 3D Building Models verbatim; with the exception of the address. To reduce the complexty of the osm [Key:addr](https://wiki.openstreetmap.org/wiki/Key:addr#Detailed_subkeys) each component is concatenated into one [string](https://en.wikibooks.org/wiki/Python_Programming/Variables_and_Strings#String) following, as closely as possible, the [ISO 19160-1:2015(en) Addressing](https://www.iso.org/obp/ui/#iso:std:iso:19160:-1:ed-1:v1:en) standard. A typical address will thus read: `housenumber street suburb postalcode city province`. Should the building be an apartment the [unit range](https://wiki.openstreetmap.org/wiki/Key:addr:flats) will prepend the address.

<p align="center">
<img src="{{site.baseurl | prepend: site.url}}/img/CityJSON_Ninja_mamre_semantics.png" style="width: 800px; height: 400px; border: 0px">
</p>
<p align="center">
    The typical semantic data connected to the 3D City Model.
</p>
