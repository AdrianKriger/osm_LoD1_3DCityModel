# Level-of-Detail 1 (LoD1) 3D City Model from [OpenStreetMap](https://en.wikipedia.org/wiki/OpenStreetMap) (osm) vector and raster Digital Elevation Model (dem).

<p align="center">
  <img width="700" height="40" src="img/CityJSON_Ninja_cput.pn">
</p>


#<img src="img/fp01.png" alt="alt text" width="750" height="450">
#<img src="img/CityJSON_Ninja_cput.png" alt="alt text" width="700" height="400" style=centerme>

This repository is inspired by [3dfier](https://tudelft3d.github.io/3dfier/minimal_data_requirements.html); product of the [3D geoinformation group](https://3d.bk.tudelft.nl/)  at [TUDelft](https://www.tudelft.nl/)

Its paper: `Ledoux H, Biljecki F, Dukai B, Kumar K, Peters R, Stoter J, and Commandeur T (2021). 3dfier: automatic reconstruction of 3D city models. Journal of Open Source Software, 6(57), 2866.` [![DOI](https://joss.theoj.org/papers/10.21105/joss.02866/status.svg)](https://doi.org/10.21105/joss.02866), [website](https://tudelft3d.github.io/3dfier/index.html) and [github](https://github.com/tudelft3d/3dfier) are available.

We generate a LoD1 City Model (buildings and terrain) from volunteered public data with elevation from a raster dem.

**NOTE:** *This workflow is not meant to scale.*
Requests for an extreme amount of data from the [osm](https://en.wikipedia.org/wiki/OpenStreetMap) server is destructive to the entire community. Village, Suburb and Campus analysis only please. For a larger area (city, state) consider harvesting data via `.pbf` ([geofabric](https://download.geofabrik.de/index.html) or [planet](https://planet.osm.org/)) - raise an issue and we can work on an alternate processing strategy.

Set parameters with a basic [json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json) to execute [osm3DCode](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3DCode.py) through [osm3DMain](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3DMain.py).
Output includes:
a) a 2.75D surface mesh (buildings connected to terrain);
b) a semantically rich LoD1 City Model (information rich buillding models seperate from the ground; but when connected form a water-tight surface<sup>*</sup>); and
c) an interactive .html.

If your interest is a dynamic visualization only; [interactiveOnly.ipynb](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/interactiveOnly.ipynb) will produce c) without a) and b).

<sup>*</sup> *- the goal is a topologically correct surface. I have not tested this for all possibilities. If the result you achive is not; you are welcome to raise an issue. I depend on you to help me improve.* 

Please read the Good-To-Know.
