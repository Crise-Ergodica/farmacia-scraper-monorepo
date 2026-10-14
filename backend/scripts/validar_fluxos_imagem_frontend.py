"""Exercise guest search, catalog pagination, favorites, detail and reload."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8082"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "reports"
    / "visual"
    / ("image-recovery-final-2026-10-11")
)


def image_state(page) -> dict:
    return page.evaluate(
        """() => ({
          url: location.href,
          imageCount: document.images.length,
          loadedImages: [...document.images].filter(
            (image) => image.complete && image.naturalWidth > 0
          ).length,
          images: [...document.images].map((image) => ({
            source: image.currentSrc || image.src,
            loaded: image.complete && image.naturalWidth > 0,
            naturalWidth: image.naturalWidth,
          })),
          text: document.body.innerText.slice(0, 1200),
          viewportWidth: innerWidth,
          documentWidth: document.documentElement.scrollWidth,
        })"""
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        guest = page.get_by_text("Continuar como convidado", exact=True).first
        guest.wait_for(state="visible", timeout=30000)
        guest.click()
        page.wait_for_url("**/home", timeout=15000)
        page.get_by_text("Compare preços de medicamentos", exact=True).first.wait_for(
            state="visible", timeout=30000
        )

        page.goto(f"{BASE_URL}/search?q=Glyxambi", wait_until="domcontentloaded")
        page.wait_for_timeout(7000)
        results["search"] = image_state(page)
        page.screenshot(path=str(OUTPUT / "search-glyxambi-390.png"), full_page=True)

        page.goto(f"{BASE_URL}/search", wait_until="domcontentloaded")
        page.get_by_text("resultados", exact=False).first.wait_for(
            state="visible", timeout=30000
        )
        page.wait_for_timeout(7000)
        results["pagination_page_1"] = image_state(page)
        page.get_by_text("Próxima", exact=True).click(timeout=15000)
        page.wait_for_function(
            "document.body.innerText.includes('Página 2 de')", timeout=30000
        )
        page.wait_for_timeout(5000)
        results["pagination_page_2"] = image_state(page)
        page.screenshot(path=str(OUTPUT / "search-page-2-390.png"), full_page=True)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        results["pagination_after_reload"] = image_state(page)

        page.goto(f"{BASE_URL}/favorites", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        results["favorites_guest"] = image_state(page)
        page.screenshot(path=str(OUTPUT / "favorites-guest-390.png"), full_page=True)

        page.goto(f"{BASE_URL}/medicine/2", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        results["glyxambi_detail"] = image_state(page)
        page.screenshot(path=str(OUTPUT / "glyxambi-detail-390.png"), full_page=True)
        context.close()
        browser.close()

    output = {"results": results, "page_errors": errors}
    (OUTPUT / "image-flow-measurements.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                name: {
                    "loaded_images": result["loadedImages"],
                    "image_count": result["imageCount"],
                    "page": result["url"],
                    "document_width": result["documentWidth"],
                    "viewport_width": result["viewportWidth"],
                }
                for name, result in results.items()
            },
            ensure_ascii=True,
        )
    )
    print(json.dumps({"page_errors": errors}, ensure_ascii=True))


if __name__ == "__main__":
    main()
