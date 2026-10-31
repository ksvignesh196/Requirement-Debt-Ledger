from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "app" / "static" / "js" / "simulation_view.js").read_text(encoding="utf-8")


def test_simulation_suite_has_no_redundant_run_buttons():
    assert 'id="btn-run-dep-sim"' not in HTML
    assert 'id="btn-run-what-if"' not in HTML
    assert 'id="btn-run-forecast"' not in HTML
    assert "btn-run-dep-sim" not in JS
    assert "btn-run-what-if" not in JS
    assert "btn-run-forecast" not in JS


def test_dependency_simulation_updates_on_slider_commit_and_requirement_change():
    assert 'slider.addEventListener("input"' in JS
    assert 'slider.addEventListener("change"' in JS
    assert 'debtSelect.addEventListener("change"' in JS
    assert "this.runDependencySimulation();" in JS


def test_plan_comparison_updates_when_milestone_changes():
    assert 'getElementById("whatif-milestone-select")?.addEventListener(' in JS
    assert '() => this.runWhatIfPlanning()' in JS


def test_forecast_updates_when_rate_is_selected():
    assert 'querySelectorAll(".rate-sensitivity-btn")' in JS
    assert 'this.runForecasting();' in JS
    assert 'aria-pressed="true"' in HTML


def test_auto_updates_ignore_stale_responses():
    assert "dependencyRequestId" in JS
    assert "whatIfRequestId" in JS
    assert "forecastRequestId" in JS
    assert "if (requestId !== this.dependencyRequestId) return;" in JS
    assert "if (requestId !== this.whatIfRequestId) return;" in JS
    assert "if (requestId !== this.forecastRequestId) return;" in JS


def test_reselecting_active_simulation_subview_does_not_refresh_again():
    assert "const subviewChanged = this.currentSubView !== subViewId;" in JS
    assert "if (subviewChanged) {" in JS


def test_reentering_planning_tools_refreshes_latest_data_only_on_tab_change():
    app_js = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "const previousTab = this.activeTab;" in app_js
    assert 'previousTab !== "simulator"' in app_js
    assert "SimulationView.loadReferenceData();" in app_js


def test_simulation_reference_data_is_loaded_on_demand():
    init_block = JS.split("init() {", 1)[1].split("},", 1)[0]
    assert "this.bindEvents();" in init_block
    assert "this.loadReferenceData();" not in init_block
