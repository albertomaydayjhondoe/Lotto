from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_clips_id_variants_body_options import PostClipsIdVariantsBodyOptions


T = TypeVar("T", bound="PostClipsIdVariantsBody")


@_attrs_define
class PostClipsIdVariantsBody:
    """
    Attributes:
        n_variants (int | Unset):
        options (PostClipsIdVariantsBodyOptions | Unset):
        dedup_key (str | Unset):
    """

    n_variants: int | Unset = UNSET
    options: PostClipsIdVariantsBodyOptions | Unset = UNSET
    dedup_key: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        n_variants = self.n_variants

        options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.options, Unset):
            options = self.options.to_dict()

        dedup_key = self.dedup_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if n_variants is not UNSET:
            field_dict["n_variants"] = n_variants
        if options is not UNSET:
            field_dict["options"] = options
        if dedup_key is not UNSET:
            field_dict["dedup_key"] = dedup_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_clips_id_variants_body_options import PostClipsIdVariantsBodyOptions

        d = dict(src_dict)
        n_variants = d.pop("n_variants", UNSET)

        _options = d.pop("options", UNSET)
        options: PostClipsIdVariantsBodyOptions | Unset
        if isinstance(_options, Unset):
            options = UNSET
        else:
            options = PostClipsIdVariantsBodyOptions.from_dict(_options)

        dedup_key = d.pop("dedup_key", UNSET)

        post_clips_id_variants_body = cls(
            n_variants=n_variants,
            options=options,
            dedup_key=dedup_key,
        )

        post_clips_id_variants_body.additional_properties = d
        return post_clips_id_variants_body

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
