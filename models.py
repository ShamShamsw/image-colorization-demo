"""Data models for Project 49: Image Colorization Demo."""

from datetime import datetime
from typing import Any, Dict, List


def _utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.utcnow().isoformat(timespec='seconds') + 'Z'


def create_colorization_config(
    strategy: str = 'adaptive_blend',
    enabled_strategies: List[str] | None = None,
    demo_image_label: str = 'street_evening',
    grid_width: int = 48,
    grid_height: int = 32,
    benchmark_widths: List[int] | None = None,
    benchmark_trials: int = 4,
    include_runtime_plot: bool = True,
    include_error_plot: bool = True,
    max_preview_rows: int = 8,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """Create a validated configuration record for one simulator session."""
    strategies = (
        enabled_strategies if enabled_strategies else ['warm_map', 'cool_map', 'adaptive_blend']
    )
    benchmark_sizes = benchmark_widths if benchmark_widths else [24, 48, 72, 96, 128]
    normalized_strategy = str(strategy).strip().lower()
    selected_strategy = normalized_strategy if normalized_strategy in strategies else 'adaptive_blend'
    return {
        'project_type': 'image_colorization_demo',
        'strategy': selected_strategy,
        'enabled_strategies': [str(value) for value in strategies],
        'demo_image_label': str(demo_image_label),
        'grid_width': max(12, int(grid_width)),
        'grid_height': max(12, int(grid_height)),
        'benchmark_widths': [max(12, int(value)) for value in benchmark_sizes],
        'benchmark_trials': max(1, int(benchmark_trials)),
        'include_runtime_plot': bool(include_runtime_plot),
        'include_error_plot': bool(include_error_plot),
        'max_preview_rows': max(1, int(max_preview_rows)),
        'random_seed': int(random_seed),
        'created_at': _utc_timestamp(),
    }


def create_image_case(
    image_id: str,
    label: str,
    name: str,
    base_tone: float,
    contrast: float,
    warmth_bias: float,
    texture_strength: float,
    description: str,
    tags: List[str],
) -> Dict[str, Any]:
    """Create one reusable synthetic image definition record."""
    return {
        'image_id': str(image_id),
        'label': str(label),
        'name': str(name),
        'base_tone': min(0.95, max(0.05, float(base_tone))),
        'contrast': min(0.95, max(0.05, float(contrast))),
        'warmth_bias': min(1.0, max(0.0, float(warmth_bias))),
        'texture_strength': min(1.0, max(0.0, float(texture_strength))),
        'description': str(description),
        'tags': [str(tag) for tag in tags],
    }


def create_pixel_record(
    pixel_index: int,
    strategy: str,
    x: int,
    y: int,
    intensity: int,
    predicted_rgb: List[int],
    reference_rgb: List[int],
    pixel_error: float,
    cumulative_error: float,
) -> Dict[str, Any]:
    """Create one per-pixel simulation output record."""
    return {
        'pixel_index': int(pixel_index),
        'strategy': str(strategy),
        'x': int(x),
        'y': int(y),
        'intensity': int(intensity),
        'predicted_rgb': [int(value) for value in predicted_rgb],
        'reference_rgb': [int(value) for value in reference_rgb],
        'pixel_error': round(float(pixel_error), 6),
        'cumulative_error': round(float(cumulative_error), 6),
    }


def create_strategy_result(
    strategy: str,
    mean_pixel_error: float,
    psnr_estimate: float,
    cumulative_error: float,
    pixel_match_pct: float,
    pixels: List[Dict[str, Any]],
    feasible: bool,
) -> Dict[str, Any]:
    """Create one colorization strategy result record."""
    return {
        'strategy': str(strategy),
        'mean_pixel_error': round(float(mean_pixel_error), 6),
        'psnr_estimate': round(float(psnr_estimate), 6),
        'cumulative_error': round(float(cumulative_error), 6),
        'pixel_match_pct': round(float(pixel_match_pct), 6),
        'pixels': list(pixels),
        'feasible': bool(feasible),
    }


def create_runtime_point(series: str, size: float, trial: int, elapsed_ms: float) -> Dict[str, Any]:
    """Create one benchmark runtime point."""
    return {
        'series': str(series),
        'size': float(size),
        'trial': int(trial),
        'elapsed_ms': round(float(elapsed_ms), 6),
    }


def create_history_entry(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create one persistent history entry."""
    return {
        'event_type': str(event_type),
        'payload': dict(payload),
        'created_at': _utc_timestamp(),
    }


def create_session_summary(
    session_id: str,
    images_available: int,
    demo_image_label: str,
    strategy_selected: str,
    strategy_runs: int,
    pixels_processed: int,
    runtime_points: int,
    elapsed_ms: float,
    artifacts: Dict[str, Any],
    pixel_previews: List[Dict[str, Any]],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Create final session summary for reporting and persistence."""
    return {
        'session_id': str(session_id),
        'images_available': int(images_available),
        'demo_image_label': str(demo_image_label),
        'strategy_selected': str(strategy_selected),
        'strategy_runs': int(strategy_runs),
        'pixels_processed': int(pixels_processed),
        'runtime_points': int(runtime_points),
        'elapsed_ms': round(float(elapsed_ms), 5),
        'artifacts': dict(artifacts),
        'pixel_previews': list(pixel_previews),
        'metrics': dict(metrics),
        'finished_at': _utc_timestamp(),
    }


def create_record(**kwargs):
    """Backwards-compatible generic record factory."""
    return dict(kwargs)
