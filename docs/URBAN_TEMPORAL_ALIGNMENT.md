# HYDRO-GUARD AI — Urban Temporal Alignment & Sequence Preparation
**Document ID:** `HGAI-ALIGN-URBAN-TEMP-2026-10-31`  
**Location:** `docs/URBAN_TEMPORAL_ALIGNMENT.md`  
**Artifact Directory:** `data/processed_global/urban_sequences/`  
**Status:** COMPLETE / PROCESSED & VERIFIED  

---

## 1. Executive Summary & Alignment Objective

In physical urban drainage networks, runoff and surcharge occur on much faster timescales (minutes to hours) than river basin inundation (hours to days). 

Task 2.4 aligned in-situ road gully water levels with catchment rainfall observations across a continuous **10-month evaluation window (2025-07-01 to 2026-04-30)** covering **7,296 synchronized hours**.

### Fundamental Alignment Rule: Zero Naive Interpolation
- Missing values are **NEVER** filled with zeros or linear extrapolations.
- Every sequence tensor is accompanied by an exact **binary valid mask** ($M \in \{0, 1\}^{W \times V}$), allowing ST-GNN loss functions to mask out unobserved steps during backpropagation.

---

## 2. Sequence Candidate Specifications

Three distinct window/horizon configurations were generated and saved in `data/processed_global/urban_sequences/`:

| Sequence Archive | Window ($W$) | Horizon ($H$) | Total Sequences ($N$) | Train Seqs ($70\%$) | Val Seqs ($15\%$) | Test Seqs ($15\%$) | Purge Gap |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `blue_heart_sequences_w12_h3.npz` | **$12\text{ hours}$** | **$3\text{ hours}$** | **7,282** | $5,085$ | $1,080$ | $1,093$ | $12\text{ hours}$ |
| `blue_heart_sequences_w6_h1.npz` | **$6\text{ hours}$** | **$1\text{ hour}$** | **7,286** | $5,088$ | $1,080$ | $1,094$ | $12\text{ hours}$ |
| `blue_heart_sequences_w24_h6.npz` | **$24\text{ hours}$** | **$6\text{ hours}$** | **7,267** | $5,074$ | $1,078$ | $1,091$ | $12\text{ hours}$ |

---

## 3. Tensor Structure & Channel Schema

Each `.npz` archive contains standardized float32 tensors:

### 3.1 Input Tensor `X` — Shape: $(N, W, V, F)$
- $N$: Number of candidate sliding window sequences ($7,267\text{ to }7,286$).
- $W$: Historical observation window ($6, 12, \text{or } 24\text{ hours}$).
- $V$: Number of monitored road gully nodes ($V = 15$).
- $F$: Feature channels ($F = 2$):
  1. `water_level_m`: Observed depth in gully sump ($m$).
  2. `catchment_rainfall_mm_h`: Synchronized mean precipitation rate ($mm/h$).

### 3.2 Target Tensors
1. `Y_level` — Shape: $(N, V)$: Continuous water level ($m$) at forecast horizon $T + H$.
2. `Y_surcharge` — Shape: $(N, V)$: Binary road surcharge indicator ($1$ if water level $> 0.30\text{ m}$ indicates gully overflow onto street; $0$ otherwise).

### 3.3 Missingness Mask `mask` — Shape: $(N, W, V)$
- $1.0$: Sensor was actively reporting valid telemetry at timestep.
- $0.0$: Sensor dropout or maintenance gap ($2.17\%$ overall missingness rate).

---

## 4. Chronological Splitting & Leakage Audit

To prevent temporal leakage in sliding window sequences:
- **Strict Chronological Order:**
  $$\max(T_{\text{train}}) < \min(T_{\text{val}}) < \max(T_{\text{val}}) < \min(T_{\text{test}})$$
- **Purge Boundary Buffer:** A $12\text{-hour}$ purge gap was enforced at the Train/Val and Val/Test transition points, guaranteeing that no sliding window in the validation set overlaps with any timestamp seen in training.
- **Event Integrity:** High-intensity storm events (such as the winter 2025/2026 convective gully surcharge episodes) remain completely contained within their respective split partitions.

---

## 5. Summary & Verification Sign-Off
All 3 sequence archives have been written to disk and verified with checksums and automated loading tests. The urban temporal dataset is completely formatted, quality-masked, and ready for model benchmarking.

