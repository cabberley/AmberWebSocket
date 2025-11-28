<h1 align="center">
  <br>
  <b>Amber WebSocket (Home Assistant Custom Integration)</b>
  <br>
  <h3 align="center">
    <i> Custom Home Assistant component for Connecting to and receiving price update messages from Amber Electric. </i>
    <br>
  </h3>
</h1>

<p align="center">
  <a href="https://github.com/cabberley/AmberWebSocket/releases"><img src="https://img.shields.io/github/v/release/cabberley/AmberWebSocket?display_name=tag&include_prereleases&sort=semver" alt="Current version"></a>
  <img alt="GitHub" src="https://img.shields.io/github/license/cabberley/AmberWebSocket"> <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/cabberley/AmberWebSocket/validate.yaml">
  <img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/cabberley/AmberWebSocket"> <img alt="GitHub Downloads (all assets, all releases)" src="https://img.shields.io/github/downloads/cabberley/AmberWebSocket/total">
 <img alt="GitHub User's stars" src="https://img.shields.io/github/stars/cabberley">

</p>
<p align="center">
    <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg"></a>
</p>
<p align="center">
  <a href="https://www.buymeacoffee.com/cabberley" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
</p>

# 

This custom integration connects Home Assistant to Amber Electric's live pricing WebSocket. A service which is currently in **ALPHA TESTING** provided by Amber

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cabberley&repository=AmberWebSocket&category=integration)

To install this Home Assistant Custom Integration, either Click on the open HACS Repository or by manually copying the `custom_components/amber_websocket` folder into your Home assistant `custom_components` folder.

> [!TIP]
> Don't forget to restart your Home Assistant after adding the integration to your HACS!

## Configuration

1. Navigate to *Settings → Devices & Services → Add Integration*.
2. Search for **Amber WebSocket**.
3. Enter your Amber API token and Site ID when prompted.

Each config entry opens a persistent WebSocket connection that keeps itself alive with exponential backoff reconnection.

### Config Flow Options

After the entry is created you can open *Configure* to tweak runtime options:

- **Enable debug logging** – flips the integration's logger to DEBUG for troubleshooting.
- **Collect general channel sensors** – on by default; exposes the standard consumption channel from Amber.
- **Collect feed-in channel sensors** – on by default; creates the export/feed-in sensor suite (prices are inverted so earnings show as negative costs).
- **Collect controlled load channel sensors** – off by default; builds the same sensor set for `controlledLoad` messages when Amber provides them.

Toggling any of these immediately reloads the config entry so the matching sensor sets are added or removed without restarting Home Assistant.

## Fired Event

Every message emitted by Amber triggers the `amber_websocket_event` event on the Home Assistant event bus. The event payload looks like:

```json
{
  "site_id": "01XXXXXXXXXXXXXXXXXXXX",
  "payload": { "timestamp": "...", "service": "live-prices", "action": "price-update", "data": { ... } }
}
```

You can automate against this event via the UI or YAML automations to capture the full raw response.

## Sensors

The integration creates the following sensors per config entry and updates them immediately whenever new prices arrive:

- `Amber General Price`, `Amber General Spot Price`, `Amber General Renewables`
- `Amber General Descriptor`, `Amber General Spike Status`
- `Amber General Start Time`, `Amber General End Time`, `Amber General NEM Time`
- `Amber Feed-in Price` (automatically inverted so exports show as negative costs)
- `Amber Feed-in Descriptor`, `Amber Feed-in Tariff Period`, `Amber Feed-in Tariff Season`
- `Amber Feed-in Start Time`, `Amber Feed-in End Time`, `Amber Feed-in NEM Time`
- `Amber Prices Updated` (timestamp of the most recent payload received)

These sensors are push-updated (no polling) and share a single device named `Amber WebSocket <site_id>` that links back to [amber.com.au](https://www.amber.com.au). If you only care about specific channels, open the integration's options and uncheck the ones you don't need: General (default on), Feed-in, and Controlled Load. Home Assistant reloads the entry automatically and adds/removes the matching sensor sets.

## Debugging

To collect verbose logs without YAML edits, open *Settings → Devices & Services → Amber WebSocket → Configure* and enable **Enable debug logging**. Home Assistant will immediately bump the integration's logger (`custom_components.amber_websocket`) to DEBUG so you can capture connection attempts, payload fan-out, and reconnection backoff. Disable the toggle to return to the default INFO level. You can still use the built-in `logger:` configuration if you prefer global control.
