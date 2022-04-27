---
layout: default
title: Metadata
parent: CityJSON
nav_order: 2
---

# CityJSON Metadata
{: .no_toc }

---

It is recommended to define metadata for the 3D City Model in the respective `param.json`. While a minimum example with a brief explanation of the metadata parameters are given here the reader is encouraged to explore the comprehensive [CityJSON Specifications](https://www.cityjson.org/specs/1.1.0/#metadata).

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---
## Title

```json
    "cjsn_title": "LoD1 City Model of rural village, Mamre, Cape Town",
```
## referenceDate
```json    
    "cjsn_referenceDate": "2021-07-31",
```
## referenceSystem

Coordinate reference system (crs) definition is formatted according to the [OGC Name Type Specification](https://docs.opengeospatial.org/pol/09-048r5.html#_production_rule_for_specification_element_names):

&emsp;&emsp;`http://www.opengis.net/def/crs/{authority}/{version}/{code}`  
&emsp;&emsp;where `{authority}` designates the authority responsible for the definition of the crs (usually "EPSG" or "OGC"),  
&emsp;&emsp;and `{version}` designates the specific version of the crs ("0" (zero) is used if there is no version).
        
```json
    "cjsn_referenceSystem": "https://www.opengis.net/def/crs/EPSG/0/32734",
```
## pointOfContact

`"pointOfContact"` is defined through 

```json    
    "cjsn_contactName": "arkriger", 
    "cjsn_emailAddress": "adrian-kriger@gmail.com", 
    "cjsn_website": "www.linkedin.com/in/adrian-kriger", 
    "cjsn_contactType": "private",
```
## +metadata-extended

Acknowledging the source of the raster DEM is possible. 

```json
    "cjsn_+meta-description": "Chief Directorate: National Geo-spatial Information",
    "cjsn_+meta-sourceSpatialResolution": "25 meter raster DEM",
    "cjsn_+meta-sourceReferenceSystem": "urn:ogc:def:crs:EPSG:20481",
    "cjsn_+meta-sourceCitation":"http://www.ngi.gov.za/",
 ```
 
 The osm attribution and `osm_LoD1_3DCityModel` processing is hardcoded (fixed) as: 
 ```python
    "source": [
         {
           "description": "OpenStreetMap contributors",
           "sourceReferenceSystem": "urn:ogc:def:crs:EPSG:4326",
           "sourceCitation": "https://www.openstreetmap.org",
         }],
    "processStep": {
            "description" : "Processing of building vector contributions <raster DEM> using osm_LoD1_3DCityModel workflow",
             "processor": {
                   "contactName": param['cjsn_contactName'],
                   "contactType": param['cjsn_contactType'],
                   "website": "https://github.com/AdrianKriger/osm_LoD1_3DCityModel"
 ```
 
 

