from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook_instagram_payload_entry_item import WebhookInstagramPayloadEntryItem


T = TypeVar("T", bound="WebhookInstagramPayload")


@_attrs_define
class WebhookInstagramPayload:
    """
    Attributes:
        object_ (str | Unset):
        entry (list[WebhookInstagramPayloadEntryItem] | Unset):
    """

    object_: str | Unset = UNSET
    entry: list[WebhookInstagramPayloadEntryItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        object_ = self.object_

        entry: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.entry, Unset):
            entry = []
            for entry_item_data in self.entry:
                entry_item = entry_item_data.to_dict()
                entry.append(entry_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if object_ is not UNSET:
            field_dict["object"] = object_
        if entry is not UNSET:
            field_dict["entry"] = entry

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_instagram_payload_entry_item import WebhookInstagramPayloadEntryItem

        d = dict(src_dict)
        object_ = d.pop("object", UNSET)

        _entry = d.pop("entry", UNSET)
        entry: list[WebhookInstagramPayloadEntryItem] | Unset = UNSET
        if _entry is not UNSET:
            entry = []
            for entry_item_data in _entry:
                entry_item = WebhookInstagramPayloadEntryItem.from_dict(entry_item_data)

                entry.append(entry_item)

        webhook_instagram_payload = cls(
            object_=object_,
            entry=entry,
        )

        webhook_instagram_payload.additional_properties = d
        return webhook_instagram_payload

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
