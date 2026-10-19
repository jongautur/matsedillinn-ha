"""Constants for Matseðillinn."""

from datetime import timedelta

DOMAIN = "matsedillinn"

CONF_LANGUAGE = "language"

DEFAULT_URL = "https://matsedillinn.net"
LANGUAGES = ["is", "en", "pl"]

SCAN_INTERVAL = timedelta(minutes=15)

# The server only serves weeks in this range relative to the current one.
MIN_WEEK_OFFSET = -4
MAX_WEEK_OFFSET = 8

# Matches the server's own wording for an empty day.
NOTHING_PLANNED = {"is": "Ekkert skipulagt", "en": "Nothing planned", "pl": "Nic nie zaplanowano"}
