"""Setup, reload, and port-resolution tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.breezart.const import (
    CONF_PROTOCOL,
    DATA_COORDINATOR,
    DOMAIN,
    KEY_NOTIFY_POWER,
    PROTOCOL_AUTO,
    PROTOCOL_MODBUS_TCP,
    PROTOCOL_NATIVE_TCP,
    TRANSLATION_KEY_CLIMATE,
)
from custom_components.breezart.coordinator import resolve_port

from .conftest import entity_id_for


async def test_setup_and_unload(hass: HomeAssistant, setup_integration, fake_client) -> None:
    """The entry loads, creates entities, and disconnects on unload."""
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(entity_id_for(hass, "climate", TRANSLATION_KEY_CLIMATE)) is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not fake_client.is_connected


@pytest.mark.parametrize(
    ("protocol", "port", "expected"),
    [
        (PROTOCOL_MODBUS_TCP, 1560, 502),
        (PROTOCOL_NATIVE_TCP, 502, 1560),
        (PROTOCOL_MODBUS_TCP, 502, 502),
        (PROTOCOL_NATIVE_TCP, 1560, 1560),
        (PROTOCOL_MODBUS_TCP, 5020, 5020),  # custom ports are kept
        (PROTOCOL_AUTO, 1560, 1560),
    ],
)
def test_resolve_port(protocol: str, port: int, expected: int) -> None:
    """Default ports follow the protocol; custom ports are left alone."""
    assert resolve_port(protocol, port) == expected


async def test_legacy_protocol_option_uses_matching_port(
    hass: HomeAssistant, config_entry, mock_create_client
) -> None:
    """An entry switched to Modbus in options before the fix connects on 502."""
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_PROTOCOL: PROTOCOL_MODBUS_TCP}
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    kwargs = mock_create_client.call_args.kwargs
    assert kwargs["protocol"] == PROTOCOL_MODBUS_TCP
    assert kwargs["port"] == 502


async def test_port_from_options_takes_precedence(
    hass: HomeAssistant, config_entry, mock_create_client
) -> None:
    """The port verified by the options flow overrides the original one."""
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_PROTOCOL: PROTOCOL_MODBUS_TCP, CONF_PORT: 5020}
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_create_client.call_args.kwargs["port"] == 5020


async def test_notification_toggle_does_not_reload(
    hass: HomeAssistant, setup_integration
) -> None:
    """Toggling a notification switch applies live without reloading."""
    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id_for(hass, "switch", KEY_NOTIFY_POWER)}, blocking=True
        )
        await hass.async_block_till_done()

    mock_reload.assert_not_called()
    assert entry.options[KEY_NOTIFY_POWER] is False
    assert coordinator.is_notification_enabled(KEY_NOTIFY_POWER) is False
    assert hass.states.get(entity_id_for(hass, "switch", KEY_NOTIFY_POWER)).state == "off"


async def test_noop_toggle_does_not_swallow_next_reload(
    hass: HomeAssistant, setup_integration
) -> None:
    """Regression: turning on an already-on switch must not skip the next real reload."""
    entry = setup_integration
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id_for(hass, "switch", KEY_NOTIFY_POWER)}, blocking=True
    )
    await hass.async_block_till_done()

    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_PROTOCOL: PROTOCOL_MODBUS_TCP}
        )
        await hass.async_block_till_done()

    mock_reload.assert_called_once_with(entry.entry_id)


async def test_notification_toggle_from_options_applies_live(
    hass: HomeAssistant, setup_integration
) -> None:
    """Changing only a toggle via options updates the coordinator and the switch."""
    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, KEY_NOTIFY_POWER: False}
        )
        await hass.async_block_till_done()

    mock_reload.assert_not_called()
    assert coordinator.is_notification_enabled(KEY_NOTIFY_POWER) is False
    assert hass.states.get(entity_id_for(hass, "switch", KEY_NOTIFY_POWER)).state == "off"


def test_hassfest_and_hacs_metadata_and_ci_workflow() -> None:
    """Verify manifest.json key order (hassfest), hacs.json keys, and CI workflow."""
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent

    # 1. hassfest requires manifest.json keys: domain, name, then alphabetical
    manifest_raw = json.loads(
        (root / "custom_components" / "breezart" / "manifest.json").read_text(encoding="utf-8")
    )
    keys = list(manifest_raw.keys())
    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:]), (
        f"hassfest requires alphabetical keys after domain/name, got {keys[2:]}"
    )

    # 2. hacs.json must only use allowed HACS keys (no iot_class)
    allowed_hacs_keys = {
        "name",
        "content_in_root",
        "zip_release",
        "filename",
        "render_readme",
        "hide_default_branch",
        "country",
        "homeassistant",
        "hacs",
        "persistent_directory",
    }
    hacs_raw = json.loads((root / "hacs.json").read_text(encoding="utf-8"))
    extra_hacs_keys = set(hacs_raw.keys()) - allowed_hacs_keys
    assert not extra_hacs_keys, f"Invalid keys in hacs.json: {extra_hacs_keys}"

    # 3. GitHub Actions workflow must exist and include pytest, hassfest, and hacs validation
    workflow_path = root / ".github" / "workflows" / "validate.yml"
    assert workflow_path.is_file(), ".github/workflows/validate.yml must exist"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    assert "pytest" in workflow_text
    assert "hassfest" in workflow_text
    assert "hacs/action" in workflow_text

    # 4. Version consistency: manifest == newest CHANGELOG entry == docs/structure.md.
    #    No hard-coded version here, so a release only edits the release files.
    import re

    version = manifest_raw["version"]
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## \[([^\]]+)\](.*)$", changelog, flags=re.MULTILINE)
    assert headings, "CHANGELOG.md has no '## [x.y.z]' entries"
    versions = [v for v, _ in headings]
    assert versions[0] == version, (
        f"manifest.json version {version} must be the newest CHANGELOG entry, found {versions[0]}"
    )
    parsed = [tuple(int(p) for p in v.split(".")) for v in versions]
    assert parsed == sorted(parsed, reverse=True) and len(set(parsed)) == len(parsed), (
        f"CHANGELOG entries must be unique and newest first: {versions}"
    )
    assert all(not rest.strip() for _, rest in headings), "CHANGELOG headings must not carry dates"
    structure = (root / "docs" / "structure.md").read_text(encoding="utf-8")
    assert f"(v{version})" in structure, f"docs/structure.md must mention v{version}"

    # 5. Repository root must contain LICENSE file for HACS <Validation license>
    license_path = root / "LICENSE"
    assert license_path.is_file(), "LICENSE must exist in repository root for HACS validation"
    assert "MIT License" in license_path.read_text(encoding="utf-8")


def test_blueprints_valid_and_idempotent_install() -> None:
    """Verify bundled Home Assistant automation blueprints and idempotent installer."""
    import tempfile
    from pathlib import Path

    from custom_components.breezart import (
        BLUEPRINT_FILENAMES,
        install_blueprints,
        parse_blueprint_metadata,
    )

    root = Path(__file__).resolve().parent.parent
    component_bp_dir = root / "custom_components" / "breezart" / "blueprints" / "automation" / "breezart"
    repo_bp_dir = root / "blueprints" / "automation" / "breezart"

    expected_files = {
        "breezart_co2_boost.yaml",
        "breezart_night_quiet_mode.yaml",
        "breezart_away_eco_mode.yaml",
        "breezart_window_open_pause.yaml",
    }
    assert set(BLUEPRINT_FILENAMES) == expected_files

    for filename in expected_files:
        comp_file = component_bp_dir / filename
        repo_file = repo_bp_dir / filename
        assert comp_file.is_file(), f"Missing component blueprint: {comp_file}"
        assert repo_file.is_file(), f"Missing repo blueprint: {repo_file}"

        raw_comp = comp_file.read_text(encoding="utf-8")
        raw_repo = repo_file.read_text(encoding="utf-8")
        assert raw_comp == raw_repo, f"Blueprint {filename} differs between component and repo root"

        meta = parse_blueprint_metadata(raw_comp)
        assert meta["domain"] == "automation", f"Invalid domain in {filename}: {meta}"
        assert meta["name"], f"Missing blueprint name in {filename}"
        assert meta["description"], f"Missing blueprint description in {filename}"
        assert len(meta["inputs"]) >= 2, f"Expected >=2 inputs in {filename}, got {meta['inputs']}"
        assert meta["has_trigger"] is True, f"Missing trigger section in {filename}"
        assert meta["has_action"] is True, f"Missing action section in {filename}"
        assert meta["mode"] in {"single", "restart", "queued", "parallel"}

        try:
            import yaml

            class _HALoader(yaml.SafeLoader):
                pass

            _HALoader.add_constructor(
                "!input", lambda loader, node: f"!input {loader.construct_scalar(node)}"
            )
            parsed = yaml.load(raw_comp, Loader=_HALoader)
            assert isinstance(parsed, dict)
            assert parsed["blueprint"]["domain"] == "automation"
        except ImportError:
            pass

    # Verify idempotent installation into a temporary Home Assistant config directory
    with tempfile.TemporaryDirectory() as tmp:
        tmp_config = Path(tmp)
        installed_first = install_blueprints(tmp_config)
        assert len(installed_first) == 4
        target_dir = tmp_config / "blueprints" / "automation" / "breezart"
        for filename in expected_files:
            assert (target_dir / filename).is_file()
            assert (target_dir / filename).read_text(encoding="utf-8") == (
                component_bp_dir / filename
            ).read_text(encoding="utf-8")

        # Running a second time must be idempotent
        installed_second = install_blueprints(tmp_config)
        assert len(installed_second) == 4
        for filename in expected_files:
            assert (target_dir / filename).read_text(encoding="utf-8") == (
                component_bp_dir / filename
            ).read_text(encoding="utf-8")


