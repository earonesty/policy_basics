# policy\_basics

A collection of rule plugins that allow basic policies to be implemented when using
the Atakama Rule Engine.

Time ranges, quotas, and other simple checks are implemented.

For more complex policies, a custom plugin can be built and loaded into the keyserver,
see https://github.com/AtakamaLLC/atakama_sdk.



# [policy\_basics](#policy_basics).meta_str


## MetaRule(RulePlugin)

Basic rule for exact match of profile ids:

YML Arguments:
 - paths:
    - list of paths
 - regexes:
    - list of regexes
 - case_sensitive: true or false
 - require_complete: require paths to have complete, validated metadata
```
Example:
    - rule: meta-rule
      paths:
        - /startswith/hr
        - contains/subpath
        - anysubpath/
        - basename
        - basename.with_ext
```

All paths and regex's that start with an '!' are inverted (not-match)
    - paths cannot match any 'inverted'

Regex matches are python (PCRE) standard regular expressions.

Path matches use the following rules:
 - paths can contain wildcards "*", that won't pass path-component boundaries
 - paths that don't contain a "/" are assumed to be file-basename matches
 - paths that contain a "/" are assumed to be path-component matches
 - paths that don't start with "/" are assumed to be subpath matches (match anywhere)




# [policy\_basics](#policy_basics).per_profile_throttle


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




# [policy\_basics](#policy_basics).profile_id


## ProfileIdRule(RulePlugin)

Basic rule for exact match of profile ids:

YML Arguments:
 - profile_ids:
    - profile_id_in_hex
    - profile words space delimited

```
Example:
    - rule: profile-id-rule
      profile_ids:
        - d56e89af673fe1897fdcc8
        - correct horse battery staple diamond hands
```




# [policy\_basics](#policy_basics).time_range


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




