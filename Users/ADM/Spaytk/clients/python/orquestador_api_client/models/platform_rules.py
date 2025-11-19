from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.platform_rules_settings import PlatformRulesSettings


T = TypeVar("T", bound="PlatformRules")


@_attrs_define
class PlatformRules:
    """
    Attributes:
        platform (str | Unset):
        settings (PlatformRulesSettings | Unset):
    """

    platform: str | Unset = UNSET
    settings: PlatformRulesSettings | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        platform = self.platform

        settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.settings, Unset):
            settings = self.settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if platform is not UNSET:
            field_dict["platform"] = platform
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.platform_rules_settings import PlatformRulesSettings

        d = dict(src_dict)
        platform = d.pop("platform", UNSET)

        _settings = d.pop("settings", UNSET)
        settings: PlatformRulesSettings | Unset
        if isinstance(_settings, Unset):
            settings = UNSET
        else:
            settings = PlatformRulesSettings.from_dict(_settings)

        platform_rules = cls(
            platform=platform,
            settings=settings,
        )

        platform_rules.additional_properties = d
        return platform_rules

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
