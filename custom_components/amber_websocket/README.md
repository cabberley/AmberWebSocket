# Amber WebSocket (Home Assistant Custom Integration)

This custom integration connects Home Assistant to Amber Electric's live pricing WebSocket. It mirrors the standalone `amber_python.py` client so that every inbound price update is available as a Home Assistant event and as a set of push-updated sensors.

## Installation

1. Copy the entire `amber_websocket` folder into `<config>/custom_components/` on your Home Assistant instance.
2. Restart Home Assistant so it discovers the new integration.

## Configuration

1. Navigate to *Settings → Devices & Services → Add Integration*.
2. Search for **Amber WebSocket**.
3. Enter your Amber API token and Site ID when prompted.

Each config entry opens a persistent WebSocket connection that keeps itself alive with exponential backoff reconnection.

## Fired Event

Every message emitted by Amber triggers the `amber_websocket_event` event on the Home Assistant event bus. The event payload looks like:

```json
{
  "site_id": "01GA20DWHV68RDSR7220XWXW22",
  "payload": { "timestamp": "...", "service": "live-prices", "action": "price-update", "data": { ... } }
}
```

You can automate against this event via the UI or YAML automations to capture the full raw response.

## Sensors

The integration creates the following sensors per config entry and updates them immediately whenever new prices arrive:

- `Amber General Price`, `Amber General Spot Price`, `Amber General Renewables`
- `Amber General Descriptor`, `Amber General Spike Status`
- `Amber General Tariff Period`, `Amber General Tariff Season`
- `Amber General Start Time`, `Amber General End Time`, `Amber General NEM Time`
- `Amber Feed-in Price` (automatically inverted so exports show as negative costs)
- `Amber Feed-in Descriptor`, `Amber Feed-in Tariff Period`, `Amber Feed-in Tariff Season`
- `Amber Feed-in Start Time`, `Amber Feed-in End Time`, `Amber Feed-in NEM Time`
- `Amber Prices Updated` (timestamp of the most recent payload received)

These sensors are push-updated (no polling) and share a single device named `Amber WebSocket <site_id>` that links back to [amber.com.au](https://www.amber.com.au). If you only care about specific channels, open the integration's options and uncheck the ones you don't need: General (default on), Feed-in, and Controlled Load. Home Assistant reloads the entry automatically and adds/removes the matching sensor sets.

## Debugging

To collect verbose logs without YAML edits, open *Settings → Devices & Services → Amber WebSocket → Configure* and enable **Enable debug logging**. Home Assistant will immediately bump the integration's logger (`custom_components.amber_websocket`) to DEBUG so you can capture connection attempts, payload fan-out, and reconnection backoff. Disable the toggle to return to the default INFO level. You can still use the built-in `logger:` configuration if you prefer global control.
