"""Validate loaded catalog screens in both themes without remounting AppProvider."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = "http://localhost:8083"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT = Path(__file__).resolve().parents[1] / "reports" / "visual" / "dark-theme-2026-10-24"
VIEWPORTS = {
    "390": {"width": 390, "height": 844},
    "768": {"width": 768, "height": 1024},
    "1440": {"width": 1440, "height": 900},
    "1920": {"width": 1920, "height": 1080},
}


def open_menu(page: Page) -> None:
    page.set_viewport_size(VIEWPORTS["390"])
    page.wait_for_timeout(250)
    page.get_by_label("Abrir menu").last.click()
    page.wait_for_timeout(200)


def menu_route(page: Page, label: str) -> None:
    open_menu(page)
    page.get_by_text(label, exact=True).last.click()
    page.wait_for_timeout(500)


def home(page: Page) -> None:
    menu_route(page, "Home")


def capture(page: Page, screen: str, theme: str, report: list[dict[str, object]]) -> None:
    for width_name, viewport in VIEWPORTS.items():
        page.set_viewport_size(viewport)
        page.wait_for_timeout(300)
        result = page.evaluate(
            """() => ({
              path: location.pathname,
              scheme: getComputedStyle(document.documentElement).colorScheme,
              background: getComputedStyle(document.body).backgroundColor,
              overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
              text: document.body.innerText.slice(0, 180),
            })"""
        )
        file_name = f"loaded-{screen}-{theme}-{width_name}.png"
        page.screenshot(path=OUTPUT / file_name, full_page=False)
        report.append({"file": file_name, **result})
    page.set_viewport_size(VIEWPORTS["390"])


def capture_theme(page: Page, theme: str, report: list[dict[str, object]]) -> None:
    home(page)
    capture(page, "home", theme, report)

    menu_route(page, "Buscar")
    capture(page, "search", theme, report)

    home(page)
    page.get_by_role("button", name="Abrir filtros").last.click()
    page.wait_for_timeout(400)
    capture(page, "filters", theme, report)

    home(page)
    page.get_by_test_id("medicine-card").last.click()
    page.wait_for_timeout(700)
    capture(page, "detail-comparison", theme, report)

    page.get_by_text("Ver histórico de preços", exact=True).last.click()
    try:
        page.get_by_text("Carregando histórico...").wait_for(state="hidden", timeout=100_000)
    except Exception:
        pass
    capture(page, "history", theme, report)

    menu_route(page, "Favoritos")
    capture(page, "favorites", theme, report)

    menu_route(page, "Perfil")
    capture(page, "profile", theme, report)

    page.get_by_text("Entrar", exact=True).last.click()
    page.wait_for_timeout(400)
    capture(page, "login", theme, report)
    page.go_back()
    page.wait_for_timeout(400)

    menu_route(page, "Configurações")
    capture(page, "settings", theme, report)

    home(page)
    open_menu(page)
    capture(page, "menu", theme, report)
    page.get_by_label("Fechar menu").first.click()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    captures: list[dict[str, object]] = []
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME)
        context = browser.new_context(viewport=VIEWPORTS["390"], color_scheme="light")
        context.add_init_script("localStorage.setItem('preco-bao:appearance', 'light')")
        page = context.new_page()
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(f"{BASE_URL}/home", wait_until="domcontentloaded", timeout=60_000)
        page.get_by_test_id("medicine-card").last.wait_for(timeout=120_000)

        capture_theme(page, "light", captures)
        menu_route(page, "Configurações")
        page.get_by_label("Tema Escuro").last.click()
        page.wait_for_timeout(300)
        capture_theme(page, "dark", captures)

        browser.close()

    result = {
        "captures": captures,
        "consoleErrors": sorted(set(errors)),
        "overflowFailures": [item for item in captures if item["overflowX"] != 0],
        "wrongScheme": [item for item in captures if item["scheme"] not in item["file"]],
    }
    (OUTPUT / "loaded-validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"captures={len(captures)} errors={len(result['consoleErrors'])} "
        f"overflow={len(result['overflowFailures'])} wrongScheme={len(result['wrongScheme'])}"
    )


if __name__ == "__main__":
    main()
