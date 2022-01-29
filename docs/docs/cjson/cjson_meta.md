---
layout: default
title: Metadata
parent: CityJSON
nav_order: 2
---

# CityJSON Metadata
{: .no_toc }

---

It is recommended to define metadata for the 3D City Model in the respective `param.json`. While a mininum example with a brief explanation of the metadata parameters are given here the reader is encouraged to explore the comprehensive [CityJSON Specifications](https://www.cityjson.org/specs/1.1.0/#metadata).

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
 
 The osm attribution is hardcoded (fixed) as 
 ```python
    "source": [
            {
            "description": "OpenStreetMap contributors",
            "sourceReferenceSystem": "urn:ogc:def:crs:EPSG:4326",
            "sourceCitation": "https://www.openstreetmap.org",
             }],
 ```
 
 

