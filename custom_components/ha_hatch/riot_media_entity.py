import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerDeviceClass,
)
from homeassistant.components.media_player.const import (
    SUPPORT_PLAY,
    SUPPORT_SELECT_SOUND_MODE,
    SUPPORT_STOP,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
    MEDIA_TYPE_MUSIC,
    SUPPORT_PAUSE,
    SUPPORT_VOLUME_MUTE
)
from homeassistant.const import (
    STATE_IDLE,
    STATE_PLAYING
)
from hatch_rest_api import RestIot
from .rest_entity import RestEntity

_LOGGER = logging.getLogger(__name__)


class RiotMediaEntity(RestEntity, MediaPlayerEntity):
    _attr_should_poll = False
    _attr_media_content_type = MEDIA_TYPE_MUSIC
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_media_title = None
    _attr_sound_mode = None
    _attr_is_volume_muted = False
    _attr_premute_volume_level: float | None = None

    def __init__(self, rest_device: RestIot):
        super().__init__(rest_device, "Media Player")
        self._attr_sound_mode_list = self.rest_device.favorite_names()

        if self.rest_device.audio_track:
            previous_track = self.rest_device.audio_track.name
            self._attr_sound_mode = previous_track
            self._attr_media_title = previous_track
        else:
            self._attr_sound_mode = self._attr_sound_mode_list[-1]
            self._attr_media_title = self._attr_sound_mode_list[-1]

        self._attr_supported_features = (
            SUPPORT_PLAY
            | SUPPORT_STOP
            | SUPPORT_SELECT_SOUND_MODE
            | SUPPORT_VOLUME_SET
            | SUPPORT_VOLUME_STEP
            | SUPPORT_PAUSE
            | SUPPORT_VOLUME_MUTE
        )

    def _update_local_state(self):
        if self.platform is None:
            return
        _LOGGER.debug(f"updating state:{self.rest_device}")
        if self.rest_device.is_playing:
            self._attr_state = STATE_PLAYING
        else:
            self._attr_state = STATE_IDLE

        self._attr_sound_mode = self.rest_device.audio_track
        self._attr_media_title = self.rest_device.audio_track
        self._attr_volume_level = self.rest_device.volume / 100

        if self._attr_state == STATE_PLAYING and self._attr_volume_level == .01:
            self._attr_is_volume_muted = True
        else:
            self._attr_is_volume_muted = False

        self._attr_device_info.update(sw_version=self.rest_device.firmware_version)
        self.async_write_ha_state()

    def set_volume_level(self, volume):
        self.rest_device.set_volume(int(volume * 100))

    def media_play(self):
        if self._attr_media_title:
            self.rest_device.set_favorite(self._attr_media_title)
        else:
            self._attr_sound_mode = self._attr_sound_mode_list[0]
            self._attr_media_title = self._attr_sound_mode_list[0]
            self.rest_device.set_favorite(self._attr_sound_mode_list[0])

    def select_sound_mode(self, sound_mode: str):
        self._attr_sound_mode = sound_mode
        self._attr_media_title = sound_mode
        self.rest_device.set_favorite(sound_mode)

    def media_stop(self):
        self.rest_device.turn_off()

    def media_pause(self):
        self.rest_device.turn_off()

    def mute_volume(self, mute: bool):
        if mute:
            self._attr_premute_volume_level = self._attr_volume_level
            self.set_volume_level(.01)
        else:
            self.set_volume_level(self._attr_premute_volume_level)
