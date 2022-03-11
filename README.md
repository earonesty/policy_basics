# policy_basics

A collection of rule plugins that allow basic policies to be implemented when using
the Atakama Rule Engine.

Time ranges, quotas, and other simple checks are implemented.

For more complex policies, a custom plugin can be built and loaded into the keyserver,
see https://github.com/AtakamaLLC/atakama_sdk.



# [policy_basics](#policy_basics).per_profile_throttle


## ProfileThrottleRule(RulePlugin)

Basic rule for per-profile limits:

YML Arguments:
 - per_hour: requests per hour
 - per_day: requests per day
 - persistent: restarting the server not clear current quotas

```
Example:
    - rule: per-profile-throttle-rule
      per_hour: 10
      per_day: 100
      persistent: False
```




# [policy_basics](#policy_basics).time_range


## TimeRangeRule(RulePlugin)

Basic rule for time ranges:

YML Arguments:
 - time_start: time start (hh:mm)
 - time_end: time end (hh:mm)
 - days: list of days of the week, monday=0, default is 0-6
 - include: list of specific dates to include
 - exclude: list of specific dates to exclude

```
Example:
    - rule: time-range-rule
      time_start: 9:00am
      time_end: 5:00pm
      exclude: 2022-06-01
```




