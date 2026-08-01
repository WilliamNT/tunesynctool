# TTL constants (in seconds)
TTL_QUEUED = 3600 # 1 hour
TTL_RUNNING = 3600 # 1 hour (refreshed by heartbeat)
TTL_FINISHED = 86400 # 24 hours

# Heartbeat settings
HEARTBEAT_INTERVAL = 30 # seconds between heartbeat updates
HEARTBEAT_STALE_THRESHOLD = 120 # seconds before considering a task stale

# SCAN batch size. Redis defaults to 10, which means one round-trip per 10 keys
# scanned. Listing tasks walks the whole keyspace, so a larger batch keeps it
# to a couple of round-trips instead of hundreds.
SCAN_COUNT = 1000