import pytest

from forge.tui.app import ForgeApp


@pytest.mark.asyncio
async def test_terminal_launch_and_navigation():
    app = ForgeApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        assert app.is_running

        await pilot.press("5")
        await pilot.pause()

        assert app.current_workspace == "drift"

        await pilot.press("6")
        await pilot.pause()

        assert app.current_workspace == "preflight"

        await pilot.press("1")
        await pilot.pause()

        assert app.current_workspace == "overview"


@pytest.mark.asyncio
async def test_preflight_workspace_renders():
    app = ForgeApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("6")
        await pilot.pause()

        assert app.current_workspace == "preflight"

        await pilot.press("p")
        await pilot.pause()

        assert app.is_running


@pytest.mark.asyncio
async def test_drift_workspace_renders_without_writing_baseline(
    tmp_path, monkeypatch
):
    from forge.services import drift

    baseline = tmp_path / "test-baseline.json"
    monkeypatch.setattr(drift, "BASELINE", baseline)

    app = ForgeApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("5")
        await pilot.pause()

        assert app.current_workspace == "drift"
        assert not baseline.exists()
