from module.device.env import IS_WINDOWS

if IS_WINDOWS:
    from module.device.platform2.platform_windows import PlatformWindows as Platform
else:
    # PlatformBase is used as Platform on non-Windows systems
    from module.device.platform2.platform_base import PlatformBase as Platform  # noqa: F401
