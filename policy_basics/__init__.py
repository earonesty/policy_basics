"""
A collection of rule plugins that allow basic policies to be implemented when using
the Atakama Rule Engine.

Time ranges, quotas, and other simple check are implemented.

For more complex policies, a custom plugin can be built and loaded into the keyserver,
see https://github.com/AtakamaLLC/atakama_sdk.
"""
from .time_range import TimeRangeRule
