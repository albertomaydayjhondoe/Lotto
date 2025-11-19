from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_jobs_body_params import PostJobsBodyParams


T = TypeVar("T", bound="PostJobsBody")


@_attrs_define
class PostJobsBody:
    """
    Attributes:
        job_type (str):
        clip_id (str | Unset):
        params (PostJobsBodyParams | Unset):
        dedup_key (str | Unset):
    """

    job_type: str
    clip_id: str | Unset = UNSET
    params: PostJobsBodyParams | Unset = UNSET
    dedup_key: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_type = self.job_type

        clip_id = self.clip_id

        params: dict[str, Any] | Unset = UNSET
        if not isinstance(self.params, Unset):
            params = self.params.to_dict()

        dedup_key = self.dedup_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "job_type": job_type,
            }
        )
        if clip_id is not UNSET:
            field_dict["clip_id"] = clip_id
        if params is not UNSET:
            field_dict["params"] = params
        if dedup_key is not UNSET:
            field_dict["dedup_key"] = dedup_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_jobs_body_params import PostJobsBodyParams

        d = dict(src_dict)
        job_type = d.pop("job_type")

        clip_id = d.pop("clip_id", UNSET)

        _params = d.pop("params", UNSET)
        params: PostJobsBodyParams | Unset
        if isinstance(_params, Unset):
            params = UNSET
        else:
            params = PostJobsBodyParams.from_dict(_params)

        dedup_key = d.pop("dedup_key", UNSET)

        post_jobs_body = cls(
            job_type=job_type,
            clip_id=clip_id,
            params=params,
            dedup_key=dedup_key,
        )

        post_jobs_body.additional_properties = d
        return post_jobs_body

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
