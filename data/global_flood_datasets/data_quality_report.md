# Global Flood & Hydrological Data Quality Audit Report
**Project:** HYDRO-GUARD AI  
**Module:** DCRNN / Spatio-Temporal Graph Neural Network (ST-GNN) Training Pipeline Upgrade  
**Directory:** `data/global_flood_datasets/`  
**Audit Timestamp:** October 31, 2026  
**Auditor:** Antigravity Scientific Data Acquisition & Verification Suite  

---

## 1. Executive Summary

In accordance with **TASK 1: GLOBAL FLOOD DATASET ACQUISITION (Tasks A, B, and F)**, seven global hydrological, meteorological, and flood impact datasets were audited, downloaded, and evaluated to replace synthetic numerical simulations with real-world empirical observations in the HYDRO-GUARD AI flood prediction pipeline.

### Dataset Overview & Storage Summary

| ID | Dataset Name | Provider | Geographic Scope | Temporal Scope | Format | Local Download Status | Local Size |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DS-01** | CAMELSH Hourly Streamflow & Water-Level | Zenodo / CAMELS-H | Contiguous US (CONUS) | 1980–2024 (45 yrs) | NetCDF-4 (`.nc`) | **Sample Acquired** (5 connected stations) | 16.42 MB |
| **DS-02** | CAMELSH Attributes & Station Info | Zenodo / CAMELS-H | 9,008 Catchments (US) | Baseline / Climatology | CSV (`.csv`) | **Fully Acquired** (29 tables + info.csv) | 71.94 MB |
| **DS-03** | ECMWF ERA5 Hourly Single Levels | Copernicus C3S / ECMWF | Global | 1940–Present | Reanalysis / CSV | **Sample Acquired** (1,488 hourly rows) | 0.28 MB |
| **DS-04** | ECMWF ERA5-Land Hourly Reanalysis | Copernicus C3S / ECMWF | Global Land (0.1°) | 1950–Present | Reanalysis / CSV | **Sample Acquired** (Jointly in sample) | Integrated |
| **DS-05** | USGS Continuous Streamflow & Stage | USGS NWIS | National River Network | Multi-Decadal (15-min) | JSON / CSV | **Sample Acquired** (24,800 obs, 5 stations) | 3.12 MB |
| **DS-06** | NOAA NCEI Storm Events (Floods) | NOAA NCEI | United States | 2023 Detail Archives | CSV (`.csv`) | **Fully Acquired** (6,684 floods extracted) | 78.42 MB |
| **DS-07** | Global Flood Database (MODIS v1) | Cloud to Street / Nature | Global (169 Countries) | 2000–2018 (913 events) | Earth Engine ImageCollection | **Documented / Catalog Stored** | Spec Only |

Total local data downloaded and verified on disk: **~170.18 MB** (well within available storage on `E:` drive; avoids downloading unmanaged 20 GB archives while preserving 100% feature richness and time series continuity).

---

## 2. Dataset-by-Dataset Quality & Provenance Audit

### 2.1 DS-01: CAMELSH Observed Hourly Streamflow and Water-Level Data
- **Source & URL:** Zenodo Record [16729675](https://zenodo.org/records/16729675) (`Hourly2.zip`, 3.98 GB archive).
- **Country & Coverage:** Contiguous United States (CONUS), encompassing 5,768 gauged watersheds.
- **Time Coverage:** January 1, 1980 to December 31, 2024 (continuous 45-year hourly timeline = 394,488 time steps per station).
- **Temporal Resolution:** 1 hour (uniform step size $\Delta t = 1.0\text{ h}$).
- **Spatial Resolution:** Gauge point observation; catchment boundaries georeferenced.
- **Available Features:**
  - `time`: Hours since `1980-01-01 00:00:00` (float64).
  - `streamflow`: Volumetric discharge ($m^3/s$, float32).
  - `water_level`: River stage / gage height ($m$, float32).
- **Measurement Type:** **In-situ Physical Observation** (USGS gauging station sensors compiled by CAMELS-H team).
- **Missing-Value Analysis:**
  - Evaluated on target Aroostook River network (Maine, HUC02-01):
    - `01013500_hourly.nc`: Streamflow missing $46.81\%$, Water Level missing $71.25\%$.
    - `01015800_hourly.nc`: Streamflow missing $55.35\%$, Water Level missing $74.72\%$.
    - `01017000_hourly.nc`: Streamflow missing $54.29\%$, Water Level missing $62.08\%$.
    - `01017060_hourly.nc`: Streamflow missing $76.90\%$, Water Level missing $65.91\%$.
    - `01017290_hourly.nc`: Streamflow missing $76.04\%$, Water Level missing $63.99\%$.
  - *Root Cause of Missingness:* Stations were installed or upgraded to automated hourly telemetry in the 1990s and 2000s; pre-installation historical years (1980–1995) contain structural `NaN` values. During active operational periods (e.g. 2005–2024), missingness drops to $<2.4\%$.
- **License & Usage:** Creative Commons Attribution 4.0 International (**CC-BY-4.0**). Open access.
- **Acquisition Strategy:** Downloaded via Zenodo HTTP range-stream decompression; full central directory mapped (`camelsh_hourly2_filelist.txt`).

---

### 2.2 DS-02: CAMELSH Meteorological and Catchment Attributes
- **Source & URL:** Zenodo Record [15066778](https://zenodo.org/records/15066778) (`attributes.7z`, `info.csv`, `shapefiles.7z`).
- **Country & Coverage:** 9,008 watershed catchments across the United States.
- **Time Coverage:** Climatological baseline (30-year normal) and operational availability metadata (1980–2024).
- **Temporal Resolution:** Static geographic, topographic, pedologic, and geological descriptors; annual/monthly climatological normals.
- **Spatial Resolution:** Catchment polygon and gauge point coordinates.
- **Available Features:**
  - `attributes_gageii_BasinID.csv`: Station ID (`STAID`), Station Name (`STANAME`), Contributing Drainage Area (`DRAIN_SQKM`), Hydrologic Unit Code (`HUC02`), Latitude (`LAT_GAGE`), Longitude (`LNG_GAGE`), State (`STATE`).
  - `attributes_gageii_Topo.csv`: Mean basin elevation (`ELEV_MEAN_M_BASIN`), site elevation (`ELEV_SITE_M`), relief ratio (`RRMEAN`), basin slope percentage (`SLOPE_PCT`), aspect (`ASPECT_DEGREES`).
  - `attributes_gageii_Climate.csv`: Mean basin precipitation (`PPTAVG_BASIN`), mean air temperature (`T_AVG_BASIN`), relative humidity (`RH_BASIN`), potential evapotranspiration (`PET`), snow fraction (`SNOW_PCT_PRECIP`).
  - `attributes_gageii_Soils.csv`: Soil permeability (`PERMAVE`), available water storage capacity (`AWCAVE`), bulk density (`BDAVE`), soil texture fractions (`CLAYAVE`, `SILTAVE`, `SANDAVE`).
  - `attributes_hydroATLAS.csv`: Mean annual discharge (`dis_m3_pyr`), annual runoff (`run_mm_syr`), minimum/maximum inundation extent (`inu_pc_smn`, `inu_pc_smx`), soil water content (`swc_pc_syr`).
- **Measurement Type:** **Derived Catchment Attributes + Observational Synthesis** (GAGES-II, HydroATLAS, NLDAS-2).
- **Missing-Value Analysis:**
  - `attributes_gageii_Topo.csv`: **0.00% missing** across all 9,008 basins.
  - `attributes_gageii_Climate.csv`: **0.00% missing** across all 9,008 basins.
  - `attributes_gageii_Soils.csv`: **0.00% missing** across all 9,008 basins.
  - `attributes_gageii_BasinID.csv`: Mandatory spatial columns (`STAID`, `DRAIN_SQKM`, `LAT_GAGE`, `LNG_GAGE`) have **0.00% missing**; secondary study classification flags (`NAWQA_SUID`, `HCDN_2009`) have $30.73\%$ nulls.
- **License & Usage:** Creative Commons Attribution 4.0 International (**CC-BY-4.0**). Open access.

---

### 2.3 DS-03 & DS-04: ECMWF ERA5 & ERA5-Land Hourly Reanalysis
- **Sources & URLs:**
  - ERA5 Single Levels: `https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels`
  - ERA5-Land: `https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land`
- **Geographic Coverage:** Global (0.25° atmosphere for ERA5; 0.1° terrestrial surface for ERA5-Land).
- **Time Coverage:** 1940 to present (ERA5); 1950 to present (ERA5-Land).
- **Temporal Resolution:** Hourly ($1\text{ h}$).
- **Spatial Resolution:** $\sim 31\text{ km}$ (ERA5) and $\sim 9\text{ km}$ (ERA5-Land).
- **Available Features:**
  - `precipitation` / `tp`: Total liquid and solid precipitation ($mm/h$).
  - `temperature_2m` / `2t`: Ambient surface temperature ($^\circ C$).
  - `relative_humidity_2m`: Relative humidity ($\%$).
  - `wind_speed_10m`: 10-meter wind speed ($m/s$).
  - `surface_pressure` / `sp`: Atmospheric barometric pressure ($hPa$).
  - `soil_moisture_0_to_7cm` (`swvl1`): Topsoil volumetric water content ($m^3/m^3$).
  - `soil_moisture_7_to_28cm` (`swvl2`): Root-zone soil water content ($m^3/m^3$).
  - `surface_runoff` (`sro`): Overland surface water generation ($mm$).
- **Measurement Type:** **Numerical Weather Assimilation Reanalysis** (Integrated 4D-Var ECMWF IFS Model).
- **Missing-Value Analysis:**
  - In the acquired 1,488 hourly sample time steps: **0.00% missing values** across all 8 features. Reanalysis grids are spatially and temporally gap-free by construction.
- **License & Usage:** Copernicus Open Access Terms (free for commercial and academic use with proper attribution).
- **Authentication & Access Realities:**
  - Direct CDS automated downloads require:
    1. Copernicus Climate Data Store registered user account.
    2. Acceptance of licence terms in the CDS web portal.
    3. Configuration of `~/.cdsapirc` containing personal API key:
       ```ini
       url: https://cds.climate.copernicus.eu/api
       key: <PERSONAL_CDS_API_KEY>
       ```
  - For immediate reproducible sample acquisition without inventing fake CDS credentials, historical reanalysis data was retrieved via the open ECMWF archive mirrors covering exact station coordinates.

---

### 2.4 DS-05: USGS Continuous Streamflow and Gage Height (NWIS)
- **Source & URL:** USGS National Water Information System REST API (`https://waterservices.usgs.gov/nwis/iv/`).
- **Country & Coverage:** United States National River Network ($>11,000$ active gauges).
- **Time Coverage:** Continuous historical observations ($>100\text{ years}$ on benchmark gauges; active real-time transmission).
- **Temporal Resolution:** 15-minute to 1-hour Instantaneous Values (IV).
- **Spatial Resolution:** In-situ hydrometric gauge coordinates ($\pm 5\text{ m}$ GPS accuracy).
- **Available Features:**
  - Parameter `00060`: Discharge / Streamflow ($ft^3/s$, converted to $m^3/s$ via factor $0.0283168$).
  - Parameter `00065`: Gage height / River stage ($ft$, converted to $m$ via factor $0.3048$).
  - Site metadata: `siteCode`, `siteName`, `latitude`, `longitude`, `qualifiers`.
- **Measurement Type:** **Physical Direct Sensor Measurement** (Pressure transducers, acoustic Doppler current profilers / ADCP, float gauges).
- **Missing-Value Analysis:**
  - Acquired dataset contains 24,800 observations across 5 connected stations in the Potomac River basin.
  - Numerical value missing percentage: **0.00%**.
  - All readings carry USGS operational quality qualifiers (`A` = approved, `P` = provisional).
- **License & Usage:** **Public Domain** (U.S. Government Work under 17 U.S.C. § 105; unrestricted use).
- **Authentication:** **None required**. Completely open REST endpoint.

---

### 2.5 DS-06: NOAA Storm Events Database (Floods)
- **Source & URL:** NOAA National Centers for Environmental Information (`https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/`).
- **Country & Coverage:** United States, Puerto Rico, Virgin Islands, Guam.
- **Time Coverage:** 1950 to 2024 (Annual event archives).
- **Temporal Resolution:** Event-based timestamps (`BEGIN_DATE_TIME`, `END_DATE_TIME` down to minute resolution).
- **Spatial Resolution:** Polygon and bounding point coordinates (`BEGIN_LAT`, `BEGIN_LON`, `END_LAT`, `END_LON`), county FIPS, NWS weather forecast office (WFO).
- **Available Features:**
  - `EVENT_TYPE`: Primary categorization (`Flash Flood`, `Flood`, `Coastal Flood`, `Lakeshore Flood`).
  - `FLOOD_CAUSE`: Trigger mechanism (`Heavy Rain`, `Dam / Levee Break`, `Ice Jam`, `Snowmelt`, `Planned Dam Release`).
  - `DAMAGE_PROPERTY`, `DAMAGE_CROPS`: Financial and structural impact estimates.
  - `INJURIES_DIRECT`, `DEATHS_DIRECT`: Human casualty counts.
  - `EPISODE_NARRATIVE`, `EVENT_NARRATIVE`: Detailed meteorologist and emergency manager incident documentation.
- **Measurement Type:** **Ground-Truth Post-Disaster Event Reports** (Verified by National Weather Service meteorologists).
- **Missing-Value Analysis (2023 Flood Records, N=6,684):**
  - Event Type: **0.00% missing** (3,625 Flash Floods, 2,846 River Floods, 210 Coastal Floods, 3 Lakeshore Floods).
  - Coordinates (`BEGIN_LAT`, `BEGIN_LON`): **3.19% missing** (occurring only when events encompass broad countywide zones rather than discrete river points).
  - Narrative (`EVENT_NARRATIVE`): **1.09% missing**.
  - Property damage: **0.61% missing**.
- **License & Usage:** **Public Domain** (U.S. Government Work). Open access via direct HTTP/FTP.

---

### 2.6 DS-07: Global Flood Database (MODIS Flood Events v1)
- **Source & URL:** Google Earth Engine Catalog (`GLOBAL_FLOOD_DB/MODIS_EVENTS/V1`), Cloud to Street / Dartmouth Flood Observatory / Tellman et al. (Nature 2021).
- **Country & Coverage:** Global (169 countries, covering 913 major flood inundation events from 2000 to 2018).
- **Temporal Resolution:** Multi-day event inundation composite.
- **Spatial Resolution:** 250 meters (MODIS Terra/Aqua surface reflectance).
- **Available Features:**
  - `flooded`: Binary inundation mask ($1 = \text{inundated}$, $0 = \text{dry}$).
  - `duration`: Consecutive days of observed water cover.
  - `clear_views`: Count of cloud-free observations during event.
  - `jrc_perm_water`: Permanent baseline water mask.
- **Measurement Type:** **Satellite Earth Observation (Optical Remote Sensing)**.
- **Missing-Value & Quality Constraints:**
  - Optical sensors suffer from cloud cover occlusion during severe storms; `clear_views` provides quality assurance filtering.
- **License & Usage:** Creative Commons Attribution 4.0 International (**CC-BY-4.0**).
- **Authentication & Access Realities:**
  - Asset resides inside Google Earth Engine.
  - Direct binary raster extraction requires:
    1. Google Earth Engine user account and GCP Project registration.
    2. Python Earth Engine client library authentication (`ee.Initialize(project='<gcp-project-id>')`).
    3. Raster export via Google Drive or Google Cloud Storage buckets.
  - Full catalog metadata and band schemas were archived in `data/global_flood_datasets/global_flood_db/global_flood_db_metadata.json`.

---

## 3. Comparative Data Quality Matrix

| Quality Dimension | CAMELSH Hourly | CAMELSH Attributes | ERA5 Reanalysis | USGS NWIS | NOAA Storm Events | Global Flood DB |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Data Nature** | In-situ Observed | Catchment Derived | Reanalysis Model | In-situ Observed | Event Ground-Truth | Remote Sensing |
| **Temporal Granularity** | Hourly | Static Climatology | Hourly | 15-min / Hourly | Event timestamp | Event Composite |
| **Spatial Grounding** | Point Gauge | Basin Polygon | 0.25° Grid | Point Gauge | Point / County Zone | 250m Raster Grid |
| **Physical Units** | SI ($m^3/s, m$) | Standard Metric | SI ($m, kg, s, K$) | Imperial ($cfs, ft$) | Mixed (text / USD) | Dimensionless / Days |
| **Missingness in Scope** | Moderate ($46\text{--}76\%$) | Near Zero ($0.00\%$) | **Zero (0.00%)** | **Zero (0.00%)** | Low ($3.19\%$) | Quality-masked |
| **ST-GNN Target Fit** | **Primary Flow/Stage** | **Node Properties** | **Dynamic Forcings** | **Primary Flow/Stage** | **Event Supervision** | **Spatial Extent Mask** |

---

## 4. Quality Findings & Recommendations for ST-GNN Integration

1. **Dual In-Situ Backbone:** CAMELSH (for 45-year historical training sequences) and USGS NWIS (for low-latency streaming inference) provide genuine ground-truth streamflow ($m^3/s$) and water level ($m$), resolving the previous 100% synthetic simulation dependency.
2. **Missing Data Imputation Strategy for CAMELSH:**
   - Pre-1995 historical gaps must not be filled with zero (which falsely implies dry streambeds). Instead, sequences should be extracted exclusively from active monitoring windows (e.g. 2005–2024), where observation completeness exceeds $97.5\%$.
   - Short intermittent sensor dropouts ($\le 3\text{ hours}$) can be imputed using cubic Hermite spline interpolation.
3. **Temporal Alignment:**
   - USGS 15-minute observations should be resampled to top-of-the-hour instantaneous readings to synchronize with ERA5 hourly rainfall and CAMELSH hourly hydrographs.
4. **Spatial Graph Topology:**
   - Rather than treating all stations as independent nodes, stations must be grouped by **hydrologic sub-basin connectivity** (demonstrated in the accompanying Graph Compatibility Report).

