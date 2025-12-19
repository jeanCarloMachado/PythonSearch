import os
import subprocess
import logging
from typing import Tuple, Optional, NamedTuple
from python_search.environment import is_mac, is_linux


class DisplayInfo(NamedTuple):
    """Information about the current display"""

    width: int
    height: int
    dpi: Optional[float] = None
    scale_factor: Optional[float] = None


class DisplayDetector:
    """Utility to detect display resolution and characteristics across
    different platforms"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_display_info(self) -> DisplayInfo:
        """Get display information for the current platform"""
        try:
            if is_mac():
                return self._get_macos_display_info()
            elif is_linux():
                return self._get_linux_display_info()
            else:
                self.logger.warning("Unsupported platform for display detection")
                return self._get_fallback_display_info()
        except Exception as e:
            self.logger.error(f"Failed to detect display info: {e}")
            return self._get_fallback_display_info()

    def _get_macos_display_info(self) -> DisplayInfo:
        """Get display information on macOS using multiple methods"""
        try:
            # Try multiple methods for getting display resolution
            width, height = self._get_macos_resolution()

            # Try to get DPI information
            dpi = self._get_macos_dpi()
            scale_factor = self._get_macos_scale_factor()

            return DisplayInfo(
                width=width, height=height, dpi=dpi, scale_factor=scale_factor
            )

        except Exception as e:
            self.logger.error(f"Failed to get macOS display info: {e}")
            # Fallback to common macOS resolutions
            return DisplayInfo(width=1920, height=1080, dpi=110.0, scale_factor=1.0)

    def _get_macos_resolution(self) -> tuple[int, int]:
        """Try multiple methods to get macOS screen resolution"""

        # Method 0: Check environment variables first
        env_width = os.environ.get("DISPLAY_WIDTH")
        env_height = os.environ.get("DISPLAY_HEIGHT")
        if env_width and env_height:
            try:
                return int(env_width), int(env_height)
            except ValueError:
                self.logger.debug(
                    "Invalid DISPLAY_WIDTH/DISPLAY_HEIGHT environment variables"
                )

        # Method 1: Try system_profiler first (more reliable)
        try:
            cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            import json

            data = json.loads(result.stdout)
            displays = data.get("SPDisplaysDataType", [])

            for display in displays:
                # Look for main display or first available display
                if "spdisplays_resolution" in display:
                    resolution = display["spdisplays_resolution"]
                    # Parse resolution like "2560 x 1440"
                    parts = resolution.split(" x ")
                    if len(parts) == 2:
                        width = int(parts[0])
                        height = int(parts[1])
                        return width, height

                # Alternative format in some macOS versions
                if "spdisplays_pixelresolution" in display:
                    resolution = display["spdisplays_pixelresolution"]
                    parts = resolution.split(" x ")
                    if len(parts) == 2:
                        width = int(parts[0])
                        height = int(parts[1])
                        return width, height
        except Exception as e:
            self.logger.debug(f"system_profiler method failed: {e}")

        # Method 2: Try osascript with different approach
        try:
            cmd = [
                "osascript",
                "-e",
                'tell application "System Events" to get the size of first desktop',
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            size_str = result.stdout.strip()
            # Parse output like "{1920, 1080}"
            size_str = size_str.strip("{}")
            parts = size_str.split(", ")
            if len(parts) == 2:
                width = int(parts[0])
                height = int(parts[1])
                return width, height
        except Exception as e:
            self.logger.debug(f"osascript System Events method failed: {e}")

        # Method 3: Try original osascript method
        try:
            cmd = [
                "osascript",
                "-e",
                'tell application "Finder" to get bounds of window of desktop',
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            bounds = result.stdout.strip().split(", ")

            if len(bounds) >= 4:
                width = int(bounds[2])
                height = int(bounds[3])
                return width, height
        except Exception as e:
            self.logger.debug(f"osascript Finder method failed: {e}")

        # Method 4: Try using Python libraries if available
        try:
            # Try using Quartz (part of pyobjc) if available
            from Quartz import CGDisplayBounds, CGMainDisplayID

            main_display = CGMainDisplayID()
            bounds = CGDisplayBounds(main_display)
            width = int(bounds.size.width)
            height = int(bounds.size.height)
            return width, height
        except ImportError:
            self.logger.debug("Quartz not available")
        except Exception as e:
            self.logger.debug(f"Quartz method failed: {e}")

        # Method 5: Try to detect common Mac display sizes based on model
        try:
            model_info = self._get_mac_model_info()
            if model_info:
                return self._guess_resolution_from_model(model_info)
        except Exception as e:
            self.logger.debug(f"Model-based detection failed: {e}")

        # If all methods fail, raise an exception
        raise RuntimeError("Could not determine macOS display resolution")

    def _get_mac_model_info(self) -> str:
        """Get Mac model information"""
        try:
            cmd = ["system_profiler", "SPHardwareDataType", "-json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            import json

            data = json.loads(result.stdout)
            hardware = data.get("SPHardwareDataType", [])

            if hardware and len(hardware) > 0:
                return hardware[0].get("machine_name", "")
        except Exception:
            pass

        return ""

    def _guess_resolution_from_model(self, model_info: str) -> tuple[int, int]:
        """Guess resolution based on Mac model"""
        model_lower = model_info.lower()

        # Common Mac display resolutions
        if "macbook air" in model_lower:
            if "13" in model_lower:
                return 1440, 900  # 13" MacBook Air
            elif "15" in model_lower:
                return 2880, 1864  # 15" MacBook Air
        elif "macbook pro" in model_lower:
            if "13" in model_lower:
                return 2560, 1600  # 13" MacBook Pro
            elif "14" in model_lower:
                return 3024, 1964  # 14" MacBook Pro
            elif "16" in model_lower:
                return 3456, 2234  # 16" MacBook Pro
        elif "imac" in model_lower:
            if "24" in model_lower:
                return 4480, 2520  # 24" iMac
            elif "27" in model_lower:
                return 5120, 2880  # 27" iMac
        elif "mac studio" in model_lower or "mac pro" in model_lower:
            # These typically use external displays, assume common resolution
            return 2560, 1440

        # Default to common laptop resolution
        return 1920, 1080

    def _get_macos_dpi(self) -> Optional[float]:
        """Get DPI on macOS"""
        try:
            cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse JSON output to extract DPI if available
            import json

            data = json.loads(result.stdout)

            # This is a simplified approach - actual DPI extraction from system_profiler
            # can be more complex depending on the display configuration
            displays = data.get("SPDisplaysDataType", [])
            if displays and len(displays) > 0:
                # Look for resolution and physical size to calculate DPI
                # This is a rough estimation
                return 110.0  # Default DPI for most Mac displays

        except Exception as e:
            self.logger.debug(f"Could not get macOS DPI: {e}")

        return None

    def _get_macos_scale_factor(self) -> Optional[float]:
        """Get display scale factor on macOS"""
        try:
            # This is a simplified approach - actual scale factor detection
            # would require more complex AppleScript or Cocoa APIs
            return 1.0
        except Exception:
            return None

    def _get_linux_display_info(self) -> DisplayInfo:
        """Get display information on Linux using xrandr or other tools"""
        try:
            # Try xrandr first (most common on X11)
            if self._command_exists("xrandr"):
                return self._get_xrandr_info()

            # Try wayland tools if available
            if self._command_exists("wlr-randr"):
                return self._get_wayland_info()

            # Fallback to environment variables
            return self._get_env_display_info()

        except Exception as e:
            self.logger.error(f"Failed to get Linux display info: {e}")
            return DisplayInfo(width=1920, height=1080, dpi=96.0, scale_factor=1.0)

    def _get_xrandr_info(self) -> DisplayInfo:
        """Parse xrandr output to get display information"""
        try:
            result = subprocess.run(
                ["xrandr"], capture_output=True, text=True, check=True
            )

            # Parse xrandr output to find primary display
            lines = result.stdout.split("\n")
            for line in lines:
                if " connected primary" in line or (
                    " connected" in line and "primary" not in result.stdout
                ):
                    # Extract resolution from line like:
                    # "DP-1 connected primary 1920x1080+0+0 (normal left
                    # inverted right x axis y axis) 510mm x 287mm"
                    parts = line.split()
                    for part in parts:
                        if "x" in part and "+" in part:
                            resolution = part.split("+")[0]
                            width, height = map(int, resolution.split("x"))

                            # Try to extract physical dimensions for DPI calculation
                            dpi = self._calculate_dpi_from_xrandr_line(
                                line, width, height
                            )

                            return DisplayInfo(
                                width=width, height=height, dpi=dpi, scale_factor=1.0
                            )

            # If no primary display found, use first connected display
            for line in lines:
                if " connected" in line and "disconnected" not in line:
                    parts = line.split()
                    for part in parts:
                        if "x" in part and ("+" in part or part.count("x") == 1):
                            if "+" in part:
                                resolution = part.split("+")[0]
                            else:
                                resolution = part
                            try:
                                width, height = map(int, resolution.split("x"))
                                return DisplayInfo(
                                    width=width,
                                    height=height,
                                    dpi=96.0,
                                    scale_factor=1.0,
                                )
                            except ValueError:
                                continue

        except Exception as e:
            self.logger.error(f"Failed to parse xrandr output: {e}")

        return DisplayInfo(width=1920, height=1080, dpi=96.0, scale_factor=1.0)

    def _calculate_dpi_from_xrandr_line(
        self, line: str, width: int, height: int
    ) -> Optional[float]:
        """Calculate DPI from xrandr line containing physical dimensions"""
        try:
            # Look for physical dimensions like "510mm x 287mm"
            import re

            mm_match = re.search(r"(\d+)mm x (\d+)mm", line)
            if mm_match:
                width_mm = int(mm_match.group(1))
                height_mm = int(mm_match.group(2))

                # Calculate DPI (dots per inch)
                width_inches = width_mm / 25.4
                height_inches = height_mm / 25.4

                dpi_x = width / width_inches
                dpi_y = height / height_inches

                # Return average DPI
                return (dpi_x + dpi_y) / 2
        except Exception:
            pass

        return None

    def _get_wayland_info(self) -> DisplayInfo:
        """Get display info for Wayland compositors"""
        try:
            result = subprocess.run(
                ["wlr-randr"], capture_output=True, text=True, check=True
            )

            # Parse wlr-randr output
            lines = result.stdout.split("\n")
            for i, line in enumerate(lines):
                if "current" in line:
                    # Look for resolution in current mode
                    import re

                    match = re.search(r"(\d+)x(\d+)", line)
                    if match:
                        width = int(match.group(1))
                        height = int(match.group(2))
                        return DisplayInfo(
                            width=width, height=height, dpi=96.0, scale_factor=1.0
                        )

        except Exception as e:
            self.logger.error(f"Failed to get Wayland display info: {e}")

        return DisplayInfo(width=1920, height=1080, dpi=96.0, scale_factor=1.0)

    def _get_env_display_info(self) -> DisplayInfo:
        """Try to get display info from environment variables"""
        try:
            # Some systems set these environment variables
            if "DISPLAY" in os.environ:
                # This is a very basic fallback
                return DisplayInfo(width=1920, height=1080, dpi=96.0, scale_factor=1.0)
        except Exception:
            pass

        return DisplayInfo(width=1920, height=1080, dpi=96.0, scale_factor=1.0)

    def _get_fallback_display_info(self) -> DisplayInfo:
        """Fallback display information for unsupported platforms"""
        return DisplayInfo(width=1920, height=1080, dpi=96.0, scale_factor=1.0)

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH"""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False


class AdaptiveWindowSizer:
    """Calculate appropriate window sizes based on display characteristics"""

    def __init__(self, display_detector: Optional[DisplayDetector] = None):
        self.display_detector = display_detector or DisplayDetector()
        self.logger = logging.getLogger(__name__)

    def get_adaptive_window_size(
        self,
        base_width_chars: int = 86,
        base_height_chars: int = 10,
        target_screen_percentage: float = 0.6,
    ) -> Tuple[str, str]:
        """
        Calculate adaptive window size based on display characteristics

        Args:
            base_width_chars: Base width in characters for reference resolution
            base_height_chars: Base height in characters for reference resolution
            target_screen_percentage: Target percentage of screen width to occupy

        Returns:
            Tuple of (width_str, height_str) suitable for kitty terminal
        """
        display_info = self.display_detector.get_display_info()

        # Calculate scale factor based on display resolution
        # Use 1920x1080 as reference resolution
        reference_width = 1920
        reference_height = 1080

        width_scale = display_info.width / reference_width
        height_scale = display_info.height / reference_height

        # Use geometric mean of width and height scales to avoid extreme ratios
        scale_factor = (width_scale * height_scale) ** 0.5

        # Apply DPI scaling if available
        if display_info.dpi:
            # Standard DPI is 96, adjust if significantly different
            dpi_scale = display_info.dpi / 96.0
            scale_factor *= dpi_scale

        # Apply display scale factor if available (for high-DPI displays)
        if display_info.scale_factor and display_info.scale_factor > 1.0:
            scale_factor *= display_info.scale_factor

        # Calculate new dimensions
        # Clamp scale factor to reasonable bounds
        scale_factor = max(0.5, min(3.0, scale_factor))

        new_width_chars = int(base_width_chars * scale_factor)
        new_height_chars = int(base_height_chars * scale_factor)

        # Ensure minimum usable size
        new_width_chars = max(40, new_width_chars)
        new_height_chars = max(5, new_height_chars)

        # Ensure we don't exceed screen bounds (rough estimation)
        max_width_chars = int(display_info.width / 10)  # Rough char width estimation
        max_height_chars = int(display_info.height / 20)  # Rough char height estimation

        new_width_chars = min(new_width_chars, max_width_chars)
        new_height_chars = min(new_height_chars, max_height_chars)

        self.logger.debug(
            f"Display: {display_info.width}x{display_info.height}, "
            f"DPI: {display_info.dpi}, Scale: {scale_factor:.2f}, "
            f"Window: {new_width_chars}x{new_height_chars}"
        )

        return f"{new_width_chars}c", f"{new_height_chars}c"

    def get_preset_sizes(self) -> dict:
        """Get predefined window sizes for different display categories"""
        display_info = self.display_detector.get_display_info()

        # Categorize display size
        if display_info.width <= 1366:  # Small displays (laptops, etc.)
            return {
                "small": ("60c", "8c"),
                "medium": ("80c", "10c"),
                "large": ("100c", "12c"),
            }
        elif display_info.width <= 1920:  # Standard HD displays
            return {
                "small": ("70c", "9c"),
                "medium": ("90c", "11c"),
                "large": ("120c", "15c"),
            }
        elif display_info.width <= 2560:  # QHD displays
            return {
                "small": ("80c", "10c"),
                "medium": ("110c", "13c"),
                "large": ("150c", "18c"),
            }
        else:  # 4K and larger displays
            return {
                "small": ("100c", "12c"),
                "medium": ("140c", "16c"),
                "large": ("180c", "22c"),
            }
