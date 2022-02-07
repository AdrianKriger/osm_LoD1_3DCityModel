---
layout: default
title: Interactive Visualization
nav_order: 4
---

# Interactive Visualization
{: .no_toc }


The [Jupyter](https://eis n.wikipedia.org/wiki/Project_Jupyter#Jupyter_Notebook) environment allows for easy customization of a dynamic visualization. The example `iframe` below is the product of [village/campus interactiveOnly.ipynb](https://github.com/AdrianKriger/osm_LoD1_3DCityModel/blob/main/village_campus/interactiveOnly.ipynb). Building stock is differentiated through color. A school, housing, retail, healthcare and community focused facilities are easily identified while the tooltips highlight the underlying data. Additional features unique to an aoi can also be included. Here farmland, streams, recreational spaces and bus rapid transit routes have been added *- you are thus limited only through data and your imagination*. <!-- {: .fs-6 .fw-300 } -->

**To navigate on a laptop without a mouse**:

- `trackpad left-click drag-left` and `-right`;
- `Ctrl left-click drag-up`, `-down`, `-left` and `-right` to rotate and so-on and
- `+` next to Backspace zoom-in and `-` next to `+` zoom-out.


<iframe src="{{site.baseurl | prepend: site.url}}/img/interactiveOnly.html" style="width: 800px; height: 400px; border: 0px"></iframe>


The visualisation above employs the default [Carto Dark Matter](https://github.com/CartoDB/basemap-styles) basemap. [Pydeck](https://deckgl.readthedocs.io/en/latest/index.html) supports a number of [map_styles](https://deckgl.readthedocs.io/en/latest/deck.html) including the extensive [mapbox gallery](https://www.mapbox.com/gallery/). 
