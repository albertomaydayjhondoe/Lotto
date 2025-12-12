from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Clip")


@_attrs_define
class Clip:
    """
    Attributes:
        id (UUID):
        start_ms (int | Unset):
        end_ms (int | Unset):
        duration_ms (int | Unset):
        visual_score (float | Unset):
    """

    id: UUID
    start_ms: int | Unset = UNSET
    end_ms: int | Unset = UNSET
    duration_ms: int | Unset = UNSET
    visual_score: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        start_ms = self.start_ms

        end_ms = self.end_ms

        duration_ms = self.duration_ms

        visual_score = self.visual_score

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if start_ms is not UNSET:
            field_dict["start_ms"] = start_ms
        if end_ms is not UNSET:
            field_dict["end_ms"] = end_ms
        if duration_ms is not UNSET:
            field_dict["duration_ms"] = duration_ms
        if visual_score is not UNSET:
            field_dict["visual_score"] = visual_score

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        start_ms = d.pop("start_ms", UNSET)

        end_ms = d.pop("end_ms", UNSET)

        duration_ms = d.pop("duration_ms", UNSET)

        visual_score = d.pop("visual_score", UNSET)

        clip = cls(
            id=id,
            start_ms=start_ms,
            end_ms=end_ms,
            duration_ms=duration_ms,
            visual_score=visual_score,
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
