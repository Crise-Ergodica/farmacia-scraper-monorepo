"""Validate every eligible catalog image through the API and source URL.

The source scan limits each image host to two concurrent requests and spaces
requests to the same host. Its JSON report is updated every 100 images so a
network interruption can be resumed with ``--resume``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

import httpx
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models import CatalogoBase
from app.services.imagens import catalog_image_matches_record, verify_image_url

API_ORIGIN = "http://127.0.0.1:8000"
REPORT_PATH = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / ("image-load-validation-2026-10-11.json")
)
PER_HOST_CONCURRENCY = 2
PER_HOST_START_INTERVAL = 0.2


def same_image_url(first: str | None, second: object) -> bool:
    if not first or not isinstance(second, str):
        return False
    left = urlsplit(first)
    right = urlsplit(second)
    return (
        left.scheme.lower() == right.scheme.lower()
        and (left.hostname or "").lower() == (right.hostname or "").lower()
        and left.port == right.port
        and unquote(left.path) == unquote(right.path)
        and sorted(parse_qsl(left.query, keep_blank_values=True))
        == sorted(parse_qsl(right.query, keep_blank_values=True))
    )


def eligible_catalog() -> list[dict[str, object]]:
    with SessionLocal() as session:
        products = session.scalars(select(CatalogoBase).order_by(CatalogoBase.id)).all()
        return [
            {
                "id": product.id,
                "name": product.name_search,
                "ean": product.codigo_barras,
                "sku": product.imagem_sku_origem,
                "source": product.imagem_fonte,
                "image_url": product.imagem_url,
            }
            for product in products
            if product.imagem_url and catalog_image_matches_record(product)
        ]


async def validate_api_routes(
    products: list[dict[str, object]],
) -> list[dict[str, object]]:
    semaphore = asyncio.Semaphore(16)
    results: list[dict[str, object]] = []
    async with httpx.AsyncClient(
        timeout=20, follow_redirects=False, trust_env=False
    ) as client:

        async def check(product: dict[str, object]) -> None:
            async with semaphore:
                product_id = product["id"]
                try:
                    response = await client.get(
                        f"{API_ORIGIN}/catalogo/medicamentos/{product_id}/imagem"
                    )
                    location = response.headers.get("location")
                    results.append(
                        {
                            "id": product_id,
                            "status": response.status_code,
                            "location_matches": same_image_url(
                                location, product["image_url"]
                            ),
                            "location": location,
                            "cache_control": response.headers.get("cache-control"),
                            "ok": response.status_code == 302
                            and same_image_url(location, product["image_url"]),
                        }
                    )
                except httpx.HTTPError as exc:
                    results.append(
                        {
                            "id": product_id,
                            "error": type(exc).__name__,
                            "ok": False,
                        }
                    )

        await asyncio.gather(*(check(product) for product in products))
    return results


async def validate_source_urls(urls: list[str], resume: bool) -> dict[str, dict]:
    completed: dict[str, dict] = {}
    if resume and REPORT_PATH.exists():
        previous = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        completed = {
            result["url"]: result
            for result in previous.get("source_results", [])
            if result.get("url") and result.get("ok")
        }

    semaphores: dict[str, asyncio.Semaphore] = {}
    locks: dict[str, asyncio.Lock] = {}
    next_start: dict[str, float] = {}
    results = dict(completed)
    pending = [url for url in urls if url not in results]
    finished_count = len(results)

    async def check(url: str) -> None:
        nonlocal finished_count
        host = (urlsplit(url).hostname or "").lower()
        semaphore = semaphores.setdefault(host, asyncio.Semaphore(PER_HOST_CONCURRENCY))
        lock = locks.setdefault(host, asyncio.Lock())
        async with semaphore:
            async with lock:
                now = time.monotonic()
                delay = max(0, next_start.get(host, now) - now)
                if delay:
                    await asyncio.sleep(delay)
                next_start[host] = time.monotonic() + PER_HOST_START_INTERVAL
            check_result = await verify_image_url(url, timeout_seconds=20)
            results[url] = {
                "url": url,
                "source": check_result.source,
                "http_status": check_result.status_code,
                "final_url": check_result.final_url,
                "reason": check_result.reason,
                "content_sha256": check_result.content_sha256,
                "ok": check_result.ok,
            }
            finished_count += 1
            if finished_count % 100 == 0 or finished_count == len(urls):
                print(
                    f"Validated source images: {finished_count}/{len(urls)}",
                    flush=True,
                )
                write_report(
                    products=[],
                    api_results=[],
                    source_results=list(results.values()),
                    complete=False,
                )

    await asyncio.gather(*(check(url) for url in pending))
    return results


def write_report(
    *,
    products: list[dict[str, object]],
    api_results: list[dict[str, object]],
    source_results: list[dict[str, object]],
    complete: bool,
) -> None:
    if not products and REPORT_PATH.exists():
        previous = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        products = previous.get("products", [])
        api_results = previous.get("api_results", [])
    result = {
        "product_count": len(products),
        "eligible_product_count": len(products),
        "api_route_ok": sum(item.get("ok", False) for item in api_results),
        "api_route_failed": sum(not item.get("ok", False) for item in api_results),
        "unique_source_urls": len(source_results),
        "source_http_ok": sum(item.get("ok", False) for item in source_results),
        "source_http_failed": sum(not item.get("ok", False) for item in source_results),
        "source_results": source_results,
        "api_results": api_results,
        "products": products,
        "complete": complete,
    }
    REPORT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def main(resume: bool) -> None:
    products = eligible_catalog()
    urls = sorted({str(product["image_url"]) for product in products})
    existing_source_results = []
    if resume and REPORT_PATH.exists():
        previous = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        existing_source_results = previous.get("source_results", [])
    print(
        f"Eligible products: {len(products)}; unique source URLs: {len(urls)}",
        flush=True,
    )
    api_results = await validate_api_routes(products)
    write_report(
        products=products,
        api_results=api_results,
        source_results=existing_source_results,
        complete=False,
    )
    source_results = await validate_source_urls(urls, resume)
    write_report(
        products=products,
        api_results=api_results,
        source_results=list(source_results.values()),
        complete=True,
    )
    print(
        json.dumps(
            {
                "products": len(products),
                "api_route_ok": sum(x["ok"] for x in api_results),
                "api_route_failed": sum(not x["ok"] for x in api_results),
                "unique_source_urls": len(urls),
                "source_http_ok": sum(x["ok"] for x in source_results.values()),
                "source_http_failed": sum(not x["ok"] for x in source_results.values()),
                "report": str(REPORT_PATH),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.resume))
