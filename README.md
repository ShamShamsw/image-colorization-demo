# Beginner Project 49: Image Colorization Demo

**Time:** 4-6 hours  
**Difficulty:** Intermediate Beginner  
**Focus:** Deterministic grayscale-to-color strategy simulation, pixel-level error analysis, persistent history, and runtime/error visualizations

---

## Why This Project?

Image colorization is a great way to learn computer vision workflows without needing a heavy deep-learning stack on day one. This project keeps the pipeline lightweight and reproducible by using synthetic grayscale scenes, reference color generation, and rule-based colorization strategies that can be benchmarked side by side.

This project teaches end-to-end colorization workflow concepts where you can:

- load or auto-seed a reusable synthetic image library for deterministic demos,
- generate grayscale image grids with configurable tone, contrast, and texture,
- produce reference RGB targets from image profile characteristics,
- compare warm-map, cool-map, and adaptive blend colorization strategies,
- track per-pixel error and cumulative error across full image traversal,
- estimate quality with mean pixel error, PSNR proxy, and close-match percentage,
- persist session and sampled-pixel history for reproducible audit trails,
- benchmark strategy runtime across increasing image widths,
- visualize runtime behavior as a multi-series chart,
- visualize cumulative color error trend for selected strategy,
- export trace bundles and benchmark bundles to JSON for inspection,
- persist historical run summaries for repeatable profiling,
- and print a readable terminal report with pixel previews and artifact paths.

---

## More Projects

You can access this project and more in this separate repository:

[student-interview-prep](https://github.com/ShamShamsw/student-interview-prep.git)

---

## What You Will Build

You will build an image colorization simulation workflow that:

1. Loads image definitions from `data/image_sets.json` (or seeds a starter set of 4 image profiles).
2. Selects a deterministic demo image profile for strategy walkthroughs.
3. Generates a synthetic grayscale grid for the configured width and height.
4. Creates reference RGB targets from profile warmth/tone settings.
5. Simulates warm-map, cool-map, and adaptive blend strategies over all pixels.
6. Compares strategy quality using mean pixel error, PSNR estimate, and pixel match rate.
7. Stores session and sampled-pixel events in `data/colorization_history.json`.
8. Benchmarks strategy runtime across configured image widths and repeated trials.
9. Aggregates runtime points into strategy-level average performance summaries.
10. Saves a strategy runtime chart under `data/outputs/`.
11. Saves a cumulative error trend chart under `data/outputs/`.
12. Persists trace, benchmark, and run-summary artifacts for future sessions.
13. Maintains a run catalog in `data/runs.json` for startup profiling.

---

## Requirements

- Python 3.11+
- `matplotlib`

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Example Session

```text
======================================================================
   IMAGE COLORIZATION DEMO
======================================================================

Configuration:
   Project type:           image_colorization_demo
   Strategy selected:      adaptive_blend
   Strategy set:           warm_map, cool_map, adaptive_blend
   Demo image label:       street_evening
   Grid width:             48
   Grid height:            32
   Benchmark widths:       24, 48, 72, 96, 128
   Trials per width:       4
   Runtime chart:          True
   Error chart:            True
   Max preview rows:       8
   Random seed:            42

Startup:
   Data directory:         data/
   Outputs directory:      data/outputs/
   Image library:          data/image_sets.json (loaded 0 images)
   Run catalog:            data/runs.json (loaded 0 runs)
   Colorization history:   data/colorization_history.json (loaded 0 entries)
   Recent runs:            None yet

---

Session complete:
   Session ID:             20260317_235921
   Images available:       4
   Demo image label:       street_evening
   Strategy selected:      adaptive_blend
   Strategy runs:          3
   Pixels processed:       1536
   Runtime points:         60
   Elapsed time:           221.34 ms

Colorization metrics: best_strategy=warm_map | best_avg_runtime_ms=2.901128 | selected_mean_pixel_error=0.085732 | selected_psnr_estimate=18.491104 | selected_pixel_match_pct=46.158854 | history_size=21

Selected strategy totals: mean_pixel_error=0.085732 | psnr_estimate=18.491104 | pixel_match_pct=46.159

Pixel previews:
   # | X  | Y  | Gray | Predicted RGB      | Reference RGB      | Error
   --+----+----+------+--------------------+--------------------+------
   1  | 0  | 0  | 122  | [121, 122, 139]    | [163, 102, 86]     | 0.1503
   2  | 6  | 0  | 140  | [139, 139, 158]    | [186, 117, 99]     | 0.1673
   3  | 12 | 0  | 157  | [155, 156, 176]    | [208, 131, 110]    | 0.1870

Artifacts saved:
   Session record:         data/outputs/run_20260317_235921.json
   Trace bundle:           data/outputs/trace_20260317_235921.json
   Benchmark file:         data/outputs/benchmark_20260317_235921.json
   Runtime chart:          data/outputs/strategy_runtime_20260317_235921.png
   Error chart:            data/outputs/error_trend_20260317_235921.png
```

---

## Run

```bash
python main.py
```
