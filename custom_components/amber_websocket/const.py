"""Constants for the Amber WebSocket integration."""
from homeassistant.const import Platform

DOMAIN = "amber_websocket"
PLATFORMS = [Platform.SENSOR]
WS_URL = "wss://api-ws.amber.com.au"
EVENT_PRICE_UPDATE = "amber_websocket_event"
ORIGIN_HEADER = "https://app.amber.com.au"
CONF_AUTH_TOKEN = "auth_token"
CONF_SITE_ID = "site_id"
CONF_DEBUG_LOGGING = "debug_logging"
CONF_CHANNEL_GENERAL = "channel_general"
CONF_CHANNEL_FEED_IN = "channel_feed_in"
CONF_CHANNEL_CONTROLLED_LOAD = "channel_controlled_load"
MIN_RECONNECT_DELAY = 5
MAX_RECONNECT_DELAY = 60
SUBSCRIBE_SERVICE = "live-prices"
CHANNEL_GENERAL = "general"
CHANNEL_FEED_IN = "feedIn"
CHANNEL_CONTROLLED_LOAD = "controlledLoad"
DEFAULT_GENERAL_ENABLED = True
DEFAULT_FEED_IN_ENABLED = True
DEFAULT_CONTROLLED_LOAD_ENABLED = False
