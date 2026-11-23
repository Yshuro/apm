"""Verdict keys resolve URL rewrites from one config probe per run."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.promise("P-OWN-git-ref-freshness")]


def test_url_rewrites_are_probed_once_for_many_origins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keying verdicts for many origins costs one git config probe, not one per origin."""
    from apm_cli.cache.commit_reachability import effective_contact

    probes: list[object] = []

    def _rewrites(env):
        probes.append(env)
        return (("https://mirror.example/", "https://github.com/rewritten/"),)

    monkeypatch.setattr("apm_cli.utils.git_env.git_url_rewrites", _rewrites)
    monkeypatch.setattr("apm_cli.cache.commit_reachability._REWRITES", {})
    env = {"GIT_CONFIG_GLOBAL": str(tmp_path / "gitconfig")}

    plain = [effective_contact(f"https://github.com/o/pkg-{i}", env) for i in range(5)]
    rewritten = effective_contact("https://github.com/rewritten/pkg", env)

    assert len(probes) == 1
    assert all(contact is not None and "/o/pkg-" in contact for contact in plain)
    assert rewritten is not None and rewritten.startswith("https://mirror.example")
