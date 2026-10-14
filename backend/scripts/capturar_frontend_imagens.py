"""Capture app screenshots and browser image-load measurements by viewport."""

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
VIEWPORTS = [(390, 844), (768, 1024), (1440, 1000), (1920, 1080)]


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    measurements: list[dict] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        for width, height in VIEWPORTS:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
                is_mobile=width < 600,
                has_touch=width < 600,
            )
            page = context.new_page()
            console_errors: list[str] = []
            failed_requests: list[str] = []
            page.on("pageerror", lambda error: console_errors.append(str(error)))
            page.on(
                "requestfailed",
                lambda request: failed_requests.append(
                    f"{request.method} {request.url}: {request.failure}"
                ),
            )
            response = page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            guest_button = page.get_by_text("Continuar como convidado", exact=True)
            guest_button.first.wait_for(state="visible", timeout=30000)
            guest_button.first.click(timeout=10000)
            page.wait_for_url("**/home", timeout=15000)
            page.get_by_text(
                "Compare preços de medicamentos", exact=True
            ).first.wait_for(state="visible", timeout=30000)
            page.wait_for_timeout(9000)
            page.screenshot(path=str(OUTPUT / f"home-{width}.png"), full_page=True)
            home = page.evaluate(
                """() => ({
                  title: document.title,
                  url: location.href,
                  images: [...document.images].map((img) => ({
                    src: img.currentSrc || img.src,
                    complete: img.complete,
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight,
                  })),
                  documentWidth: document.documentElement.scrollWidth,
                  viewportWidth: innerWidth,
                  text: document.body.innerText.slice(0, 2000),
                })"""
            )
            detail_response = page.goto(
                f"{BASE_URL}/medicine/4190",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(6500)
            page.screenshot(path=str(OUTPUT / f"cutisanol-{width}.png"), full_page=True)
            details = page.evaluate(
                """() => ({
                  url: location.href,
                  images: [...document.images].map((img) => ({
                    src: img.currentSrc || img.src,
                    complete: img.complete,
                    naturalWidth: img.naturalWidth,
                  })),
                  text: document.body.innerText.slice(0, 1500),
                })"""
            )
            measurements.append(
                {
                    "viewport": [width, height],
                    "home_http_status": response.status if response else None,
                    "home_loaded_images": sum(
                        image["complete"] and image["naturalWidth"] > 0
                        for image in home["images"]
                    ),
                    "home_image_count": len(home["images"]),
                    "home_document_width": home["documentWidth"],
                    "home_viewport_width": home["viewportWidth"],
                    "home": home,
                    "detail_http_status": detail_response.status
                    if detail_response
                    else None,
                    "detail_loaded_images": sum(
                        image["complete"] and image["naturalWidth"] > 0
                        for image in details["images"]
                    ),
                    "detail_image_count": len(details["images"]),
                    "detail": details,
                    "page_errors": console_errors,
                    "failed_requests": failed_requests,
                }
            )
            context.close()
        browser.close()
    (OUTPUT / "browser-image-measurements.json").write_text(
        json.dumps(measurements, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            [
                {
                    "viewport": item["viewport"],
                    "home_loaded": item["home_loaded_images"],
                    "home_total": item["home_image_count"],
                    "detail_loaded": item["detail_loaded_images"],
                    "detail_total": item["detail_image_count"],
                    "home_width": item["home_document_width"],
                    "viewport_width": item["home_viewport_width"],
                    "page_errors": len(item["page_errors"]),
                    "failed_requests": len(item["failed_requests"]),
                }
                for item in measurements
            ],
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
