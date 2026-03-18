"""Tests for Crunchbase client."""

from src.enrichment.crunchbase import CrunchbaseClient


class TestCrunchbaseClient:
    def test_parse_employee_enum(self):
        client = CrunchbaseClient.__new__(CrunchbaseClient)
        assert client._parse_employee_enum("c_00051_00100") == 75
        assert client._parse_employee_enum("c_00251_00500") == 375
        assert client._parse_employee_enum("unknown") is None
