#!/usr/bin/env python3
"""
Test script for display detection and adaptive window sizing
"""

import logging
from python_search.host_system.display_detection import (
    DisplayDetector,
    AdaptiveWindowSizer,
)


def main():
    # Set up logging
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    print("=== Display Detection Test ===")

    # Test display detection
    detector = DisplayDetector()
    display_info = detector.get_display_info()

    print(f"Display Resolution: {display_info.width}x{display_info.height}")
    print(f"DPI: {display_info.dpi}")
    print(f"Scale Factor: {display_info.scale_factor}")

    print("\n=== Adaptive Window Sizing Test ===")

    # Test adaptive window sizing
    sizer = AdaptiveWindowSizer(detector)

    # Test default adaptive sizing
    width, height = sizer.get_adaptive_window_size()
    print(f"Adaptive Window Size: {width} x {height}")

    # Test with different base sizes
    small_width, small_height = sizer.get_adaptive_window_size(60, 8)
    print(f"Small Adaptive Size: {small_width} x {small_height}")

    large_width, large_height = sizer.get_adaptive_window_size(120, 15)
    print(f"Large Adaptive Size: {large_width} x {large_height}")

    print("\n=== Preset Sizes ===")

    # Test preset sizes
    presets = sizer.get_preset_sizes()
    for preset_name, (preset_width, preset_height) in presets.items():
        print(f"{preset_name.capitalize()}: {preset_width} x {preset_height}")

    print("\n=== Environment Variable Examples ===")
    print("You can override window sizing with these environment variables:")
    print("export PYTHON_SEARCH_WINDOW_WIDTH='100c'")
    print("export PYTHON_SEARCH_WINDOW_HEIGHT='12c'")
    print("# OR")
    print("export PYTHON_SEARCH_WINDOW_PRESET='large'")


if __name__ == "__main__":
    main()
