LOD1 3D City Model from [osm.pbf](https://wiki.openstreetmap.org/wiki/PBF_Format) via [pyrosm](https://pyrosm.readthedocs.io/en/latest/) with elevation from a raster DEM.

**Please use this workflow should you Area-of-Interest have a population of more than 10 000.**

Set parameters with a basic [json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/osm3Ddistricts_param.json) to execute [osm3DCodeDistricts](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/osm3DCodeDistricts.py) through [osm3DMainDistricts](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/osm3DMainDistricts.py). A dynamic visualization is possible with [interactiveOnly](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/interactiveOnly.ipynb)

Please read the [Good-To-Know](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/Good-To-Know.md).
&nbsp;

&nbsp;

*use with caution; I am experiencing challenges handeling exceptions (buildings as nodes, without tags, etc. ~ [issue #8](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/issues/8)) and haven't been able to properly put this through its paces:  
06-01-2022*
