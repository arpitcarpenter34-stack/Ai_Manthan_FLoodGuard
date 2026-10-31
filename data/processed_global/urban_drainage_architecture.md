# Urban Drainage Graph & Street-Level Inundation Engine Design
**Project:** HYDRO-GUARD AI  
**Module Specification:** Subsystem Architecture for Urban Drainage & Street Inundation (PS-11 Phase 2)  
**Document:** `data/processed_global/urban_drainage_architecture.md`  
**Date:** October 31, 2026  
**Status:** **TECHNICAL DESIGN & MATHEMATICAL SPECIFICATION**  

---

## 1. Urban Drainage Network as a Directed Graph

To model stormwater propagation inside a city, the underground and surface drainage infrastructure is formulated as an augmented directed graph:

$$G_{\text{drain}} = (V_d, E_d)$$

```
                                 [Precipitation Inflow P(t)]
                                              │
                                              ▼
┌─────────────────────────────────────── [Surface Catchment Node] ───────────────────────────────────────┐
│                                             │                                                          │
│                                             ▼                                                          │
│     [Drop Inlet / Catch Basin Node] ◄── [Street Gutter Node] ──► [Overland Road Segment Node]          │
│                    │                                                            ▲                      │
│                    │ Gravity Drain                                              │ Surcharge Overflow   │
│                    ▼                                                            │ (When h > h_rim)     │
│        [Junction / Manhole Node] ───────────────────────────────────────────────┘                      │
│                    │                                                                                   │
│                    │ Circular Conduit (Manning Q)                                                      │
│                    ▼                                                                                   │
│           [Sump Basin / Pumping Station Node] ──► [Sluice Gate Node] ──► [River Outfall Node]          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Node Types & Physical Attributes ($V_d$)

1. **Junction / Manhole Nodes ($V_{\text{manhole}}$)**:
   - $z_{\text{invert}}$: Invert bottom elevation ($m\text{ MSL}$).
   - $z_{\text{rim}}$: Surface street manhole cover elevation ($m\text{ MSL}$).
   - $d_{\text{depth}} = z_{\text{rim}} - z_{\text{invert}}$: Maximum storage depth before surface spill.
   - $A_{\text{manhole}}$: Cross-sectional storage area ($\approx 1.0\text{--}2.0\text{ m}^2$).
   - Dynamic State: Water depth $y_j(t)$ and pressure head $H_j(t) = z_{\text{invert}} + y_j(t)$.

2. **Storage Basin / Sump Nodes ($V_{\text{sump}}$)**:
   - Pump intake retention well.
   - $V_{\text{capacity}}$: Usable holding volume ($m^3$).
   - $h_{\text{suction\_min}}$: Minimum water depth required to operate pumps without air entrainment.
   - $h_{\text{alarm}}$: Emergency overflow threshold.

3. **River Outfall Nodes ($V_{\text{outfall}}$)**:
   - Interface between urban stormwater pipes and the external natural river.
   - Boundary condition driven directly by our river ST-GNN predicted river stage $h_{\text{river}}(t)$.
   - Governed by backwater check-valves / sluice flap gates.

### 1.2 Edge Types & Hydraulic Attributes ($E_d$)

1. **Gravity Pipe Conduits ($E_{\text{pipe}}$)**:
   - Invert slope: $S_0 = \frac{z_{\text{in}} - z_{\text{out}}}{L}$.
   - Diameter $D$ or width/height ($m$).
   - Manning roughness $n$ (Concrete pipe $n \approx 0.013\text{ s/m}^{1/3}$; Corrugated metal $n \approx 0.024$).
   - Maximum free-surface discharge capacity via Manning's Equation:
     $$Q_{\text{full}} = \frac{1}{n} A_{\text{full}} R_{h,\text{full}}^{2/3} S_0^{1/2} = \frac{1}{n} \left(\frac{\pi D^2}{4}\right) \left(\frac{D}{4}\right)^{2/3} S_0^{1/2}$$

2. **Pump Force Mains ($E_{\text{pump}}$)**:
   - Active conveyance edge actuated by electric drainage pumps.
   - Forward flow capacity determined by pump curve: $Q_{\text{pump}} = f(\Delta H, u_{\text{speed}})$.

---

## 2. Dynamic 1D-2D Coupled Hydraulic Mechanism

Urban street flooding is mathematically modeled through a **dual-drainage 1D-2D coupling**:

```
                              RAIN INTENSITY I(t)
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │    Rational / SCS Runoff      │
                      │       Q_surface(t)            │
                      └───────────────┬───────────────┘
                                      │
                       Inlet Capacity │ Q_inlet = min(Q_surface, Q_curb_capacity)
                                      ▼
                      ┌───────────────────────────────┐
                      │   1D Underground Conduit      │
                      │      Pipe Flow Q_pipe         │
                      └───────────────┬───────────────┘
                                      │
                         Is Conduit   │
                         Surcharged?  │ Condition: y_j(t) > d_depth
                                      ▼
                                     YES
                                      │
                       Overland Spill │ Q_spill = c_w * L_rim * sqrt(2 * g * (y_j - d_depth))
                                      ▼
                      ┌───────────────────────────────┐
                      │    2D Street Inundation       │
                      │  Water Depth on Road Graph    │
                      └───────────────────────────────┘
```

### 2.1 Surcharge and Surface Overland Spill
When storm runoff exceeds underground pipe capacity, the hydraulic gradeline (HGL) rises above the ground surface elevation ($H_j > z_{\text{rim}}$). The surcharge flow rate spilled onto the street surface is calculated using the weir discharge equation:

$$Q_{\text{spill},j}(t) = c_w \cdot P_{\text{manhole}} \cdot \sqrt{2g} \cdot \max\left(0.0, y_j(t) - d_{\text{depth}}\right)^{3/2}$$

where:
- $c_w \approx 0.60$ is the discharge weir coefficient.
- $P_{\text{manhole}} = \pi D_{\text{rim}}$ is the perimeter of the manhole / drop inlet.
- $y_j(t) - d_{\text{depth}}$ is the excess pressure head above the street surface.

---

## 3. Street-Level Inundation & Road Segment Risk Mapping

### 3.1 Road Network Graph Extraction ($G_{\text{road}}$)
The urban street network is modeled as a navigable graph $G_{\text{road}} = (V_r, E_r)$ extracted from OpenStreetMap:
- **Road Edge $e_r$:** Road segment centerline polyline with length $L_r$, width $W_r$, and surface material.
- **Topographic Elevation:** Road link elevation profile sampled from high-resolution LiDAR / Copernicus DEM:
  $$z_{\text{road}}(s), \quad s \in [0, L_r]$$
- **Height Above Nearest Drainage (HAND):**
  $$\Delta z_{\text{HAND}} = z_{\text{road}} - z_{\text{drain\_outlet}}$$

### 3.2 Road Inundation Depth Estimation
When surcharge spill $Q_{\text{spill}}$ enters road link $r$, the overland water depth $d_{\text{road}}(t)$ is determined by local volumetric ponding and street gutter conveyance:

$$d_{\text{road}}(t) = \frac{V_{\text{water},r}(t)}{L_r \cdot W_r}$$

where the water volume evolves according to:

$$\frac{dV_{\text{water},r}}{dt} = \sum Q_{\text{spill},\text{in}} + Q_{\text{overland\_in}} - Q_{\text{gutter\_out}}$$

### 3.3 Street Inundation Risk & Traffic Hazard Tiers

```
┌─────────────────┬──────────────────────┬────────────────────────────────────────────────────────┐
│ Inundation Tier │ Road Water Depth     │ Physical & Operational Consequence                     │
├─────────────────┼──────────────────────┼────────────────────────────────────────────────────────┤
│ PASSABLE        │ d < 0.10 m (< 4 in)  │ Normal vehicle operation; gutter drainage active       │
│ CAUTION         │ 0.10 m <= d < 0.30 m │ Two-wheelers stalled; low-clearance sedans restricted  │
│ CRITICAL DANGER │ 0.30 m <= d < 0.60 m │ Exhaust pipe water intake; vehicular engine lock       │
│ CATASTROPHIC    │ d >= 0.60 m (> 2 ft) │ Vehicles swept away (buoyant lift); road closed        │
└─────────────────┴──────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 4. Implementation Interface for Module Integration

The Python interface for the urban drainage graph is defined as a clean class structure:

```python
class UrbanDrainageGraph:
    """
    Constructs and solves 1D-2D coupled urban drainage network.
    Compatible with NetworkX and PyTorch Geometric for ST-GNN inference.
    """
    def __init__(self, junctions_file: str, conduits_file: str, road_segments_file: str):
        self.nodes = {}  # Manholes, sumps, outfalls
        self.edges = {}  # Conduits, pumps, gates
        self.roads = {}  # Street polylines with elevation
        
    def step_hydraulic_state(self, rainfall_intensity_mmh: float, river_boundary_stage_m: float, dt_seconds: float):
        """
        Computes 1D conduit flow, manhole surcharge, and street inundation depths.
        Returns road hazard GeoJSON.
        """
        pass
```

