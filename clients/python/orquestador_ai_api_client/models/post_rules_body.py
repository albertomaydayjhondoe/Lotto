from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_rules_body_rules import PostRulesBodyRules


T = TypeVar("T", bound="PostRulesBody")


@_attrs_define
class PostRulesBody:
    """
    Attributes:
        name (str | Unset):
        rules (PostRulesBodyRules | Unset):
    """

    name: str | Unset = UNSET
    rules: PostRulesBodyRules | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        rules: dict[str, Any] | Unset = UNSET
        if not isinstance(self.rules, Unset):
            rules = self.rules.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if rules is not UNSET:
            field_dict["rules"] = rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_rules_body_rules import PostRulesBodyRules

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        _rules = d.pop("rules", UNSET)
        rules: PostRulesBodyRules | Unset
        if isinstance(_rules, Unset):
            rules = UNSET
        else:
            rules = PostRulesBodyRules.from_dict(_rules)

        post_rules_body = cls(
            name=name,
            rules=rules,
        )

        post_rules_body.additional_properties = d
        return post_rules_body

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
