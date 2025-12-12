from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.campaign_create_targeting import CampaignCreateTargeting


T = TypeVar("T", bound="CampaignCreate")


@_attrs_define
class CampaignCreate:
    """
    Attributes:
        name (str):
        clip_id (UUID):
        budget_cents (int):
        targeting (CampaignCreateTargeting | Unset):
    """

    name: str
    clip_id: UUID
    budget_cents: int
    targeting: CampaignCreateTargeting | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        clip_id = str(self.clip_id)

        budget_cents = self.budget_cents

        targeting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.targeting, Unset):
            targeting = self.targeting.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "clip_id": clip_id,
                "budget_cents": budget_cents,
            }
        )
        if targeting is not UNSET:
            field_dict["targeting"] = targeting

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.campaign_create_targeting import CampaignCreateTargeting

        d = dict(src_dict)
        name = d.pop("name")

        clip_id = UUID(d.pop("clip_id"))

        budget_cents = d.pop("budget_cents")

        _targeting = d.pop("targeting", UNSET)
        targeting: CampaignCreateTargeting | Unset
        if isinstance(_targeting, Unset):
            targeting = UNSET
        else:
            targeting = CampaignCreateTargeting.from_dict(_targeting)

        campaign_create = cls(
            name=name,
            clip_id=clip_id,
            budget_cents=budget_cents,
            targeting=targeting,
        )

        campaign_create.additional_properties = d
        return campaign_create

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
