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


def test_a_ref_tip_of_the_fresh_clone_needs_no_object_probe(tmp_path: Path) -> None:
    from apm_cli.cache.git_cache import _is_ref_tip

    packed, loose, other = "a" * 40, "b" * 40, "c" * 40
    git_dir = tmp_path / "staged.git"
    (git_dir / "refs" / "heads").mkdir(parents=True)
    (git_dir / "packed-refs").write_text(
        f"# pack-refs with: peeled fully-peeled sorted\n{packed} refs/heads/main\n",
        encoding="ascii",
    )
    (git_dir / "refs" / "heads" / "dev").write_text(loose + "\n", encoding="ascii")

    assert _is_ref_tip(git_dir, packed.upper())
    assert _is_ref_tip(git_dir, loose)
    assert not _is_ref_tip(git_dir, other)
    assert not _is_ref_tip(tmp_path / "missing.git", packed)
