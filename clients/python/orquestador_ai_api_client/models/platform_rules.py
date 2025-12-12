from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.platform_rules_rules import PlatformRulesRules


T = TypeVar("T", bound="PlatformRules")


@_attrs_define
class PlatformRules:
    """
    Attributes:
        id (str | Unset):
        rules (PlatformRulesRules | Unset):
    """

    id: str | Unset = UNSET
    rules: PlatformRulesRules | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        rules: dict[str, Any] | Unset = UNSET
        if not isinstance(self.rules, Unset):
            rules = self.rules.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if rules is not UNSET:
            field_dict["rules"] = rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.platform_rules_rules import PlatformRulesRules

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _rules = d.pop("rules", UNSET)
        rules: PlatformRulesRules | Unset
        if isinstance(_rules, Unset):
            rules = UNSET
        else:
            rules = PlatformRulesRules.from_dict(_rules)

        platform_rules = cls(
            id=id,
            rules=rules,
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
