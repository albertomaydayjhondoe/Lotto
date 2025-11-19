from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="VideoUploadResponse")


@_attrs_define
class VideoUploadResponse:
    """
    Attributes:
        video_asset_id (UUID):
        job_id (UUID):
        message (str | Unset):
    """

    video_asset_id: UUID
    job_id: UUID
    message: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        video_asset_id = str(self.video_asset_id)

        job_id = str(self.job_id)

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "video_asset_id": video_asset_id,
                "job_id": job_id,
            }
        )
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        video_asset_id = UUID(d.pop("video_asset_id"))

        job_id = UUID(d.pop("job_id"))

        message = d.pop("message", UNSET)

        video_upload_response = cls(
            video_asset_id=video_asset_id,
            job_id=job_id,
            message=message,
        )

        video_upload_response.additional_properties = d
        return video_upload_response

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
