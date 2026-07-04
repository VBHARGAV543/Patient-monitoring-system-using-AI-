from pathlib import Path
import time
from playwright.sync_api import sync_playwright

base = Path(r"c:\Users\Lenovo\Desktop\ERTS\2025\newupdatedproject\Patient-monitoring-system-using-AI--main-main0.2")
flowcharts_dir = base / "assets" / "flowcharts"
figures_dir = base / "assets" / "figures"
figures = [
    ("fig1_admission_acquisition.html", "FIG1_Patient_Admission_Data_Acquisition_ZOOMED.png"),
    ("fig2_ml_prediction.html", "FIG2_ML_Feature_Engineering_Prediction_ZOOMED.png"),
    ("fig3_alarm_policy.html", "FIG3_Alarm_Policy_Engine_ZOOMED.png"),
    ("fig4_logging_discharge.html", "FIG4_Logging_Broadcast_Discharge_ZOOMED.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for html_name, png_name in figures:
        page = browser.new_page(viewport={"width": 1800, "height": 1200}, device_scale_factor=2)
        page.goto((flowcharts_dir / html_name).as_uri())
        page.wait_for_selector("svg", timeout=15000)
        page.eval_on_selector(".diagram-wrapper", "el => el.style.maxWidth = 'none'")
        page.eval_on_selector(".mermaid", "el => { el.style.zoom = '1.45'; el.style.transformOrigin = 'top center'; }")
        page.eval_on_selector("body", "el => { el.style.padding = '20px'; }")
        time.sleep(2)
        page.locator(".diagram-wrapper").screenshot(path=str(figures_dir / png_name))
        page.close()
        print(f"Saved: {png_name}")
    browser.close()
