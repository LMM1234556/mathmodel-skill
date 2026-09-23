# MATLAB visualization protocol

Use this protocol when a result becomes a figure and again when the paper is
assembled. All quantitative figures in this workflow are generated in MATLAB.
Python, R, or a solver may compute results, but they must export a stable
CSV/MAT file that MATLAB reads; their plotting libraries are not part of this
workflow, and screenshots or notebook-rendered charts are not paper-ready.

Non-data diagrams such as a hand-authored mechanism sketch are outside this
rule, but must be identified as diagrams rather than analytical figures.

## Figure contract

Before plotting, register:

| Field | Meaning |
|---|---|
| `figure_id` | Stable ID such as `Q2-F03` |
| `claim` | The one sentence this figure supports |
| `decision` | What a reader can decide or understand from it |
| `source_paths` | CSV/MAT/result files read by MATLAB, never “from code” |
| `generator` | MATLAB `.m` file and relevant function |
| `renderer` | Must be `MATLAB` for a quantitative figure |
| `chart_type` | Chosen chart |
| `chart_type_rationale` | Why this chart matches the task and what alternative was rejected |
| `encoding` | x/y/color/line/marker/facet meanings and units |
| `uncertainty` | Interval, distribution, scenarios, or why none applies |
| `caption` | What is shown, conditions, and the takeaway |

Store records in `figures/figure_registry.json`. A quantitative figure is not
paper-ready when `renderer != "MATLAB"`, its claim is unnamed, or its source
cannot be reproduced.

## Choose the display by analytical task

Run `mm_choose_chart(task)` as a starting recommendation, then record the
data-specific rationale. The helper cannot decide whether the data satisfy the
chart's assumptions.

| Analytical task | Usually appropriate | Required condition | Reject by default |
|---|---|---|---|
| Ordered time trend | line + observed markers; interval ribbon when needed | ordered x with meaningful spacing | smoothed curve hiding sparse observations |
| Category comparison | sorted horizontal bar or dot plot | common quantitative scale | 3-D bars; unsorted rainbow bars |
| Distribution | ECDF; histogram with justified bins; box/violin plus points | sample size and grouping disclosed | mean-only bar chart |
| Relationship | scatter + justified fit and interval | paired observations | connecting unordered observations |
| Model performance | residual, QQ, calibration, confusion matrix, error-by-split | out-of-sample or validation predictions | only training fit |
| Optimization | Pareto/trade-off, decision profile, constraint slack | feasibility and objective definitions shown | isolated objective value |
| Sensitivity | tornado, response curve, or two-factor heatmap | perturbation basis stated | arbitrary +/-10% without basis |
| Spatial result | map with scale, legend, projection/source | valid coordinates and geographic context | rainbow map without units |
| Matrix/intensity | sequential or diverging heatmap | ordered scale and meaningful center | categorical hues for continuous magnitude |
| Exact lookup | table, not a chart | exact values are the task | decorative dense chart |

If no row matches, use the domain-standard display only after writing its
assumptions and rejected alternative. Pie/donut, radar, dual-axis, 3-D, Sankey,
and chord diagrams require an explicit analytical reason; visual novelty is not
a reason.

## Semantic safeguards for specialized figures

- Radar charts are allowed only after all indicators are put on a comparable,
  direction-consistent scale. Never interpret polygon area as a quantitative
  overall score.
- Correlation heatmaps use a fixed `[-1, 1]` scale with zero as the diverging
  midpoint. Correlation networks must disclose edge threshold, multiple-testing
  control when inference is claimed, and cannot be described as causal.
- Prediction figures use the same held-out observations across models. Pair the
  observed-versus-predicted view with residual/calibration evidence; never draw
  an interval that was not computed.
- SHAP values and raw features must join by stable sample ID. Record output units,
  baseline, and an additivity check. SHAP, PDP, GAM response curves, feature
  importance, and partial correlation are model descriptions, not causal effects.
- Spatial figures must declare geometry type, coordinate reference system,
  spatial support and interpolation method. Do not interpolate discrete classes
  or imply coverage outside the observed/support domain.

## Color policy: vivid, controlled, and printable

- Use `mm_style` and its vivid colorblind-aware palette. Saturated colors are
  accents; the background stays white and gridlines remain light.
- Use one stable color for the same model/scenario across the paper. The focal
  series receives the strongest color; context series use gray or lower visual
  weight.
- Do not encode meaning by hue alone. Pair colors with line styles, markers,
  direct labels, or hatching.
- Use at most 6 simultaneous categorical colors in one panel. Beyond that,
  group, facet, highlight, or label directly.
- Use sequential colors for magnitude and diverging colors only around a
  meaningful midpoint. Do not use `jet`, default rainbow maps, or gradients as
  decoration.
- A vivid palette does not justify filling every object with a different
  color. Category bars use one color unless color itself carries a registered
  meaning.

## Construction rules

- One main question per figure. Split unrelated messages instead of making a
  dashboard-shaped collage.
- Put units in axis labels or headers. Distinguish percentage points from
  percentages and power from energy.
- Show observed data separately from fitted, extrapolated, or simulated values.
- Show uncertainty when it affects the claim; state its construction in the
  caption.
- Do not truncate a quantitative axis when truncation changes the perceived
  effect without an explicit break and explanation.
- Avoid dual axes, 3-D effects, excessive gradients, and chartjunk.
- Export at final physical size. Produce vector PDF plus 300 dpi PNG; raster
  heatmaps/images may use PNG when vector output is impractical.
- Captions must state data/scope, encoding, conditions, and takeaway.

## MATLAB helper workflow

Copy `<skill>/templates/shared/matlab/` into the project utility directory and:

1. save modeling outputs to `results/*.csv` or `results/*.mat`;
2. call `mm_choose_chart` and record the rationale;
3. create the MATLAB figure and call `mm_style`;
4. call `mm_export_figure` with the complete metadata struct.

`mm_export_figure` writes PNG/PDF, a `.figure.json` sidecar, and atomically
updates `figure_registry.json`. It blocks missing evidence metadata and severe
structural defects. It cannot determine scientific truth; compare every figure
with its source data at final paper size.

## Figure review gate

Check every inserted figure:

1. `renderer` is MATLAB and the `.m` generator resolves;
2. source paths resolve and numbers agree with saved results;
3. the chart type matches the analytical task and its rationale is credible;
4. axes, units, legends, order, and sample/scenario definitions are unambiguous;
5. uncertainty and failure cases are visible when material;
6. the caption does not claim causality the analysis did not establish;
7. grayscale and colorblind reading remain distinguishable;
8. labels remain readable at final PDF size.

Wrong chart type, non-MATLAB quantitative output, corrupt files,
unsupported claims, wrong units, misleading encodings, or unreadable labels are
high-severity issues. Visual plainness alone is not a defect.
