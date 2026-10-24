"""Capture the light/dark visual matrix and verify browser theme behavior."""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = "http://localhost:8083"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT = Path(__file__).resolve().parents[1] / "reports" / "visual" / "dark-theme-2026-10-24"
VIEWPORTS = {
    "390": {"width": 390, "height": 844},
    "768": {"width": 768, "height": 1024},
    "1440": {"width": 1440, "height": 900},
    "1920": {"width": 1920, "height": 1080},
}
ROUTES = {
    "home": "/home",
    "search": "/search",
    "filters": "/filters",
    "detail-and-comparison": "/medicine/1",
    "history": "/history/1",
    "favorites": "/favorites",
    "profile": "/profile",
    "login": "/login",
    "settings": "/settings",
}


def set_preference(page, preference: str) -> None:
    page.evaluate(
        "preference => localStorage.setItem('preco-bao:appearance', preference)",
        preference,
    )


def wait_for_app(page) -> None:
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(900)


def measurements(page) -> dict[str, object]:
    return page.evaluate(
        """() => ({
          url: location.pathname,
          preference: localStorage.getItem('preco-bao:appearance'),
          colorScheme: getComputedStyle(document.documentElement).colorScheme,
          background: getComputedStyle(document.body).backgroundColor,
          overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          title: document.querySelector('h1')?.textContent || document.querySelector('[role=heading]')?.textContent || null,
        })"""
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {"captures": [], "behavior": {}, "consoleErrors": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME)

        if os.environ.get("THEME_BEHAVIOR_ONLY") != "1":
            for theme in ("light", "dark"):
                for width_name, viewport in VIEWPORTS.items():
                    context = browser.new_context(viewport=viewport, color_scheme="light")
                    page = context.new_page()
                    page.on(
                        "console",
                        lambda message: report["consoleErrors"].append(message.text)
                        if message.type == "error"
                        else None,
                    )
                    page.goto(f"{BASE_URL}/settings", wait_until="domcontentloaded", timeout=60_000)
                    set_preference(page, theme)
                    page.reload(wait_until="domcontentloaded", timeout=60_000)
                    wait_for_app(page)

                    routes = ROUTES if width_name in {"390", "1440"} else {
                        "home": ROUTES["home"],
                        "settings": ROUTES["settings"],
                        "history": ROUTES["history"],
                    }
                    for name, route in routes.items():
                        page.goto(f"{BASE_URL}{route}", wait_until="domcontentloaded", timeout=60_000)
                        wait_for_app(page)
                        result = measurements(page)
                        file_name = f"{name}-{theme}-{width_name}.png"
                        page.screenshot(path=OUTPUT / file_name, full_page=False)
                        report["captures"].append({"file": file_name, **result})

                    page.goto(f"{BASE_URL}/home", wait_until="domcontentloaded", timeout=60_000)
                    wait_for_app(page)
                    menu_label = "Abrir menu" if viewport["width"] < 900 else "Mais opções"
                    button = page.get_by_label(menu_label)
                    if button.count():
                        button.first.click()
                        page.wait_for_timeout(250)
                        file_name = f"menu-{theme}-{width_name}.png"
                        page.screenshot(path=OUTPUT / file_name, full_page=False)
                        report["captures"].append({"file": file_name, **measurements(page)})
                    context.close()

        context = browser.new_context(viewport=VIEWPORTS["390"], color_scheme="light")
        page = context.new_page()
        page.goto(f"{BASE_URL}/settings", wait_until="domcontentloaded", timeout=60_000)
        wait_for_app(page)
        page.get_by_label("Tema Escuro").click()
        selected_dark = measurements(page)
        page.reload(wait_until="domcontentloaded", timeout=60_000)
        wait_for_app(page)
        restored_dark = measurements(page)
        page.get_by_label("Tema Sistema").click()
        system_light = measurements(page)
        page.emulate_media(color_scheme="dark")
        page.wait_for_timeout(200)
        system_dark = measurements(page)
        page.get_by_label("Tema Claro").click()
        page.emulate_media(color_scheme="dark")
        page.wait_for_timeout(200)
        manual_light = measurements(page)
        report["behavior"] = {
            "selectedDark": selected_dark,
            "restoredDark": restored_dark,
            "systemLight": system_light,
            "systemDarkAfterLiveChange": system_dark,
            "manualLightWithDarkSystem": manual_light,
        }
        context.close()
        browser.close()

    report["consoleErrors"] = sorted(set(report["consoleErrors"]))
    (OUTPUT / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report["behavior"], ensure_ascii=False, indent=2))
    print(f"captures={len(report['captures'])} consoleErrors={len(report['consoleErrors'])}")


if __name__ == "__main__":
    main()
