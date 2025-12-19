# Adaptive Window Sizing

PythonSearch now supports adaptive window sizing that automatically adjusts the terminal window size based on your display characteristics. This ensures the search interface looks consistent and appropriately sized across different monitors and resolutions.

## Features

### Automatic Display Detection
- **macOS**: Uses `osascript` and `system_profiler` to detect display resolution and characteristics
- **Linux**: Uses `xrandr` (X11) or `wlr-randr` (Wayland) to get display information
- **Cross-platform**: Falls back to sensible defaults on unsupported platforms

### Adaptive Sizing Algorithm
The adaptive sizing algorithm considers:
- Display resolution (width × height)
- DPI (dots per inch) when available
- Display scale factor for high-DPI displays
- Maintains reasonable bounds to ensure usability

### Display Categories
Windows are automatically sized based on display categories:
- **Small displays** (≤1366px width): Laptops, small monitors
- **Standard HD** (≤1920px width): Most desktop monitors
- **QHD displays** (≤2560px width): High-resolution monitors
- **4K+ displays** (>2560px width): Ultra-high resolution displays

## Configuration Options

### 1. Automatic Adaptive Sizing (Default)
```python
from python_search.configuration.configuration import PythonSearchConfiguration

config = PythonSearchConfiguration(
    adaptive_window_sizing=True  # This is the default
)
```

### 2. Preset Sizes
Choose from predefined size categories:
```python
config = PythonSearchConfiguration(
    adaptive_window_sizing=True,
    window_size_preset="medium"  # Options: "small", "medium", "large"
)
```

### 3. Custom Fixed Size
Override adaptive sizing with a fixed size:
```python
config = PythonSearchConfiguration(
    custom_window_size=(100, 15)  # (width_chars, height_chars)
)
```

### 4. Disable Adaptive Sizing
```python
config = PythonSearchConfiguration(
    adaptive_window_sizing=False
)
# This will use the default size (86c × 10c)
```

## Environment Variable Overrides

You can override window sizing and display detection at runtime using environment variables:

### Custom Window Size
```bash
export PYTHON_SEARCH_WINDOW_WIDTH='120c'
export PYTHON_SEARCH_WINDOW_HEIGHT='15c'
python_search
```

### Preset Size
```bash
export PYTHON_SEARCH_WINDOW_PRESET='large'
python_search
```

### Display Detection Override
If automatic display detection fails or you want to override it:
```bash
export DISPLAY_WIDTH='2560'
export DISPLAY_HEIGHT='1440'
python_search
```

### Combined Example
```bash
# Force specific display size and use large preset
export DISPLAY_WIDTH='3840'
export DISPLAY_HEIGHT='2160'
export PYTHON_SEARCH_WINDOW_PRESET='large'
python_search
```

## Testing Display Detection

Use the test script to check how your display is detected:

```bash
cd python_search/host_system
python test_display_detection.py
```

This will show:
- Your display resolution and characteristics
- Calculated adaptive window sizes
- Available preset sizes for your display
- Environment variable examples

## Example Output

```
=== Display Detection Test ===
Display Resolution: 2560x1440
DPI: 109.0
Scale Factor: 1.0

=== Adaptive Window Sizing Test ===
Adaptive Window Size: 103c x 12c
Small Adaptive Size: 72c x 10c
Large Adaptive Size: 144c x 18c

=== Preset Sizes ===
Small: 80c x 10c
Medium: 110c x 13c
Large: 150c x 18c
```

## Troubleshooting

### Display Detection Issues
If display detection fails, the system will:
1. Log a warning message
2. Fall back to default dimensions (1920×1080)
3. Use standard preset sizes

### Platform-Specific Notes

#### macOS
- Requires `osascript` for resolution detection
- May need accessibility permissions for some features
- Works best on macOS 10.14+

#### Linux
- Requires `xrandr` for X11 systems
- Requires `wlr-randr` for Wayland systems
- Falls back to environment variables if tools unavailable

#### Windows
- Currently uses fallback values
- Future versions may add Windows-specific detection

### Performance
- Display detection runs once per application launch
- Results are cached for the session
- Minimal performance impact on startup

## Migration from Fixed Sizing

If you were previously using custom window sizes, your configuration will continue to work unchanged. The adaptive sizing only activates when:
1. No `custom_window_size` is specified, AND
2. `adaptive_window_sizing` is True (default)

To migrate to adaptive sizing, simply remove the `custom_window_size` parameter from your configuration.
