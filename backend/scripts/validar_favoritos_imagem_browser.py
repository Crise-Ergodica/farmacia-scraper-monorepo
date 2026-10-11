"""Create and remove a local test account to verify persisted favorite images."""

from __future__ import annotations

import json
import secrets
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models import Usuario

BASE_URL = "http://localhost:8082"
API_URL = "http://127.0.0.1:8000"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "reports"
    / "visual"
    / ("image-recovery-final-2026-10-11")
)


def favorite_state(page) -> dict:
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
          text: document.body.innerText.slice(0, 1000),
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: innerWidth,
        })"""
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    email = f"image-audit-{int(time.time())}-{secrets.token_hex(3)}@preco-bao.dev"
    password = secrets.token_urlsafe(24)
    user_created = False
    results: dict[str, object] = {}
    try:
        with httpx.Client(base_url=API_URL, timeout=20) as client:
            created = client.post(
                "/auth/register",
                json={
                    "nome": "Validação temporária",
                    "email": email,
                    "password": password,
                },
            )
            created.raise_for_status()
            user_created = True
            token_response = client.post(
                "/auth/jwt/login",
                data={"username": email, "password": password},
            )
            token_response.raise_for_status()
            token = token_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            add = client.post("/users/me/favoritos/medicamentos/2", headers=headers)
            add.raise_for_status()
            before_browser = client.get(
                "/users/me/favoritos/medicamentos", headers=headers
            )
            before_browser.raise_for_status()
            favorite_ids = [item["id"] for item in before_browser.json()]
            if 2 not in favorite_ids:
                raise RuntimeError("Favorite endpoint did not persist medicine ID 2")

        page_errors: list[str] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=CHROME,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
            page.locator('input[type="email"]').fill(email)
            page.locator('input[type="password"]').fill(password)
            page.get_by_role("button", name="Entrar").click()
            page.wait_for_url("**/home", timeout=30000)
            page.goto(f"{BASE_URL}/favorites", wait_until="domcontentloaded")
            page.get_by_text("Favoritos", exact=True).first.wait_for(
                state="visible", timeout=30000
            )
            page.get_by_text("Glyxambi", exact=False).first.wait_for(
                state="visible", timeout=30000
            )
            page.wait_for_timeout(4000)
            results["saved_favorite"] = favorite_state(page)
            page.screenshot(
                path=str(OUTPUT / "favorites-authenticated-390.png"), full_page=True
            )
            page.reload(wait_until="domcontentloaded")
            page.get_by_text("Glyxambi", exact=False).first.wait_for(
                state="visible", timeout=30000
            )
            page.wait_for_timeout(3000)
            results["saved_favorite_after_reload"] = favorite_state(page)
            page.screenshot(
                path=str(OUTPUT / "favorites-authenticated-reload-390.png"),
                full_page=True,
            )
            context.close()
            browser.close()
        results["page_errors"] = page_errors
    finally:
        if user_created:
            with SessionLocal() as session:
                user = session.scalar(select(Usuario).where(Usuario.email == email))
                if user:
                    session.delete(user)
                    session.commit()
            results["temporary_user_removed"] = True

    (OUTPUT / "authenticated-favorites-image-measurements.json").write_text(
        json.dumps(results, ensure_ascii=True, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "loaded_before_reload": results["saved_favorite"]["loadedImages"],
                "images_before_reload": results["saved_favorite"]["imageCount"],
                "loaded_after_reload": results["saved_favorite_after_reload"][
                    "loadedImages"
                ],
                "images_after_reload": results["saved_favorite_after_reload"][
                    "imageCount"
                ],
                "page_errors": results["page_errors"],
                "temporary_user_removed": results["temporary_user_removed"],
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
