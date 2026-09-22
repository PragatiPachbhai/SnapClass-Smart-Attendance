from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

import httpx
import streamlit as st


@dataclass
class _Query:
    table_name: str
    operation: str = "select"
    columns: str = "*"
    filters: list[tuple[str, str, Any]] = field(default_factory=list)
    payload: Any = None

    def select(self, columns: str = "*") -> "_Query":
        self.operation = "select"
        self.columns = columns
        return self

    def eq(self, column: str, value: Any) -> "_Query":
        self.filters.append((column, "eq", value))
        return self

    def insert(self, payload: Any) -> "_Query":
        self.operation = "insert"
        self.payload = payload
        return self

    def delete(self) -> "_Query":
        self.operation = "delete"
        return self

    def execute(self) -> Any:
        url = f"{_client.base_url}/{quote(self.table_name, safe='')}"
        params: list[tuple[str, str]] = []
        if self.operation == "select":
            params.append(("select", self.columns))
        for column, operator, value in self.filters:
            params.append((column, f"{operator}.{value}"))

        headers = _client.headers.copy()
        if self.operation == "insert":
            headers["Prefer"] = "return=representation"
            response = httpx.post(url, headers=headers, json=self.payload, timeout=30)
        elif self.operation == "delete":
            response = httpx.delete(url, headers=headers, params=params, timeout=30)
        else:
            response = httpx.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return type("Response", (), {"data": response.json()})()


class _RestClient:
    def __init__(self, project_url: str, api_key: str):
        self.base_url = project_url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def table(self, table_name: str) -> _Query:
        return _Query(table_name)


_client = _RestClient(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = _client