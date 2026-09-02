# Visualization protocol

Use this protocol when a result is turned into a figure and again when the
paper is assembled. A figure is evidence for a named claim, not decoration and
not proof merely because it looks technical.

## Figure contract

Before plotting, register:

| Field | Meaning |
|---|---|
| `figure_id` | Stable ID such as `Q2-F03` |
| `claim` | The one sentence this figure supports |
| `decision` | What a reader can decide or understand from it |
| `source_paths` | Data/result files used, never “from code” |
| `generator` | Script/notebook path and relevant function or cell |
| `chart_type` | Chosen chart and rejected misleading alternative |
| `encoding` | x/y/color/size/facet meanings and units |
| `uncertainty` | Interval, distribution, scenarios, or why none applies |
| `caption` | What is shown, conditions, and the takeaway |

Store these records in `figures/figure_registry.json`. A figure without a named
claim or reproducible source path is not paper-ready.

## Choose the display by analytical task

| Task | Usually appropriate | Common misuse |
|---|---|---|
| Trend over ordered time | line with actual sampling intervals | smoothed curve hiding sparse points |
| Compare categories | sorted dot/bar chart | 3-D bars or pie chart with many slices |
| Distribution | ECDF, histogram with stated bins, box/violin plus points | reporting only the mean |
| Relationship | scatter with transparent points and justified fit | connecting unordered observations |
| Model performance | residual/QQ/calibration/error-by-split panels | only train-set fit |
| Optimization | decision profile, trade-off/Pareto plot, constraint slack | objective value with no feasible-context view |
| Sensitivity | tornado, response curve, heatmap for joint effects | arbitrary ±10% without a basis |
| Spatial result | map with scale, legend, projection/source | rainbow color map without units |
| Exact lookup | table | dense chart that forces visual estimation |

The table is routing guidance, not a mandatory style catalogue. Use a domain
standard when it communicates the evidence more faithfully.

## Construction rules

- One main question per figure. Split unrelated messages instead of making a
  dashboard-shaped collage.
- Use a colorblind-safe palette and do not encode meaning by color alone.
- Put units in axis labels or headers. Distinguish percentage points from
  percentages and power from energy.
- Show observed data separately from fitted, extrapolated, or simulated values.
- Show uncertainty when it affects the claim; state the interval/scenario
  construction in the caption.
- Do not truncate a quantitative axis when the truncation changes the perceived
  effect without an explicit visual break and explanation.
- Avoid dual axes, 3-D effects, excessive gradients, and default rainbow maps
  unless the encoding has a defensible analytical purpose.
- Use consistent names, colors, ordering, precision, and scenario definitions
  across the paper.
- Export at the paper's final physical size. Prefer vector PDF for line art and
  also create a 300 dpi PNG for inspection; raster heatmaps/images may remain
  raster when vector output is impractical.
- Captions must be self-contained: data/scope, encoding, condition, and the
  conclusion the figure supports.

## Shared plotting helper

Copy `<skill>/templates/shared/plot_style.py` into the project utility directory
and import it from figure-generating scripts. `save_figure` creates PNG/PDF
outputs plus a `.figure.json` sidecar and reports structural warnings. It cannot
judge whether a chart is substantively truthful; the team must still inspect
the final-size output and compare it with the underlying data.

## Figure review gate

Review every figure at the width used in the final PDF, not only in a notebook.
Check:

1. claim and source paths resolve;
2. numbers agree with the saved results;
3. axes, units, legends, category order, and sample/scenario definitions are
   unambiguous;
4. uncertainty and failure cases are visible when material;
5. the caption states the takeaway without claiming causality the analysis did
   not establish;
6. grayscale/print and colorblind reading remain distinguishable;
7. labels remain readable after insertion into the compiled paper.

Corrupt files, unsupported claims, wrong units, misleading encodings, or
unreadable final-size labels are high-severity issues. Visual plainness alone is
not a defect; clarity and evidential honesty take priority over decoration.
