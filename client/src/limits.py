"""
Client-side mirror of server validation limits.

These values MUST stay in sync with:
  server/src/services/auth_service.py  — username / password
  server/src/services/map_service.py   — map name
"""

# Auth
MIN_USERNAME_LEN = 3
MAX_USERNAME_LEN = 16
MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 256

# Map
MAX_MAP_NAME_LEN = 64
MAX_MAP_MEMBERS = 128
