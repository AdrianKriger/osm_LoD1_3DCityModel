# Good-To-Know

<ins>**Parameters:**</ins>  
a) Area-of-interest (aoi) is defined `Large area -> focus area` or `State (Province) -> village / campus`.    
b) Your aoi must exist in osm as either a [way or relation](https://wiki.openstreetmap.org/wiki/Elements); and the type must explicitly be [set](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3Dmamre_param.json#L4).  
c) Define [metadata](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3Dmamre_param.json#L22-L32) for the City Model. Without it the dataset has no value.  [CityJSON Specifications](https://www.cityjson.org/specs/1.1.0/#metadata) are pretty comprehensive.  
d) Create a dynamic .html with [interactiveOnly](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/interactiveOnly.ipynb). The [Jupyter](https://jupyter.org/) environment allows for easy customization of the final product. The static png below (Fig 1.) illustrates building stock differentiated through color. A school, housing, retail, healthcare and community focused facilities are easily identified. Additional features unique to an aoi can also be included. Here farmland, streams, recreational spaces and bus rapid transit routes have been added *- you are thus limited only through data and your imagination*. The interactive version can be found [here](https://adriankriger.github.io/osm_LoD1_3DCityModel/docs/interactive/).

<p align="center">
  <img width="650" height="350" src="img/interactive.png">
</p>  
<p align="center">
    Fig 1. An example of how the interactive visualization can be customized through coloring the building stock (school, retail, housing, social development facilities, etc.) and including aoi specific features (recreational ground, agricultural land, etc.).
</p>

e) While [interactiveOnly](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/interactiveOnly.ipynb) should execute successfully in any area; the [CityJSON](https://www.cityjson.org/) will not when an aoi extend's into NoData (typically the ocean). This means [these types of areas](https://www.openstreetmap.org/relation/2034620#map=14/-33.9128/18.4430) will fail to produce a LoD1 3D City Model while [these](https://www.openstreetmap.org/way/689159965) will pass.

<ins>**Accuracy:**</ins>  
dem - in South Africa if you are using the [National geo-spatial information](http://www.ngi.gov.za/) raster dem the [resolution is 25-m at 3-m accurate](https://www.ee.co.za/wp-content/uploads/2015/08/Julie-Verhulp.pdf).  
vector - A [snap routine](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3DCode.py#L283-L290) reduces the number of vertices within 0.2-m on the osm vector layer. 

<ins>**Precision:**</ins>  
I've chosen to process in Universal Transverse Mercator 33 South. You can choose another [crs](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3Dmamre_param.json#L15). Be aware a floating-point precision error might arise.

<ins>**Building Heights:**</ins>  
The osm tag `building:level` is taken as a [proxy for the height of a building](https://wiki.openstreetmap.org/wiki/Key:building:levels). The calculation is simply `building:level * 2.8 + 1.3`. If a structure does not have a `building:level` tag no LoD1 model is created. Vector data is through [&copy; OpenStreetMap contributors](https://www.openstreetmap.org/copyright). All data from OpenStreetMap is licensed under the [OpenStreetMap License](https://wiki.osmfoundation.org/wiki/Licence).

<ins>**Raster dem:**</ins>  
a) The [osm3Dcput_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/extra/osm3Dcput_param.json#L15) defines the raster I used in the example. [osm3Dmamre_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3Dmamre_param.json#L15) defines another. These datasets, and more, are available from the [CD:NGI Geoportal](http://www.ngi.gov.za/index.php/online-shop/what-is-itis-portal); State copyright reserved. The Chief Directorate: National Geospatial Information is a branch of the [Department Rural Development and Land Reform](https://www.drdlr.gov.za/sites/Internet/Branches/NationalGeomaticsAndManagementServices/Pages/National-Geo-Spatial-Information.aspx) and is a key contributor to the [South African Spatial Data Infrustructure](http://www.sasdi.gov.za/sites/SASDI/Pages/Home.aspx).  
b) The script handles the projection and clipping to an aoi. If your focus area falls on the boundary of two raster sheets perhaps the [Districts](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/tree/main/districts) processing strategy is better.  

<ins>**Triangulation:**</ins>  
a) [PyVista](https://www.pyvista.org/) is [built-in](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3DCode.py#L498-L524) and will execute after the triangulation; before the 3D City Model is created. This is to visualize the terrain. I have left [line 298 of osm3DCode](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3DCode.py#L292-L298) as an aid.
You need to verify if the building footprints have been removed from the surface. The two images illustrate an example were a specific vector had to be accounted for or the result would not be topologically correct (water-tight with no holes nor gaps).

<p align="center">
  <img src="img/fp01.png" alt="alt text" width="350" height="350">  <img src="img/fp02.png" alt="alt text" width="350" height="350">
</p> 
<p align="center">
    Fig 2. - left illustrates the building footprint removed from the terrain. - right shows the vertices accounted for; but the ground remains.
</p>

b) Please see [Districts](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/districts/Good-To-Know.md) for an additional quality check.  
c) Shewchuck's [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) may not be sold or included in commercial products without a license.  

<ins>**CityJSON attributes:**</ins>  
a) [osm tags](https://wiki.openstreetmap.org/wiki/Map_features#Building) are simply copied to the 3D Building Models verbatim; with the exception of the address. To reduce the complexty of the [Key:addr](https://wiki.openstreetmap.org/wiki/Key:addr#Detailed_subkeys) each component is concatenated into one [string](https://en.wikibooks.org/wiki/Python_Programming/Variables_and_Strings#String) following, as closely as possible, the [ISO 19160-1:2015(en) Addressing](https://www.iso.org/obp/ui/#iso:std:iso:19160:-1:ed-1:v1:en) standard. A typical address will thus read: `housenumber street suburb postalcode city province`. Should the building be an apartment the [unit range](https://wiki.openstreetmap.org/wiki/Key:addr:flats) will prepend the address.  
The [code](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/osm3DCode.py#L188-L205) can easily be extended to meet your specific needs. no osm tag = no attribute.  
b) Google ['plus codes'](https://maps.google.com/pluscodes/) are included at a precision of [11 characters - 3.5-meter block size](https://en.wikipedia.org/wiki/Open_Location_Code) (e.g. 4FRW3J9R+892Q); referenced to the [`representative_point()`](https://shapely.readthedocs.io/en/stable/manual.html) of buildings. - in Fig 2. this would be the red dot.  
c) Fig. 3 illustrates the typical semantic data connected to the 3D City Model. *Visualization: [ninja](https://ninja.cityjson.org/#)*

<p align="center">
  <img width="650" height="350" src="img/CityJSON_Ninja_mamre_semantics.png">
</p>  
<p align="center">
    Fig 3. An example of the CityJSON attributes. 
</p>

<ins>**Alternatives:**</ins>  
[BlenderGIS](https://github.com/domlysz/BlenderGIS) and [QGIS](https://qgis.org/en/site/) offers some (if not all and more) of this functionality.

<ins>**[The Penultimate Truth:](https://en.wikipedia.org/wiki/The_Penultimate_Truth)**</ins>  
Its not very efficient.

<ins>**Lastly:**</ins>  
Please don't burden the osm server with requests for an extreme amount of data.
