# Drainage Pump & Sluice Gate Optimization Engine Design
**Project:** HYDRO-GUARD AI  
**Module Specification:** Operational Decision Support & Constrained Optimization (PS-11 Phase 2)  
**Document:** `data/processed_global/pump_gate_optimization_design.md`  
**Date:** October 31, 2026  
**Status:** **MATHEMATICAL SPECIFICATION & SAFETY PROTOCOL**  

---

## 1. Executive Summary & Operational Objective

Urban stormwater drainage networks in flood-prone cities rely on automated pumping stations and sluice gates to discharge stormwater into receiving rivers. However, during severe storms, pump operations face severe competing constraints:
1. **Flood Prevention:** Evacuating stormwater from low-lying sumps before street manholes surcharge.
2. **Backwater Gate Flap Condition:** River stages may rise higher than the urban drain invert, causing river water to reverse flow into the city if sluice gates remain open!
3. **Downstream River Overtopping:** Pumping excess urban water into an already crested river can worsen regional flood devastation downstream.
4. **Energy Cost & Equipment Wear:** Excessive pump cycling causes motor burnouts and surges electrical grid demand.

Under **Task 2.1**, an advanced **Model Predictive Control (MPC) / Constrained Multi-Objective Optimization Module** is formulated.

> [!CAUTION]
> **MANDATORY SAFETY ISOLATION (ZERO PHYSICAL ACTUATION)**
> This module operates exclusively within a **Safe Simulation Environment**. The output provides advisory dispatch recommendations and simulated valve states. Under no circumstances will software directly transmit actuation commands to physical industrial PLCs, SCADA relays, or electrical switchgear without human operator sign-off and physical safety interlocks.

---

## 2. Mathematical Optimization Formulation (MPC)

The decision engine operates on a rolling prediction horizon of $T_p = 6\text{ hours}$ with a discrete timestep of $\Delta t = 15\text{ minutes}$ ($K = 24\text{ control steps}$).

```
       [Predicted Storm Runoff Q_in(t)]       [ST-GNN River Stage Forecast h_river(t)]
                       │                                         │
                       ▼                                         ▼
            ┌────────────────────────────────────────────────────────┐
            │       MODEL PREDICTIVE CONTROL OPTIMIZER (MPC)         │
            │          Minimize Multi-Objective Cost Function        │
            │   Subject to Conservation, Capacity & Safety Limits    │
            └──────────────────────────┬─────────────────────────────┘
                                       │
                      Optimal Dispatch Trajectory u*(t)
                                       │
                                       ▼
            ┌────────────────────────────────────────────────────────┐
            │          VIRTUAL SCADA SIMULATION SANDBOX              │
            │   Simulates Sump Depth, Power Consumption, Flow Rates  │
            │      * Physical Actuation Blocked by Hardware Air-Gap  │
            └────────────────────────────────────────────────────────┘
```

### 2.1 Objective Cost Function ($J$)

The optimization minimizes a weighted composite cost across the prediction horizon $k \in \{1, \dots, K\}$:

$$\min_{\mathbf{u}, \boldsymbol{\theta}} J = \sum_{k=1}^{K} \Big[ w_{\text{flood}} \cdot J_{\text{flood}}(k) + w_{\text{energy}} \cdot J_{\text{energy}}(k) + w_{\text{wear}} \cdot J_{\text{wear}}(k) + w_{\text{river}} \cdot J_{\text{river}}(k) \Big]$$

#### 1. Flood Penalty Term ($J_{\text{flood}}$):
Penalizes water levels in sumps and critical junctions exceeding safe thresholds:
$$J_{\text{flood}}(k) = \sum_{j \in \text{sumps}} \max\left(0, y_j(k) - y_{j,\text{safe}}\right)^2 + 10 \cdot \sum_{j \in \text{sumps}} \max\left(0, y_j(k) - y_{j,\text{spill}}\right)^2$$

#### 2. Energy Consumption Term ($J_{\text{energy}}$):
Minimizes electrical power cost based on time-of-use tariffs $C_e(k)$ (\$/kWh):
$$J_{\text{energy}}(k) = C_e(k) \sum_{i \in \text{pumps}} P_i(k) \cdot u_i(k) \cdot \Delta t$$
where pump power $P_i(k)$ is a function of discharge rate and total dynamic head:
$$P_i(k) = \frac{\rho g \cdot Q_{\text{pump},i} \cdot \Delta H_i(k)}{\eta_{\text{motor}} \cdot \eta_{\text{pump}}}$$

#### 3. Equipment Mechanical Wear & Rapid Cycling ($J_{\text{wear}}$):
Penalizes switching pumps on and off repeatedly:
$$J_{\text{wear}}(k) = \sum_{i \in \text{pumps}} \left| u_i(k) - u_i(k-1) \right|$$

#### 4. Downstream River Impact Penalty ($J_{\text{river}}$):
Penalizes pumping into a river node whose stage is currently at or above NWS Minor Flood Stage:
$$J_{\text{river}}(k) = \max\left(0, h_{\text{river}}(k) - h_{\text{flood\_stage}}\right) \cdot \sum_{i} Q_{\text{pump},i}(k)$$

---

## 3. Physical & Hydraulic Constraints

### 3.1 Sump Basin Mass Conservation:
For each pump station wet-well:
$$V_j(k) = V_j(k-1) + \Delta t \left[ Q_{\text{in},j}(k) - \sum_{i \in \text{pumps}} u_i(k) \cdot Q_{\text{pump},i}(k) - Q_{\text{gate},j}(k) \right]$$
$$y_j(k) = f_{\text{geometry}}^{-1}\left(V_j(k)\right)$$

### 3.2 Sluice Gate Flow & Backwater Interlock:
Gravity discharge through a sluice gate depends on the head difference between urban sump $y_j$ and river stage $h_{\text{river}}$:

$$Q_{\text{gate}}(k) = \begin{cases} c_d \cdot W_g \cdot \theta_{\text{gate}}(k) \sqrt{2g \left(y_j(k) - h_{\text{river}}(k)\right)} & \text{if } y_j(k) > h_{\text{river}}(k) \\ 0.0 & \text{if } h_{\text{river}}(k) \ge y_j(k) \quad \text{\textbf{(Backwater Lock)}}\end{cases}$$

> **SAFETY RULE:** If $h_{\text{river}}(k) \ge y_j(k)$, the sluice gate aperture $\theta_{\text{gate}}(k)$ must be forced to $0.0$ (closed) to prevent river inundation of the city!

### 3.3 Pump Operating Constraints:
1. **Binary / Speed Control:** $u_i(k) \in \{0, 1\}$ for fixed-speed pumps; $u_i(k) \in [0.0, 1.0]$ for Variable Frequency Drives (VFD).
2. **Minimum Net Positive Suction Head (NPSH):**
   $$u_i(k) = 0 \quad \text{if } y_j(k) < h_{\text{suction\_min}}$$
3. **Maximum Starts Per Hour:**
   $$\sum_{m=k-3}^{k} \max\left(0, u_i(m) - u_i(m-1)\right) \le 1 \quad (\text{Max 4 starts per hour})$$

---

## 4. Software Architecture & Safety Interlocks

```python
class PumpGateOptimizer:
    """
    Model Predictive Control (MPC) Engine for Drainage Pumps & Sluice Gates.
    Solves multi-objective MILP / Non-linear programming via SciPy/CasADi.
    """
    def __init__(self, sump_capacity_m3: float, pump_specs: list, gate_specs: list):
        self.sump_capacity = sump_capacity_m3
        self.pumps = pump_specs
        self.gates = gate_specs
        self.simulation_mode = True  # STRICT HARDWARE AIR-GAP
        
    def solve_optimal_dispatch(
        self,
        predicted_inflow_m3s: np.ndarray,       # Horizon (K,)
        forecasted_river_stage_m: np.ndarray,   # Horizon (K,) from ST-GNN
        initial_sump_depth_m: float
    ) -> dict:
        """
        Solves optimal pump schedule u*(t) and gate aperture theta*(t).
        Returns advisory plan with safety checks.
        """
        # Safety Assertions
        # 1. Backwater interlock check
        # 2. NPSH suction depth protection
        # 3. Maximum starts per hour constraint
        pass
```

### Safety Air-Gap Guarantees:
- Output commands are tagged with `IS_ADVISORY_ONLY = True`.
- No direct network socket or Modbus/DNP3 industrial communication stack is initialized.
- A virtual simulator visualizes water levels and energy consumption without hardware exposure.

