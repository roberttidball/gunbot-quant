"""FXMacroData client helpers for macro-aware Gunbot Quant workflows."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import quote

import requests

ENDPOINTS = (
    "data_catalogue",
    "announcements",
    "latest_announcements",
    "announcement_changes",
    "calendar",
    "predictions",
    "forex",
    "cot",
    "commodity",
    "commodities_latest",
    "curves",
    "curve_proxies",
    "forward_curves",
    "rate_differentials",
    "forward_differentials",
    "market_sessions",
    "risk_sentiment",
    "news",
    "press_releases",
    "graphql",
    "custom",
)

Transport = Callable[[str, str, dict[str, Any] | None, Any | None], Any]


class FxMacroDataError(RuntimeError):
    """Raised when an FXMacroData request cannot be built or completed."""


@dataclass
class FxMacroDataClient:
    api_key: str | None = None
    base_url: str = "https://api.fxmacrodata.com/v1"
    timeout: float = 30.0
    transport: Transport | None = None
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if self.api_key is None:
            self.api_key = os.getenv("FXMACRODATA_API_KEY") or os.getenv("FXMD_API_KEY")

    def request(
        self,
        endpoint: str,
        *,
        currency: str | None = None,
        indicator: str | None = None,
        base: str | None = None,
        quote_currency: str | None = None,
        path: str | None = None,
        params: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> Any:
        method, endpoint_path = self._endpoint_path(
            endpoint,
            currency=currency,
            indicator=indicator,
            base=base,
            quote_currency=quote_currency,
            path=path,
            body=body,
        )
        return self._send(method, endpoint_path, params=params, body=body)

    def data_catalogue(self, currency: str, **params: Any) -> Any:
        return self.request("data_catalogue", currency=currency, params=params)

    def announcements(self, currency: str, indicator: str, **params: Any) -> Any:
        return self.request("announcements", currency=currency, indicator=indicator, params=params)

    def latest_announcements(self, currency: str, **params: Any) -> Any:
        return self.request("latest_announcements", currency=currency, params=params)

    def announcement_changes(self, **params: Any) -> Any:
        return self.request("announcement_changes", params=params)

    def calendar(self, currency: str, **params: Any) -> Any:
        return self.request("calendar", currency=currency, params=params)

    def predictions(self, currency: str, indicator: str, **params: Any) -> Any:
        return self.request("predictions", currency=currency, indicator=indicator, params=params)

    def forex(self, base: str, quote_currency: str, **params: Any) -> Any:
        return self.request("forex", base=base, quote_currency=quote_currency, params=params)

    def cot(self, currency: str, **params: Any) -> Any:
        return self.request("cot", currency=currency, params=params)

    def commodity(self, indicator: str, **params: Any) -> Any:
        return self.request("commodity", indicator=indicator, params=params)

    def commodities_latest(self, **params: Any) -> Any:
        return self.request("commodities_latest", params=params)

    def curves(self, currency: str, **params: Any) -> Any:
        return self.request("curves", currency=currency, params=params)

    def curve_proxies(self, currency: str, **params: Any) -> Any:
        return self.request("curve_proxies", currency=currency, params=params)

    def forward_curves(self, currency: str, **params: Any) -> Any:
        return self.request("forward_curves", currency=currency, params=params)

    def rate_differentials(self, base: str, quote_currency: str, **params: Any) -> Any:
        return self.request(
            "rate_differentials", base=base, quote_currency=quote_currency, params=params
        )

    def forward_differentials(self, base: str, quote_currency: str, **params: Any) -> Any:
        return self.request(
            "forward_differentials", base=base, quote_currency=quote_currency, params=params
        )

    def market_sessions(self, **params: Any) -> Any:
        return self.request("market_sessions", params=params)

    def risk_sentiment(self, **params: Any) -> Any:
        return self.request("risk_sentiment", params=params)

    def news(self, currency: str, **params: Any) -> Any:
        return self.request("news", currency=currency, params=params)

    def press_releases(self, currency: str, **params: Any) -> Any:
        return self.request("press_releases", currency=currency, params=params)

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> Any:
        return self.request("graphql", body={"query": query, "variables": variables or {}})

    def macro_context(
        self,
        currency: str,
        indicator: str,
        *,
        days_ahead: int = 30,
        include_news: bool = True,
    ) -> dict[str, Any]:
        context = {
            "catalogue": self.data_catalogue(currency),
            "latest": self.latest_announcements(currency),
            "announcement": self.announcements(currency, indicator),
            "prediction": self.predictions(currency, indicator),
            "calendar": self.calendar(currency, days_ahead=days_ahead),
            "cot": self.cot(currency),
            "curve": self.curves(currency),
        }
        if include_news:
            context["news"] = self.news(currency)
        return context

    def _endpoint_path(
        self,
        endpoint: str,
        *,
        currency: str | None,
        indicator: str | None,
        base: str | None,
        quote_currency: str | None,
        path: str | None,
        body: Any | None,
    ) -> tuple[str, str]:
        if endpoint not in ENDPOINTS:
            raise FxMacroDataError(f"Unsupported FXMacroData endpoint: {endpoint}")
        if endpoint == "data_catalogue":
            return "GET", f"/data_catalogue/{slug(currency, 'currency')}"
        if endpoint == "announcements":
            return "GET", f"/announcements/{slug(currency, 'currency')}/{slug(indicator, 'indicator')}"
        if endpoint == "latest_announcements":
            return "GET", f"/announcements/{slug(currency, 'currency')}/latest"
        if endpoint == "announcement_changes":
            return "GET", "/announcements/changes"
        if endpoint == "calendar":
            return "GET", f"/calendar/{slug(currency, 'currency')}"
        if endpoint == "predictions":
            return "GET", f"/predictions/{slug(currency, 'currency')}/{slug(indicator, 'indicator')}"
        if endpoint == "forex":
            return "GET", f"/forex/{slug(base, 'base')}/{slug(quote_currency, 'quote_currency')}"
        if endpoint == "cot":
            return "GET", f"/cot/{slug(currency, 'currency')}"
        if endpoint == "commodity":
            return "GET", f"/commodities/{slug(indicator, 'indicator')}"
        if endpoint == "commodities_latest":
            return "GET", "/commodities/latest"
        if endpoint == "curves":
            return "GET", f"/curves/{slug(currency, 'currency')}"
        if endpoint == "curve_proxies":
            return "GET", f"/curve_proxies/{slug(currency, 'currency')}"
        if endpoint == "forward_curves":
            return "GET", f"/forward_curves/{slug(currency, 'currency')}"
        if endpoint == "rate_differentials":
            return "GET", f"/rate_differentials/{slug(base, 'base')}/{slug(quote_currency, 'quote_currency')}"
        if endpoint == "forward_differentials":
            return "GET", f"/forward_differentials/{slug(base, 'base')}/{slug(quote_currency, 'quote_currency')}"
        if endpoint == "market_sessions":
            return "GET", "/market_sessions"
        if endpoint == "risk_sentiment":
            return "GET", "/risk_sentiment"
        if endpoint == "news":
            return "GET", f"/news/{slug(currency, 'currency')}"
        if endpoint == "press_releases":
            return "GET", f"/press-releases/{slug(currency, 'currency')}"
        if endpoint == "graphql":
            return "POST", "/graphql"
        if not path:
            raise FxMacroDataError("path is required for custom FXMacroData requests")
        return ("POST" if body is not None else "GET"), path if path.startswith("/") else f"/{path}"

    def _send(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> Any:
        query = {k: v for k, v in (params or {}).items() if v is not None}
        if self.api_key and "api_key" not in query:
            query["api_key"] = self.api_key
        url = f"{self.base_url}{path}"
        if self.transport:
            return self.transport(method, url, query or None, body)
        response = self.session.request(method, url, params=query, json=body, timeout=self.timeout)
        response.raise_for_status()
        return response.json()


def slug(value: str | None, name: str) -> str:
    if not value:
        raise FxMacroDataError(f"{name} is required")
    return quote(value.lower(), safe="")
