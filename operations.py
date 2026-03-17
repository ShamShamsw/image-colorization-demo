"""Business logic for Project 49: Image Colorization Demo."""

from __future__ import annotations

import math
import random
import time
from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List, Tuple

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt

from models import (
    create_colorization_config,
    create_history_entry,
    create_image_case,
    create_pixel_record,
    create_runtime_point,
    create_session_summary,
    create_strategy_result,
)
from storage import (
    OUTPUTS_DIR,
    ensure_data_dirs,
    load_history,
    load_image_library,
    load_run_catalog,
    save_benchmark_file,
    save_history,
    save_image_library,
    save_run_record,
    save_trace_file,
)


PLOT_COLORS = {
    'warm_map': '#d95f02',
    'cool_map': '#1b9e77',
    'adaptive_blend': '#2c3e50',
    'selected_plan': '#e76f51',
}


def _session_id() -> str:
    """Build a compact session ID from UTC timestamp."""
    return datetime.utcnow().strftime('%Y%m%d_%H%M%S')


def _clamp_channel(value: float) -> int:
    """Clamp one RGB channel to integer [0, 255]."""
    return int(min(255, max(0, round(value))))


def _default_image_library() -> List[Dict[str, Any]]:
    """Return deterministic starter image profiles used on first run."""
    return [
        create_image_case(
            image_id='img_001',
            label='street_evening',
            name='City Street At Dusk',
            base_tone=0.44,
            contrast=0.52,
            warmth_bias=0.76,
            texture_strength=0.35,
            description='Warm neon-like scene with medium contrast.',
            tags=['street', 'warm', 'demo'],
        ),
        create_image_case(
            image_id='img_002',
            label='forest_morning',
            name='Forest Canopy',
            base_tone=0.57,
            contrast=0.46,
            warmth_bias=0.34,
            texture_strength=0.49,
            description='Cool and green leaning scene with textured gradients.',
            tags=['forest', 'cool', 'nature'],
        ),
        create_image_case(
            image_id='img_003',
            label='desert_sunrise',
            name='Desert Sunrise',
            base_tone=0.63,
            contrast=0.41,
            warmth_bias=0.88,
            texture_strength=0.22,
            description='Bright warm scene with soft transitions.',
            tags=['desert', 'sunrise', 'warm'],
        ),
        create_image_case(
            image_id='img_004',
            label='mountain_lake',
            name='Mountain Lake',
            base_tone=0.49,
            contrast=0.58,
            warmth_bias=0.28,
            texture_strength=0.31,
            description='Crisp cool palette with deeper shadows.',
            tags=['mountain', 'lake', 'cool'],
        ),
    ]


def _generate_grayscale_grid(
    image_case: Dict[str, Any],
    width: int,
    height: int,
    rng: random.Random,
) -> List[Dict[str, int]]:
    """Generate a deterministic synthetic grayscale image grid."""
    pixels: List[Dict[str, int]] = []
    base = float(image_case['base_tone'])
    contrast = float(image_case['contrast'])
    texture = float(image_case['texture_strength'])

    for y in range(height):
        y_ratio = y / max(1, height - 1)
        for x in range(width):
            x_ratio = x / max(1, width - 1)
            wave = 0.5 + (0.5 * math.sin((x_ratio * 3.6 + y_ratio * 2.3) * math.pi))
            band = 0.5 + (0.5 * math.cos((y_ratio * 4.1 - x_ratio * 1.7) * math.pi))
            texture_noise = rng.uniform(-0.5, 0.5) * texture
            intensity_float = base + ((wave - 0.5) * contrast) + ((band - 0.5) * contrast * 0.4) + texture_noise
            intensity = _clamp_channel(intensity_float * 255.0)
            pixels.append({'x': x, 'y': y, 'intensity': intensity})
    return pixels


def _reference_rgb(intensity: int, image_case: Dict[str, Any]) -> List[int]:
    """Generate reference RGB color for one grayscale intensity sample."""
    warm = float(image_case['warmth_bias'])
    tone = float(intensity)
    cool = 1.0 - warm

    red = (tone * (0.58 + 0.34 * warm)) + (22 * warm)
    green = (tone * (0.66 + 0.11 * cool)) + (10 * (0.5 + cool))
    blue = (tone * (0.54 + 0.38 * cool)) + (18 * cool)
    return [_clamp_channel(red), _clamp_channel(green), _clamp_channel(blue)]


def _predict_rgb(strategy: str, intensity: int) -> List[int]:
    """Predict RGB values for one pixel using a selected strategy."""
    tone = float(intensity)
    normalized = tone / 255.0

    warm_guess = [
        _clamp_channel((tone * 1.14) + 18),
        _clamp_channel((tone * 0.93) + 12),
        _clamp_channel((tone * 0.67) + 4),
    ]
    cool_guess = [
        _clamp_channel((tone * 0.72) + 5),
        _clamp_channel((tone * 0.95) + 11),
        _clamp_channel((tone * 1.17) + 21),
    ]

    if strategy == 'warm_map':
        return warm_guess
    if strategy == 'cool_map':
        return cool_guess

    warm_weight = 0.25 + (0.65 * normalized)
    cool_weight = 1.0 - warm_weight
    return [
        _clamp_channel((warm_guess[0] * warm_weight) + (cool_guess[0] * cool_weight)),
        _clamp_channel((warm_guess[1] * 0.5) + (cool_guess[1] * 0.5)),
        _clamp_channel((warm_guess[2] * (0.28 + 0.3 * normalized)) + (cool_guess[2] * (0.72 - 0.3 * normalized))),
    ]


def _pixel_error(predicted: List[int], reference: List[int]) -> float:
    """Compute normalized absolute channel error for one pixel."""
    channel_error = sum(abs(predicted[index] - reference[index]) for index in range(3)) / 3.0
    return channel_error / 255.0


def _run_strategy(
    strategy: str,
    image_case: Dict[str, Any],
    width: int,
    height: int,
    rng: random.Random,
) -> Dict[str, Any]:
    """Run one colorization strategy over a synthetic grayscale grid."""
    grayscale_pixels = _generate_grayscale_grid(image_case, width, height, rng)

    pixels: List[Dict[str, Any]] = []
    cumulative_error = 0.0
    mse_total = 0.0
    close_match_count = 0

    for index, pixel in enumerate(grayscale_pixels, start=1):
        intensity = int(pixel['intensity'])
        predicted = _predict_rgb(strategy, intensity)
        reference = _reference_rgb(intensity, image_case)
        error = _pixel_error(predicted, reference)
        cumulative_error += error

        squared_error = sum((predicted[channel] - reference[channel]) ** 2 for channel in range(3)) / 3.0
        mse_total += squared_error
        if error <= 0.065:
            close_match_count += 1

        pixels.append(
            create_pixel_record(
                pixel_index=index,
                strategy=strategy,
                x=int(pixel['x']),
                y=int(pixel['y']),
                intensity=intensity,
                predicted_rgb=predicted,
                reference_rgb=reference,
                pixel_error=error,
                cumulative_error=cumulative_error,
            )
        )

    count = max(1, len(pixels))
    mean_pixel_error = cumulative_error / count
    mse = mse_total / count
    if mse <= 1e-12:
        psnr_estimate = 99.0
    else:
        psnr_estimate = 20.0 * math.log10(255.0) - (10.0 * math.log10(mse))
    pixel_match_pct = (close_match_count / count) * 100.0

    return create_strategy_result(
        strategy=strategy,
        mean_pixel_error=mean_pixel_error,
        psnr_estimate=psnr_estimate,
        cumulative_error=cumulative_error,
        pixel_match_pct=pixel_match_pct,
        pixels=pixels,
        feasible=bool(pixels),
    )


def _compare_strategies(
    image_case: Dict[str, Any],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Run configured colorization strategies for side-by-side comparison."""
    results: List[Dict[str, Any]] = []
    base_seed = int(config['random_seed'])
    for offset, strategy in enumerate(config['enabled_strategies'], start=1):
        strategy_rng = random.Random(base_seed + (offset * 97))
        results.append(
            _run_strategy(
                strategy=strategy,
                image_case=image_case,
                width=config['grid_width'],
                height=config['grid_height'],
                rng=strategy_rng,
            )
        )
    return results


def _benchmark_runtime(config: Dict[str, Any], image_case: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Benchmark strategy runtime across increasing synthetic image sizes."""
    points: List[Dict[str, Any]] = []
    base_seed = int(config['random_seed'])

    for width in config['benchmark_widths']:
        height = max(12, int(width * 0.67))
        for strategy_index, strategy in enumerate(config['enabled_strategies'], start=1):
            for trial in range(1, config['benchmark_trials'] + 1):
                trial_seed = base_seed + (width * 13) + (strategy_index * 101) + trial
                trial_rng = random.Random(trial_seed)
                started = time.perf_counter()
                _run_strategy(strategy, image_case, width, height, trial_rng)
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                points.append(create_runtime_point(strategy, float(width), trial, elapsed_ms))
    return points


def _aggregate_runtime(points: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, float]]]:
    """Average runtime benchmark points by strategy and image width."""
    grouped: Dict[str, Dict[float, List[float]]] = defaultdict(lambda: defaultdict(list))
    for point in points:
        grouped[point['series']][point['size']].append(point['elapsed_ms'])

    summary: Dict[str, List[Dict[str, float]]] = {}
    for strategy, buckets in grouped.items():
        rows: List[Dict[str, float]] = []
        for size in sorted(buckets):
            rows.append({'size': size, 'elapsed_ms': round(mean(buckets[size]), 6)})
        summary[strategy] = rows
    return summary


def _save_runtime_chart(runtime_summary: Dict[str, List[Dict[str, float]]], session_id: str) -> str:
    """Persist benchmark runtime chart."""
    figure, axis = plt.subplots(figsize=(9.2, 5.0))
    for series, rows in runtime_summary.items():
        axis.plot(
            [row['size'] for row in rows],
            [row['elapsed_ms'] for row in rows],
            marker='o',
            linewidth=2,
            label=series.replace('_', ' ').title(),
            color=PLOT_COLORS.get(series, '#6c757d'),
        )
    axis.set_title('Average Runtime By Resolution And Strategy')
    axis.set_xlabel('Image width (pixels)')
    axis.set_ylabel('Elapsed time (ms)')
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    figure.tight_layout()
    file_path = OUTPUTS_DIR / f'strategy_runtime_{session_id}.png'
    figure.savefig(file_path, dpi=150)
    plt.close(figure)
    return str(file_path)


def _save_error_chart(selected_pixels: List[Dict[str, Any]], session_id: str) -> str:
    """Persist cumulative error trend chart for selected strategy."""
    figure, axis = plt.subplots(figsize=(8.8, 4.8))
    if selected_pixels:
        axis.plot(
            [int(row['pixel_index']) for row in selected_pixels],
            [float(row['cumulative_error']) for row in selected_pixels],
            marker='o',
            markersize=2.0,
            linewidth=1.8,
            color=PLOT_COLORS['selected_plan'],
        )
    axis.set_title('Cumulative Color Error Trend Across Demo Image')
    axis.set_xlabel('Pixel index')
    axis.set_ylabel('Cumulative normalized error')
    axis.grid(alpha=0.25)
    figure.tight_layout()
    file_path = OUTPUTS_DIR / f'error_trend_{session_id}.png'
    figure.savefig(file_path, dpi=150)
    plt.close(figure)
    return str(file_path)


def _image_preview_points(pixels: List[Dict[str, Any]], max_rows: int) -> List[Dict[str, Any]]:
    """Build evenly sampled pixel previews across one colorization trace."""
    if not pixels:
        return []
    interval = max(1, len(pixels) // max(1, max_rows))
    selected = [pixels[index] for index in range(0, len(pixels), interval)]
    return selected[:max_rows]


def load_colorization_profile() -> Dict[str, Any]:
    """Return startup profile built from previously saved catalogs."""
    ensure_data_dirs()
    run_catalog = load_run_catalog()
    library = load_image_library()
    history = load_history()
    recent_runs = [
        f"{item.get('session_id', '')}:{item.get('best_strategy', '')}:{item.get('demo_image_label', '')}"
        for item in run_catalog[-5:]
    ]
    return {
        'catalog_file': 'data/runs.json',
        'library_file': 'data/image_sets.json',
        'history_file': 'data/colorization_history.json',
        'runs_stored': len(run_catalog),
        'images_available': len(library),
        'history_entries': len(history),
        'recent_runs': recent_runs,
    }


def run_core_flow() -> Dict[str, Any]:
    """Run one complete colorization simulation, benchmark, and plotting session."""
    ensure_data_dirs()
    config = create_colorization_config()
    session_id = _session_id()
    started = time.perf_counter()

    image_library = load_image_library()
    if not image_library:
        image_library = _default_image_library()
        save_image_library(image_library)

    demo_image = next(
        (item for item in image_library if item['label'] == config['demo_image_label']),
        image_library[0],
    )

    comparison = _compare_strategies(demo_image, config)
    selected_result = next((item for item in comparison if item['strategy'] == config['strategy']), None)
    if selected_result is None and comparison:
        selected_result = min(comparison, key=lambda item: float(item['mean_pixel_error']))
    selected_result = selected_result or create_strategy_result('none', 0.0, 0.0, 0.0, 0.0, [], False)

    history = load_history()
    history.append(
        create_history_entry(
            'colorization_session',
            {
                'session_id': session_id,
                'strategy': selected_result['strategy'],
                'pixels_processed': len(selected_result['pixels']),
                'mean_pixel_error': selected_result['mean_pixel_error'],
                'psnr_estimate': selected_result['psnr_estimate'],
            },
        )
    )
    sampled_pixels = _image_preview_points(selected_result['pixels'], max_rows=20)
    for pixel in sampled_pixels:
        history.append(create_history_entry('colorized_pixel', pixel))
    history = history[-500:]
    history_file = save_history(history)

    runtime_points = _benchmark_runtime(config, demo_image)
    runtime_summary = _aggregate_runtime(runtime_points)

    trace_payload = {
        'session_id': session_id,
        'config': config,
        'image_case': demo_image,
        'strategy_comparison': comparison,
        'selected_result': selected_result,
        'history_file': history_file,
    }
    benchmark_payload = {
        'session_id': session_id,
        'runtime_points': runtime_points,
        'runtime_summary': runtime_summary,
    }

    runtime_chart_file = ''
    error_chart_file = ''
    if config['include_runtime_plot']:
        runtime_chart_file = _save_runtime_chart(runtime_summary, session_id)
    if config['include_error_plot']:
        error_chart_file = _save_error_chart(selected_result['pixels'], session_id)

    trace_file = save_trace_file(trace_payload, session_id)
    benchmark_file = save_benchmark_file(benchmark_payload, session_id)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    average_by_series = {
        series: mean(row['elapsed_ms'] for row in rows)
        for series, rows in runtime_summary.items()
        if rows
    }
    best_strategy = min(average_by_series.items(), key=lambda item: item[1])[0] if average_by_series else ''

    metrics = {
        'best_strategy': best_strategy,
        'best_avg_runtime_ms': round(average_by_series.get(best_strategy, 0.0), 6),
        'selected_mean_pixel_error': round(float(selected_result['mean_pixel_error']), 6),
        'selected_psnr_estimate': round(float(selected_result['psnr_estimate']), 6),
        'selected_pixel_match_pct': round(float(selected_result['pixel_match_pct']), 6),
        'history_size': len(history),
    }

    artifacts = {
        'trace_file': trace_file,
        'benchmark_file': benchmark_file,
        'runtime_chart_file': runtime_chart_file,
        'error_chart_file': error_chart_file,
        'history_file': history_file,
    }

    pixel_previews = _image_preview_points(selected_result['pixels'], config['max_preview_rows'])
    summary = create_session_summary(
        session_id=session_id,
        images_available=len(image_library),
        demo_image_label=demo_image['label'],
        strategy_selected=selected_result['strategy'],
        strategy_runs=len(comparison),
        pixels_processed=len(selected_result['pixels']),
        runtime_points=len(runtime_points),
        elapsed_ms=elapsed_ms,
        artifacts=artifacts,
        pixel_previews=pixel_previews,
        metrics=metrics,
    )
    summary['history_previews'] = history[-config['max_preview_rows'] :]
    summary['max_preview_rows'] = config['max_preview_rows']
    summary['selected_result'] = selected_result

    run_record = dict(summary)
    session_file = save_run_record(run_record)
    summary['artifacts']['session_file'] = session_file
    return summary
