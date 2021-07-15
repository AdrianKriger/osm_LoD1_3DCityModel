# Good-To-Know

**Parameters:**  
a) Area-of-interest (aoi) is defined `Large area -> focus area` or `State (Province) -> village / suburb`;  
b) Your aoi must be exist in osm as either a [way or relation](https://wiki.openstreetmap.org/wiki/Elements); and the type must explicitly be [set](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L4);  
c) Set [metadata](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L21-L31) for the City Model. Without is the dataset has no value; and  
d) Although interactive is set to ['True'](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L33); I recommend 'False'. Create the .html with [interactiveOnly](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/interactiveOnly.ipynb). This allows for greater control to include additional features unique to your aoi.

**Accuracy**  
dem - in South Africa if you are using the [National geo-spatial information](http://www.ngi.gov.za/) raster dem the [resolution is 25-m with at 3-m accurate](https://www.ee.co.za/wp-content/uploads/2015/08/Julie-Verhulp.pdf).  
vector - A [snap routine](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3DCode.py#L231-L238) reduces the number of vertices within 0.2-m on the osm vector layer. 

**Precision**  
Processing is executed in Universal Transverse Mercator. You can choose the [zone](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L6). Be aware a floating-point precision error might arise.

**Raster dem**  
The [osm3Dcput_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3Dcput_param.json#L15) specifies the raster I used in the example. [osm3Dmamre_param.json](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/extra/osm3Dmamre_param.json#L15) specifies another. These datasets are [avaliable](http://www.ngi.gov.za/index.php/online-shop/what-is-itis-portal)
The script handles the projection and clipping to an aoi. If your focus area falls on the boundary of two raster sheets - you are welcome to an issue so we can expand the fucntionallity to `glob` a folder, reproject, clip and continue. Bear in mind the *NOTE.*

**Triangulation**  
a) [PyVista](https://www.pyvista.org/) is [built-in](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3DCode.py#L415) and will execute after the triangulation; before the 3D City Model is created. This is to visualize the terrain surface. I have left [line 242 of osm3DCode](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/osm3DCode.py#L242) as an aid.
You need to verify if the building footprints have been removed from the terrain surface. The two images illustrate an example were a specific vector had to be excluded. 

<img src="img/fp01.png" alt="alt text" width="250" height="250">  <img src="img/fp02.png" alt="alt text" width="250" height="250">

b) [Triangle](https://www.cs.cmu.edu/~quake/triangle.html) is non-commercial.

**Alternatives**
[BlenderGIS](https://github.com/domlysz/BlenderGIS) and [QGIS](https://qgis.org/en/site/) offers some (if not all and more) of this functionality.

**[The Penultimate Truth](https://en.wikipedia.org/wiki/The_Penultimate_Truth)**
It not very efficient.

**Lastly***
Please don't burden the osm server with requests for an extreme amount of data.
