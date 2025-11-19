from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.clip_variant import ClipVariant


T = TypeVar("T", bound="Clip")


@_attrs_define
class Clip:
    """
    Attributes:
        id (str | Unset):
        title (str | Unset):
        variants (list[ClipVariant] | Unset):
    """

    id: str | Unset = UNSET
    title: str | Unset = UNSET
    variants: list[ClipVariant] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title = self.title

        variants: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.variants, Unset):
            variants = []
            for variants_item_data in self.variants:
                variants_item = variants_item_data.to_dict()
                variants.append(variants_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if title is not UNSET:
            field_dict["title"] = title
        if variants is not UNSET:
            field_dict["variants"] = variants

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.clip_variant import ClipVariant

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        title = d.pop("title", UNSET)

        _variants = d.pop("variants", UNSET)
        variants: list[ClipVariant] | Unset = UNSET
        if _variants is not UNSET:
            variants = []
            for variants_item_data in _variants:
                variants_item = ClipVariant.from_dict(variants_item_data)

                variants.append(variants_item)

        clip = cls(
            id=id,
            title=title,
            variants=variants,
        )

        clip.additional_properties = d
        return clip

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
