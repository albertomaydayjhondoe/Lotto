from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ConfirmPublishRequest")


@_attrs_define
class ConfirmPublishRequest:
    """
    Attributes:
        clip_id (UUID):
        post_url (str):
        post_id (str):
        confirmed_by (UUID):
        platform (str | Unset):  Example: instagram.
        published_at (datetime.datetime | Unset):
        trace_id (str | Unset): Idempotency / trace id for auditing
    """

    clip_id: UUID
    post_url: str
    post_id: str
    confirmed_by: UUID
    platform: str | Unset = UNSET
    published_at: datetime.datetime | Unset = UNSET
    trace_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        clip_id = str(self.clip_id)

        post_url = self.post_url

        post_id = self.post_id

        confirmed_by = str(self.confirmed_by)

        platform = self.platform

        published_at: str | Unset = UNSET
        if not isinstance(self.published_at, Unset):
            published_at = self.published_at.isoformat()

        trace_id = self.trace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "clip_id": clip_id,
                "post_url": post_url,
                "post_id": post_id,
                "confirmed_by": confirmed_by,
            }
        )
        if platform is not UNSET:
            field_dict["platform"] = platform
        if published_at is not UNSET:
            field_dict["published_at"] = published_at
        if trace_id is not UNSET:
            field_dict["trace_id"] = trace_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        clip_id = UUID(d.pop("clip_id"))

        post_url = d.pop("post_url")

        post_id = d.pop("post_id")

        confirmed_by = UUID(d.pop("confirmed_by"))

        platform = d.pop("platform", UNSET)

        _published_at = d.pop("published_at", UNSET)
        published_at: datetime.datetime | Unset
        if isinstance(_published_at, Unset):
            published_at = UNSET
        else:
            published_at = isoparse(_published_at)

        trace_id = d.pop("trace_id", UNSET)

        confirm_publish_request = cls(
            clip_id=clip_id,
            post_url=post_url,
            post_id=post_id,
            confirmed_by=confirmed_by,
            platform=platform,
            published_at=published_at,
            trace_id=trace_id,
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
