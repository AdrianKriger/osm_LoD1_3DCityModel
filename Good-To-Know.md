# Good-To-Know

**Parameters:**  
a) Area-of-interest (aoi) is defined `Large area -> focus area` or `State (Province) -> village / campus`.    
b) Your aoi must exist in osm as either a [way or relation](https://wiki.openstreetmap.org/wiki/Elements); and the type must explicitly be [set](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L4).  
c) Define [metadata](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L22-L30) for the City Model. Without it the dataset has no value.    
d) Although interactive is set to ['True'](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L34); I recommend 'False'. Create the .html with [interactiveOnly](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/interactiveOnly.ipynb). The [Jupyter](https://jupyter.org/) environment allows for easy customization of the final product. The static png below illustrates building stock differentiated through color. A school, housing, retail, healthcare and community focused facilities are easily identified. Additional features unique to an aoi can also be included. Here farmland, streams and recreational spaces have been added *- you are thus limited only through data and your imagination*.

<p align="center">
  <img width="650" height="350" src="img/interactive.png">
</p>  
<p align="center">
    Fig 1. An example of how the interactive visualization can be customized through coloring the building stock (school, retail, housing, social development facilities, etc.) and including aoi specific features (recreational ground, agricultural land. etc.).
</p>

**Accuracy:**  
dem - in South Africa if you are using the [National geo-spatial information](http://www.ngi.gov.za/) raster dem the [resolution is 25-m at 3-m accurate](https://www.ee.co.za/wp-content/uploads/2015/08/Julie-Verhulp.pdf).  
vector - A [snap routine](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3DCode.py#L231-L238) reduces the number of vertices within 0.2-m on the osm vector layer. 

**Precision:**  
I've chosen to process in Universal Transverse Mercator. You can choose another [crs](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L6). Be aware a floating-point precision error might arise.

**Building Heights:**  
The osm tag `building:level` is taken as a [proxy for the height of a building](https://wiki.openstreetmap.org/wiki/Key:building:levels). The calculation is simply `building:level * 2.8 + 1.3`. If a structure does not have a `building:level` tag no LoD1 model is created. Vector data is through [&copy; OpenStreetMap contributors](https://www.openstreetmap.org/copyright). All data from OpenStreetMap is licensed under the [OpenStreetMap License](https://wiki.osmfoundation.org/wiki/Licence).

**Raster dem:**  
a) The [osm3Dcput_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L15) defines the raster I used in the example. [osm3Dmamre_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/extra/osm3Dmamre_param.json#L15) defines another. These datasets, and more, are available from the [CD:NGI Geoportal](http://www.ngi.gov.za/index.php/online-shop/what-is-itis-portal); State copyright reserved. The Chief Directorate: National Geospatial Information is a branch of the [Department Rural Development and Land Reform](https://www.drdlr.gov.za/sites/Internet/Branches/NationalGeomaticsAndManagementServices/Pages/National-Geo-Spatial-Information.aspx) and is a key contributor to the [South African Spatial Data Infrustructure](http://www.sasdi.gov.za/sites/SASDI/Pages/Home.aspx).  
b) The script handles the projection and clipping to an aoi. If your focus area falls on the boundary of two raster sheets - you are welcome to raise an issue so we can expand the functionality to `glob` a folder, reproject, **merge**, clip and continue. Bear in mind the **NOTE.**

**Triangulation:**  
a) [PyVista](https://www.pyvista.org/) is [built-in](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3DCode.py#L440-L466) and will execute after the triangulation; before the 3D City Model is created. This is to visualize the terrain. I have left [line 242 of osm3DCode](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3DCode.py#L242) as an aid.
You need to verify if the building footprints have been removed from the surface. The two images illustrate an example were a specific vector had to be accounted for or the result would not be topologically correct (water-tight with no holes nor gaps).

<p align="center">
  <img src="img/fp01.png" alt="alt text" width="250" height="250">  <img src="img/fp02.png" alt="alt text" width="250" height="250">
</p> 
<p align="center">
    Fig 2. - left illustrates the building footprint removed from the terrain. - right shows the vertices accounted for; but the ground remains.
</p>

b) Shewchuck's [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) may not be sold or included in commercial products without a license.  

**CityJSON attributes:**  
[osm tags](https://wiki.openstreetmap.org/wiki/Map_features#Building) are simply copied to the 3D Building Models verbatim; with the exception of the address. To reduce the complexty of the [Key:addr](https://wiki.openstreetmap.org/wiki/Key:addr#Detailed_subkeys) each component is concatenated into one string following the [ISO 19160-1:2015(en) Addressing](https://www.iso.org/obp/ui/#iso:std:iso:19160:-1:ed-1:v1:en) standard. A typical address will thus read:  
`housenumber street suburb postalcode city province`. Should the building be an apartment the [unit range](https://wiki.openstreetmap.org/wiki/Key:addr:flats) will prepend the address.  
no tag = no attribute. 

**Alternatives:**  
[BlenderGIS](https://github.com/domlysz/BlenderGIS) and [QGIS](https://qgis.org/en/site/) offers some (if not all and more) of this functionality.

**[The Penultimate Truth:](https://en.wikipedia.org/wiki/The_Penultimate_Truth)**  
Its not very efficient.

**Lastly:**  
Please don't burden the osm server with requests for an extreme amount of data.
