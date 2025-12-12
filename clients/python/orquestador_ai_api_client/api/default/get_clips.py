from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.clip import Clip
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    status: str | Unset = UNSET,
    min_visual_score: float | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["status"] = status

    params["min_visual_score"] = min_visual_score

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/clips",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> list[Clip] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = Clip.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[list[Clip]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: str | Unset = UNSET,
    min_visual_score: float | Unset = UNSET,
) -> Response[list[Clip]]:
    """List clips with filters

    Args:
        status (str | Unset):
        min_visual_score (float | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Clip]]
    """

    kwargs = _get_kwargs(
        status=status,
        min_visual_score=min_visual_score,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    status: str | Unset = UNSET,
    min_visual_score: float | Unset = UNSET,
) -> list[Clip] | None:
    """List clips with filters

    Args:
        status (str | Unset):
        min_visual_score (float | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Clip]
    """

    return sync_detailed(
        client=client,
        status=status,
        min_visual_score=min_visual_score,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: str | Unset = UNSET,
    min_visual_score: float | Unset = UNSET,
) -> Response[list[Clip]]:
    """List clips with filters

    Args:
        status (str | Unset):
        min_visual_score (float | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Clip]]
    """

    kwargs = _get_kwargs(
        status=status,
        min_visual_score=min_visual_score,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    status: str | Unset = UNSET,
    min_visual_score: float | Unset = UNSET,
) -> list[Clip] | None:
    """List clips with filters

    Args:
        status (str | Unset):
        min_visual_score (float | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Clip]
    """

    return (
        await asyncio_detailed(
            client=client,
            status=status,
            min_visual_score=min_visual_score,
        )
    ).parsed
