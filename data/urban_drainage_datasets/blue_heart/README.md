# Blue Heart dataset

## Overview

This dataset provides high density hydrometric and sewer system data collected under the Blue Heart project (Blue Heart, 2026) from 497 gauges across a 78 km<sup>2</sup> urban catchment in the UK, including from rainfall gauges, fluvial water level gauges, groundwater monitoring boreholes, road gullies and in-sewer level sensors. This data is supplemented by metadata describing the sensor network, shape files providing detail on the catchment topography and layout of the fluvial and sewer systems, and additional air and water temperature data providing contextual environmental conditions.

## Contents and structure

### `index_telemetry_data.csv`

An index of all gauge locations, including the following information for each location:
* Name
* Latitude and longitude (`locationLatitude` and `locationLongitude`)
* Gauge type (Borehole / Fluvial / Sewer / Highway gully / Rain) (`gaugeType`)
* Relative path of .csv file containing the timeseries telemetry data for this location (`dataPath`) (e.g. "3_borehole_data/WS13 - Polegate Park.csv")
* Relative path of .csv file containing the quality labels for the timeseries telemetry data for this location (`dataQualityFlagsPath`) (e.g. "3_borehole_data/WS13 - Polegate Park_quality_flags.csv")
* List of the timeseries parameters available for this location (`gaugeParameters`) (e.g. "Water Temperature; Air Temperature; Depth To Water")
* List of units in which the above timeseries are recorded (`parameterUnits`) (one per parameter, e.g. "°C; °C; m" corresponding to gaugeParameters "Water Temperature; Air Temperature; Depth To Water")
* The gauge owner (`gaugeOwner`) (Blue Heart or Southern Water)
* Flood threshold (water level above which flooding occurs) (`floodThreshold_mm`); only available for gauges of 'Highway gully' type.
* Estimated channel bed and bank levels, based on cross section data (`bedLevelEstimate_mAOD` and `bankLevelEstimate_mAOD`); only available for gauges of 'Fluvial' type.

### `1_catchment_shape_files/`: Shapefiles characterising the catchment

Contains shape files characterising the catchment, including:
* `catchment_outline\`: Catchment outline shape files
* `elevation\`: Shape files containing elevation data for the catchment
* `infiltration\`: Shape files containing infiltration data for the catchment

### `2_network_shape_files/`: Shape files describing the sewer and fluvial systems

Contains shape files representing the fluvial network and sewer system, including:
* `links\`: Shape files containing geometry and attributes of 'link' components in the sewer and fluvial systems, including conduits, river reaches, weirs, sluices, valves and screens. Metadata for all links is also provided in csv format (`links\links_metadata.csv`).
* `nodes\`: Shape files containing geometry and attributes of 'node' components in the sewer system, including manholes, outfalls and storage. Metadata for all nodes is also provided in csv format (`).

### `3_borehole_telemetry_data/`: Borehole timeseries data

Contains .csv files with timeseries data from boreholes and corresponding .csv files with quality labels for the data (two files per location, with file names matching the location name, e.g. "WS13 - Polegate Park.csv" and "WS13 - Polegate Park_quality_flags").

### `4_fluvial_telemetry_data/`: Fluvial system timeseries data

Contains .csv files with timeseries data from the fluvial system and corresponding .csv files with quality labels for the data (two files per location, with file names matching the location name, e.g. "Astaire Ave.csv" and "Astaire Ave_quality_flags").

### `5_sewer_telemetry_data/`: Sewer system timeseries data

Contains .csv files with timeseries data from the sewer system and corresponding .csv files with quality labels for the data (two files per location, with file names matching the location name, e.g. "EASTBOURNE WTW (TQ58005103).csv" and "EASTBOURNE WTW (TQ58005103)_quality_flags").

### `6_highway_gully_telemetry_data/`: Highway gully timeseries data

Contains .csv files with timeseries data from highway gullies and corresponding .csv files with quality labels for the data (two files per location, with file names matching the location name, e.g. "ESH5B_Star Rd.csv" and "ESH5B_Star Rd_quality_flags").

### `7_rain_gauge_telemetry_data/`: Raingauge timeseries data

Contains .csv files with timeseries data from rain gauges and corresponding .csv files with quality labels for the data (two files per location, with file names matching the location name, e.g. "Bourne School.csv" and "Bourne School_quality_flags").

## Timestamp formats

Timestamps in all raw telemetry data are unaltered from that in which they were stored by the devices. This is typically a UTC‑offset RFC 3339 timestamp, consisting of date (YYYY‑MM‑DD), time (HH:MM:SS) and timezone offset from UTC (e.g. "2025-06-30 16:42:43+00:00"), but for highway gully telemetry data does not include the timezone offset (e.g. "2025-06-30 16:42:43").
All .csv files containing calculated quality labels use UTC‑offset RFC 3339 timestamps.

## Data quality labels

Data quality labels are included for the telemetry data as detailed above, based on range checks, rate-of-change checks and persistence checks. The labels for each data point consist of a numeric flag and, if applicable, alphabetic labels indicating which quality checks were failed, as detailed below. E.g. "3BE" indicates data classified as 'bad' due to being both below the feasible range and persistently constant.

| Flag | Category | Description                         |
|:-----|:---------|:------------------------------------|
| 1    | Good     | Quality control check(s) passed     |
| 2    | Suspect  | Suspect data                        |
| 3    | Bad      | Not physically plausible            |

| Label | Description                   |
|:-----|:-------------------------------|
| A    | Above feasible range           |
| B    | Below feasible range           |
| C    | Low SNR                        |
| D    | High rate of change            |
| E    | Persistently constant value    |

## Acknowledgements

This research was completed for the ‘Blue Heart’ project and funded by the Department for Environment, Food and Rural Affairs (Defra) as part of the £200 million Flood and Coastal Innovation Programmes which is managed by the Environment Agency. The programmes will drive innovation in flood and coastal resilience and adaptation to a changing climate.
The authors gratefully acknowledge Southern Water for providing access to their sewer monitoring data and for granting permission to share the dataset publicly.

## References

Blue Heart (2026) Flood awareness and resilience in Eastbourne and Southern Wealden, https://www.blueheart.org.uk/

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20699635.svg)](https://doi.org/10.5281/zenodo.20699635)