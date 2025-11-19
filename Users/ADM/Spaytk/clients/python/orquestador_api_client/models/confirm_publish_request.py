from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ConfirmPublishRequest")


@_attrs_define
class ConfirmPublishRequest:
    """
    Attributes:
        clip_id (str):
        platform (str):
    """

    clip_id: str
    platform: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        clip_id = self.clip_id

        platform = self.platform

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "clip_id": clip_id,
                "platform": platform,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        clip_id = d.pop("clip_id")

        platform = d.pop("platform")

        confirm_publish_request = cls(
            clip_id=clip_id,
            platform=platform,
        )

        confirm_publish_request.additional_properties = d
        return confirm_publish_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
