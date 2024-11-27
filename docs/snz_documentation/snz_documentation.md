# TS 1170.5 Seismic Demand Parameters



## Digital supplements for Tables 3.4, 3.5, and 3.2 

This webpage provides access to the digital supplements associated with the Seismic Demand Parameter (SDP) tables provided in TS 1170.5 ([insert link]()). 

The parameter values vary by location, annual probability of exceedance (APOE), and Site Class.



The spectral shape-related parameters are defined in Section 3.1.2, copied below. 

![sa_parameter_definitions](sa_parameter_definitions.png)

Additional parameters include:

![m_definition](m_definition.png)

![d_definition](d_definition.png)



The TS 1170.5 provides two sets of SDP tables, one table for named urban and rural settlements (Table 3.4) and another table for a 0.1 x 0.1 degree grid of latitudes and longitudes (Table 3.5). The tables are provided in three file formats (PDF, JSON, and CSV), along with geospatial data used in deriving the parameter values.



The relevant metadata for each format and links to the files are provided below. The following tools provide additional support for accessing the data:

- a python package for dynamically querying the parameter tables ([insert link]())

- a webtool (provided by SESOC) for visualising and downloading parameters on a location-by-location basis ([insert link]())

  

 

## SDP tables metadata

The difference between Tables 3.4 and 3.5 is the type of location specified in the location groupings (where each location group includes six APOEs).

Table | Location type | Example
:--:|:---:| ---
**3.4** | &nbsp; named settlement | _Wellington_ 
**3.5** | lat/lon grid point | _-42.3~174.8_ (with 0.1 degree precision) 

#### PDF files

Formatted, searchable files, as included in the TS 1170.5 document. Settlement names with macrons are supplemented with a plain text version, for flexible searchability.

<span style="color:red">Todo: switch the location to Whangarei to demonstrate the macrons. (Column header will become Settlement.)</span>

![pdf_table](pdf_table.png)

#### CSV files

Unformatted, comma separated text files.

<span style="color:red">Todo: add equivalent set of parameters in .csv format.</span>

#### JSON files

Python dictionaries including the SDP values and a schema defining the metadata. The dictionary can be read as a pandas table using:

        pandas.read_json(filepath, orient="table")

![pd_table](placeholder_pd_table.png)






## Geospatial files metadata

<span style="color:red">Todo: finalise the file format and metadata of the .geojson files.</span>



### Named settlements (Table 3.4)

The parameter values in Table 3.4 apply for all locations that fall within urban and rural settlement boundaries, as defined by the geospatial polygon data provided in the GEOJSON file.

- [insert .pdf link]()
- [insert .csv link]()
- [insert .json link]()
- [insert .geojson link]()


### Grid locations (Table 3.5)

The parameter values in Table 3.5 apply for all other locations, by taking the nearest 0.1 x 0.1 degree latitude/longitude grid point.

- [insert .pdf link]()
- [insert .csv link]()
- [insert .json link]()


### Major faults (Table 3.2)

The geospatial data that defines the major faults named in Table 3.2.

- [insert .geojson link]()
