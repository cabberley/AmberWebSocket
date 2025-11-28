"""Sensor platform for Amber WebSocket."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    CHANNEL_CONTROLLED_LOAD,
    CHANNEL_FEED_IN,
    CHANNEL_GENERAL,
    CONF_CHANNEL_CONTROLLED_LOAD,
    CONF_CHANNEL_FEED_IN,
    CONF_CHANNEL_GENERAL,
    CONF_SITE_ID,
    DEFAULT_CONTROLLED_LOAD_ENABLED,
    DEFAULT_FEED_IN_ENABLED,
    DEFAULT_GENERAL_ENABLED,
    DOMAIN,
)
from .coordinator import AmberCoordinator

_LOGGER = logging.getLogger(__name__)


ValueTransform = Callable[[Any], Any]
CoordinatorValueFn = Callable[[AmberCoordinator], Any]


def _to_datetime(value: Any):
    if not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = dt_util.as_utc(parsed)
    return parsed


def _invert_if_number(value: Any):
    if isinstance(value, (int, float)):
        return value * -1
    return value


def _tariff_value(channel: str, field: str) -> CoordinatorValueFn:
    def _value(coord: AmberCoordinator) -> Any:
        return coord.tariff_value(channel, field)

    return _value


def _channel_sensor_bundle(
    prefix: str,
    friendly_name: str,
    channel: str,
    *,
    invert_price: bool = False,
    price_icon: str = "mdi:flash",
) -> tuple[AmberSensorEntityDescription, ...]:
    price_transform = _invert_if_number if invert_price else None
    return (
        AmberSensorEntityDescription(
            key=f"{prefix}_per_kwh",
            name=f"Amber {friendly_name} Price",
            icon=price_icon,
            native_unit_of_measurement="c/kWh",
            state_class=SensorStateClass.MEASUREMENT,
            channel=channel,
            source_key="perKwh",
            value_transform=price_transform,
        ),
        AmberSensorEntityDescription(
            key=f"{prefix}_descriptor",
            name=f"Amber {friendly_name} Descriptor",
            icon="mdi:information-outline",
            channel=channel,
            source_key="descriptor",
        ),
        AmberSensorEntityDescription(
            key=f"{prefix}_start_time",
            name=f"Amber {friendly_name} Start Time",
            icon="mdi:clock-start",
            device_class=SensorDeviceClass.TIMESTAMP,
            channel=channel,
            source_key="startTime",
            value_transform=_to_datetime,
        ),
        AmberSensorEntityDescription(
            key=f"{prefix}_end_time",
            name=f"Amber {friendly_name} End Time",
            icon="mdi:clock-end",
            device_class=SensorDeviceClass.TIMESTAMP,
            channel=channel,
            source_key="endTime",
            value_transform=_to_datetime,
        ),
        AmberSensorEntityDescription(
            key=f"{prefix}_nem_time",
            name=f"Amber {friendly_name} NEM Time",
            icon="mdi:clock",
            device_class=SensorDeviceClass.TIMESTAMP,
            channel=channel,
            source_key="nemTime",
            value_transform=_to_datetime,
        ),
    )


@dataclass(kw_only=True)
class AmberSensorEntityDescription(SensorEntityDescription):
    """Describe an Amber sensor."""

    channel: str | None = None
    source_key: str | None = None
    value_transform: ValueTransform | None = None
    value_fn: CoordinatorValueFn | None = None


GENERAL_SENSOR_DESCRIPTIONS: tuple[AmberSensorEntityDescription, ...] = (
    AmberSensorEntityDescription(
        key="general_per_kwh",
        name="Amber General Price",
        icon="mdi:flash",
        native_unit_of_measurement="c/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        channel=CHANNEL_GENERAL,
        source_key="perKwh",
    ),
    AmberSensorEntityDescription(
        key="general_spot_per_kwh",
        name="Amber General Spot Price",
        icon="mdi:currency-usd",
        native_unit_of_measurement="c/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        channel=CHANNEL_GENERAL,
        source_key="spotPerKwh",
    ),
    AmberSensorEntityDescription(
        key="general_renewables",
        name="Amber General Renewables",
        icon="mdi:leaf",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        channel=CHANNEL_GENERAL,
        source_key="renewables",
    ),
    AmberSensorEntityDescription(
        key="general_descriptor",
        name="Amber General Descriptor",
        icon="mdi:information",
        channel=CHANNEL_GENERAL,
        source_key="descriptor",
    ),
    AmberSensorEntityDescription(
        key="general_spike_status",
        name="Amber General Spike Status",
        icon="mdi:alert",
        channel=CHANNEL_GENERAL,
        source_key="spikeStatus",
    ),
#    AmberSensorEntityDescription(
#        key="general_tariff_period",
#        name="Amber General Tariff Period",
#        icon="mdi:calendar-clock",
#        channel=CHANNEL_GENERAL,
#        value_fn=_tariff_value(CHANNEL_GENERAL, "period"),
#    ),
#    AmberSensorEntityDescription(
#        key="general_tariff_season",
#        name="Amber General Tariff Season",
#        icon="mdi:calendar",
#        channel=CHANNEL_GENERAL,
#        value_fn=_tariff_value(CHANNEL_GENERAL, "season"),
#    ),
    AmberSensorEntityDescription(
        key="general_start_time",
        name="Amber General Start Time",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        channel=CHANNEL_GENERAL,
        source_key="startTime",
        value_transform=_to_datetime,
    ),
    AmberSensorEntityDescription(
        key="general_end_time",
        name="Amber General End Time",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        channel=CHANNEL_GENERAL,
        source_key="endTime",
        value_transform=_to_datetime,
    ),
    AmberSensorEntityDescription(
        key="general_nem_time",
        name="Amber General NEM Time",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        channel=CHANNEL_GENERAL,
        source_key="nemTime",
        value_transform=_to_datetime,
    ),
)

SENSOR_DESCRIPTIONS: tuple[AmberSensorEntityDescription, ...] = (
    GENERAL_SENSOR_DESCRIPTIONS
    + _channel_sensor_bundle(
        "feed_in", "Feed-in", CHANNEL_FEED_IN, invert_price=True, price_icon="mdi:solar-power"
    )
    + _channel_sensor_bundle(
        "controlled_load",
        "Controlled Load",
        CHANNEL_CONTROLLED_LOAD,
        price_icon="mdi:transmission-tower",
    )
    + (
        AmberSensorEntityDescription(
            key="updated_at",
            name="Amber Prices Updated",
            icon="mdi:clock-check",
            device_class=SensorDeviceClass.TIMESTAMP,
            value_fn=lambda coord: coord.last_update_at(),
        ),
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Amber sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: AmberCoordinator = data["coordinator"]

    include_general = entry.options.get(CONF_CHANNEL_GENERAL, DEFAULT_GENERAL_ENABLED)
    include_feed_in = entry.options.get(CONF_CHANNEL_FEED_IN, DEFAULT_FEED_IN_ENABLED)
    include_controlled_load = entry.options.get(
        CONF_CHANNEL_CONTROLLED_LOAD, DEFAULT_CONTROLLED_LOAD_ENABLED
    )

    def _channel_allowed(description: AmberSensorEntityDescription) -> bool:
        if description.channel is None:
            return True
        if description.channel == CHANNEL_GENERAL:
            return include_general
        if description.channel == CHANNEL_FEED_IN:
            return include_feed_in
        if description.channel == CHANNEL_CONTROLLED_LOAD:
            return include_controlled_load
        return True

    filtered = [desc for desc in SENSOR_DESCRIPTIONS if _channel_allowed(desc)]

    sensors = [
        AmberPriceSensor(coordinator, entry, description)
        for description in filtered
    ]
    _LOGGER.debug(
        "Creating %s Amber sensors for site %s (general=%s feed_in=%s controlled=%s)",
        len(sensors),
        entry.data[CONF_SITE_ID],
        include_general,
        include_feed_in,
        include_controlled_load,
    )
    async_add_entities(sensors)


class AmberPriceSensor(SensorEntity):
    """Representation of a push-updated Amber sensor."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: AmberCoordinator,
        entry,
        description: AmberSensorEntityDescription,
    ) -> None:
        self.entity_description = description
        self._coordinator = coordinator
        self._entry = entry
        self._unsub = None
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_SITE_ID])},
            manufacturer="Amber Electric",
            name=f"Amber WebSocket {entry.data[CONF_SITE_ID]}",
            configuration_url="https://www.amber.com.au",
        )

    async def async_added_to_hass(self) -> None:
        self._unsub = self._coordinator.async_add_listener(self._handle_coordinator_update)
        _LOGGER.debug("Sensor %s subscribed to coordinator", self.entity_id)
        self._handle_coordinator_update()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
            _LOGGER.debug("Sensor %s unsubscribed from coordinator", self.entity_id)

    def _handle_coordinator_update(self) -> None:
        description = self.entity_description

        if description.value_fn is not None:
            value = description.value_fn(self._coordinator)
        elif description.channel and description.source_key:
            value = self._coordinator.channel_value(
                description.channel,
                description.source_key,
            )
        else:
            value = None

        if value is not None and description.value_transform is not None:
            value = description.value_transform(value)
        _LOGGER.debug(
            "Sensor %s updated value: %s",
            self.entity_id,
            value,
        )
        self._attr_native_value = value
        self.async_write_ha_state()
