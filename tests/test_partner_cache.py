import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.partner_cache import PartnerCache, Partner  # noqa: E402


@pytest.fixture
def cache_file(tmp_path):
    return tmp_path / "partners.yaml"


class TestPartnerCache:
    def test_empty_cache_from_missing_file(self, cache_file):
        cache = PartnerCache.load(cache_file)
        assert cache.partners == []

    def test_roundtrip_save_and_load(self, cache_file):
        cache = PartnerCache(partners=[])
        cache.upsert(Partner(
            nev="Példa Kft.",
            adoszam="12345678-2-42",
            irszam="1111",
            telepules="Budapest",
            cim="Példa utca 1.",
            email="info@pelda.hu",
        ))
        cache.save(cache_file)

        loaded = PartnerCache.load(cache_file)
        assert len(loaded.partners) == 1
        assert loaded.partners[0].nev == "Példa Kft."
        assert loaded.partners[0].adoszam == "12345678-2-42"

    def test_find_by_name_substring(self, cache_file):
        cache = PartnerCache(partners=[
            Partner(nev="Example Kft.", adoszam="11111111-1-11"),
            Partner(nev="Másik Bt.", adoszam="22222222-2-22"),
        ])
        result = cache.find_by_name("example")
        assert result is not None
        assert result.nev == "Example Kft."

    def test_find_by_tax_id(self, cache_file):
        cache = PartnerCache(partners=[
            Partner(nev="A", adoszam="11111111-1-11"),
            Partner(nev="B", adoszam="22222222-2-22"),
        ])
        result = cache.find_by_tax_id("22222222-2-22")
        assert result is not None
        assert result.nev == "B"

    def test_upsert_replaces_existing_by_tax_id(self, cache_file):
        cache = PartnerCache(partners=[
            Partner(nev="Old Name", adoszam="11111111-1-11", email="old@x.hu"),
        ])
        cache.upsert(Partner(nev="New Name", adoszam="11111111-1-11", email="new@x.hu"))
        assert len(cache.partners) == 1
        assert cache.partners[0].nev == "New Name"
        assert cache.partners[0].email == "new@x.hu"

    def test_upsert_adds_new_if_tax_id_not_found(self, cache_file):
        cache = PartnerCache(partners=[
            Partner(nev="A", adoszam="11111111-1-11"),
        ])
        cache.upsert(Partner(nev="B", adoszam="22222222-2-22"))
        assert len(cache.partners) == 2
