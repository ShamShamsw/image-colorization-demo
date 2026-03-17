"""Presentation helpers for Project 49: Image Colorization Demo."""

from typing import Any, Dict, List


def format_header() -> str:
    """Format session header banner."""
    return '=' * 70 + '\n' + '   IMAGE COLORIZATION DEMO\n' + '=' * 70


def format_startup_guide(config: Dict[str, Any], profile: Dict[str, Any]) -> str:
    """Format startup configuration and historical profile."""
    recent = ', '.join(profile.get('recent_runs', [])) or 'None yet'
    lines = [
        '',
        'Configuration:',
        f"   Project type:           {config['project_type']}",
        f"   Strategy selected:      {config['strategy']}",
        f"   Strategy set:           {', '.join(config['enabled_strategies'])}",
        f"   Demo image label:       {config['demo_image_label']}",
        f"   Grid width:             {config['grid_width']}",
        f"   Grid height:            {config['grid_height']}",
        f"   Benchmark widths:       {', '.join(str(value) for value in config['benchmark_widths'])}",
        f"   Trials per width:       {config['benchmark_trials']}",
        f"   Runtime chart:          {config['include_runtime_plot']}",
        f"   Error chart:            {config['include_error_plot']}",
        f"   Max preview rows:       {config['max_preview_rows']}",
        f"   Random seed:            {config['random_seed']}",
        '',
        'Startup:',
        '   Data directory:         data/',
        '   Outputs directory:      data/outputs/',
        (
            f"   Image library:          {profile['library_file']} "
            f"(loaded {profile['images_available']} images)"
        ),
        (
            f"   Run catalog:            {profile['catalog_file']} "
            f"(loaded {profile['runs_stored']} runs)"
        ),
        (
            f"   Colorization history:   {profile['history_file']} "
            f"(loaded {profile['history_entries']} entries)"
        ),
        f"   Recent runs:            {recent}",
        '',
        '---',
    ]
    return '\n'.join(lines)


def _clip_preview(value: str, width: int = 36) -> str:
    """Return a compact preview string for table output."""
    compact = value.replace('\n', ' ').strip()
    if len(compact) <= width:
        return compact
    return compact[: width - 3] + '...'


def format_pixel_table(pixels: List[Dict[str, Any]]) -> str:
    """Format strategy pixel preview table."""
    if not pixels:
        return 'No pixel previews generated.'
    lines = [
        'Pixel previews:',
        '   # | X  | Y  | Gray | Predicted RGB      | Reference RGB      | Error',
        '   --+----+----+------+--------------------+--------------------+------',
    ]
    for row in pixels:
        lines.append(
            '   '
            f"{int(row.get('pixel_index', 0)):<2} | "
            f"{int(row.get('x', 0)):<2} | "
            f"{int(row.get('y', 0)):<2} | "
            f"{int(row.get('intensity', 0)):<4} | "
            f"{_clip_preview(str(row.get('predicted_rgb', [])), 18):<18} | "
            f"{_clip_preview(str(row.get('reference_rgb', [])), 18):<18} | "
            f"{float(row.get('pixel_error', 0.0)):<.4f}"
        )
    return '\n'.join(lines)


def format_history_table(history: List[Dict[str, Any]], max_rows: int) -> str:
    """Format history preview table."""
    if not history:
        return 'No history entries available.'
    lines = [
        'Recent history:',
        '   Event type         | Preview                              | Created at',
        '   -------------------+--------------------------------------+----------------------',
    ]
    for row in history[-max_rows:]:
        payload = row.get('payload', {})
        if row.get('event_type') == 'colorization_session':
            preview = (
                f"{payload.get('strategy', '')} | "
                f"pixels={payload.get('pixels_processed', 0)} | "
                f"error={payload.get('mean_pixel_error', 0)}"
            )
        elif row.get('event_type') == 'colorized_pixel':
            preview = (
                f"{payload.get('pixel_index', 0)}. "
                f"({payload.get('x', 0)}, {payload.get('y', 0)}) "
                f"e={payload.get('pixel_error', 0)}"
            )
        else:
            preview = str(payload)
        lines.append(
            '   '
            f"{_clip_preview(str(row.get('event_type', '')), 19):<19} | "
            f"{_clip_preview(preview, 36):<36} | "
            f"{_clip_preview(str(row.get('created_at', '')), 20):<20}"
        )
    return '\n'.join(lines)


def format_run_report(summary: Dict[str, Any]) -> str:
    """Format final session report."""
    artifacts = summary.get('artifacts', {})
    metrics = summary.get('metrics', {})
    selected_result = summary.get('selected_result', {})
    lines = [
        '',
        'Session complete:',
        f"   Session ID:             {summary['session_id']}",
        f"   Images available:       {summary['images_available']}",
        f"   Demo image label:       {summary['demo_image_label']}",
        f"   Strategy selected:      {summary['strategy_selected']}",
        f"   Strategy runs:          {summary['strategy_runs']}",
        f"   Pixels processed:       {summary['pixels_processed']}",
        f"   Runtime points:         {summary['runtime_points']}",
        f"   Elapsed time:           {summary['elapsed_ms']:.2f} ms",
        '',
        (
            'Colorization metrics: '
            f"best_strategy={metrics.get('best_strategy', 'N/A')} | "
            f"best_avg_runtime_ms={metrics.get('best_avg_runtime_ms', 0.0):.6f} | "
            f"selected_mean_pixel_error={metrics.get('selected_mean_pixel_error', 0.0):.6f} | "
            f"selected_psnr_estimate={metrics.get('selected_psnr_estimate', 0.0):.6f} | "
            f"selected_pixel_match_pct={metrics.get('selected_pixel_match_pct', 0.0):.6f} | "
            f"history_size={metrics.get('history_size', 0)}"
        ),
        '',
        (
            'Selected strategy totals: '
            f"mean_pixel_error={float(selected_result.get('mean_pixel_error', 0.0)):.6f} | "
            f"psnr_estimate={float(selected_result.get('psnr_estimate', 0.0)):.6f} | "
            f"pixel_match_pct={float(selected_result.get('pixel_match_pct', 0.0)):.3f}"
        ),
        '',
        format_pixel_table(summary.get('pixel_previews', [])),
        '',
        format_history_table(summary.get('history_previews', []), max_rows=summary.get('max_preview_rows', 8)),
        '',
        'Artifacts saved:',
        f"   Session record:         {artifacts.get('session_file', 'N/A')}",
        f"   Trace bundle:           {artifacts.get('trace_file', 'N/A')}",
        f"   Benchmark file:         {artifacts.get('benchmark_file', 'N/A')}",
        f"   Runtime chart:          {artifacts.get('runtime_chart_file', 'N/A')}",
        f"   Error chart:            {artifacts.get('error_chart_file', 'N/A')}",
    ]
    return '\n'.join(lines)


def format_message(message: str) -> str:
    """Format a user-facing message string."""
    return f'[Project 49] {message}'
