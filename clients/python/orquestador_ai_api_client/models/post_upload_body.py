from __future__ import annotations

import datetime
from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from .. import types
from ..types import UNSET, File, FileTypes, Unset

T = TypeVar("T", bound="PostUploadBody")


@_attrs_define
class PostUploadBody:
    """
    Attributes:
        file (File | Unset):
        title (str | Unset):
        description (str | Unset):
        release_date (datetime.date | Unset):
        idempotency_key (str | Unset):
    """

    file: File | Unset = UNSET
    title: str | Unset = UNSET
    description: str | Unset = UNSET
    release_date: datetime.date | Unset = UNSET
    idempotency_key: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file: FileTypes | Unset = UNSET
        if not isinstance(self.file, Unset):
            file = self.file.to_tuple()

        title = self.title

        description = self.description

        release_date: str | Unset = UNSET
        if not isinstance(self.release_date, Unset):
            release_date = self.release_date.isoformat()

        idempotency_key = self.idempotency_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file is not UNSET:
            field_dict["file"] = file
        if title is not UNSET:
            field_dict["title"] = title
        if description is not UNSET:
            field_dict["description"] = description
        if release_date is not UNSET:
            field_dict["release_date"] = release_date
        if idempotency_key is not UNSET:
            field_dict["idempotency_key"] = idempotency_key

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        if not isinstance(self.file, Unset):
            files.append(("file", self.file.to_tuple()))

        if not isinstance(self.title, Unset):
            files.append(("title", (None, str(self.title).encode(), "text/plain")))

        if not isinstance(self.description, Unset):
            files.append(("description", (None, str(self.description).encode(), "text/plain")))

        if not isinstance(self.release_date, Unset):
            files.append(("release_date", (None, self.release_date.isoformat().encode(), "text/plain")))

        if not isinstance(self.idempotency_key, Unset):
            files.append(("idempotency_key", (None, str(self.idempotency_key).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _file = d.pop("file", UNSET)
        file: File | Unset
        if isinstance(_file, Unset):
            file = UNSET
        else:
            file = File(payload=BytesIO(_file))

        title = d.pop("title", UNSET)

        description = d.pop("description", UNSET)

        _release_date = d.pop("release_date", UNSET)
        release_date: datetime.date | Unset
        if isinstance(_release_date, Unset):
            release_date = UNSET
        else:
            release_date = isoparse(_release_date).date()

        idempotency_key = d.pop("idempotency_key", UNSET)

        post_upload_body = cls(
            file=file,
            title=title,
            description=description,
            release_date=release_date,
            idempotency_key=idempotency_key,
        )

        post_upload_body.additional_properties = d
        return post_upload_body

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
