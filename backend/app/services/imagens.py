"""Safe product image selection and HTTP validation for pharmacy catalog data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import unquote, urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.models.catalogo import CatalogoBase

ALLOWED_IMAGE_HOSTS = {
    "farmaciaindiana.vteximg.com.br": "Indiana",
    "i3-imagens-prd.araujo.com.br": "Araujo",
    "www.araujo.com.br": "Araujo",
}
GENERIC_IMAGE_MARKERS = (
    "logo",
    "banner",
    "placeholder",
    "sem-imagem",
    "no-image",
    "tarjadogenerico",
    "tarjado-generico",
    "medicamento-tarjado",
    "caixa-medicamento",
    "caixa-azul",
    "caixa-vermelha",
    "caixa-neo-quimica",
    "caixa-da-indiana",
    "caixa-merck",
    "caixa-althaia",
    "remedioindiana",
    "image-to-upload",
    "medicamentos-caixa",
    "imagem-indisponivel",
    "medicamento-tarjado-generico",
)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
KNOWN_GENERIC_ASSETS = {"231489_7897705203095_2.webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class ImageCheck:
    ok: bool
    source: str | None = None
    status_code: int | None = None
    final_url: str | None = None
    reason: str | None = None


def source_for_url(url: str) -> str | None:
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return None
    return ALLOWED_IMAGE_HOSTS.get(host)


def embedded_eans(url: str) -> set[str]:
    path = urlsplit(url).path.rsplit("/", 1)[-1]
    return set(re.findall(r"(?<!\d)\d{13,14}(?!\d)", path))


def image_rejection_reason(url: str) -> str | None:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return "URL de imagem inválida."
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return "A imagem exige uma URL HTTPS pública."
    try:
        port = parsed.port
    except ValueError:
        return "Porta de imagem inválida."
    if port not in (None, 443):
        return "Porta de imagem não permitida."
    source = source_for_url(url)
    if source is None:
        return "Domínio de imagem não autorizado."
    filename = unquote(parsed.path.rsplit("/", 1)[-1]).lower()
    normalized_filename = re.sub(r"[^a-z0-9]+", "", filename)
    if filename == "generico.webp" or filename in KNOWN_GENERIC_ASSETS or any(
        re.sub(r"[^a-z0-9]+", "", marker) in normalized_filename
        for marker in GENERIC_IMAGE_MARKERS
    ):
        return "A fonte retornou um ícone ou imagem genérica."
    if not any(filename.endswith(extension) for extension in IMAGE_EXTENSIONS):
        return "Formato não é uma imagem de produto aceita."
    return None


def validate_image_association(
    *,
    image_url: str,
    pharmacy_name: str,
    sku: str | None,
    ean: str | None,
    product_url: str | None,
) -> tuple[bool, str | None, str | None]:
    """Check source and product identifiers before any network request."""
    reason = image_rejection_reason(image_url)
    if reason:
        return False, None, reason
    source = source_for_url(image_url)
    normalized_pharmacy = pharmacy_name.casefold()
    expected_source = (
        "Araujo"
        if "araujo" in normalized_pharmacy
        else "Indiana"
        if "indiana" in normalized_pharmacy
        else None
    )
    if expected_source is None:
        return False, source, "A origem da oferta não possui validador configurado."
    if source != expected_source:
        return False, source, "A imagem não pertence à farmácia da oferta."

    image_eans = embedded_eans(image_url)
    if image_eans and ean and ean not in image_eans:
        return False, source, "O EAN no arquivo diverge do medicamento."

    if source == "Araujo":
        offer_sku = re.fullmatch(r"ARJ(\d+)", sku or "")
        if not offer_sku or not product_url:
            return False, source, "SKU da Araújo ausente para conferir a imagem."
        product_id = re.search(r"/(\d+)\.html?$", urlsplit(product_url).path)
        image_parts = [part for part in urlsplit(image_url).path.split("/") if part]
        if (
            not product_id
            or product_id.group(1) != offer_sku.group(1)
            or offer_sku.group(1) not in image_parts[:-1]
        ):
            return False, source, "O SKU da imagem diverge da página do produto."
        return True, "ean" if image_eans else "sku", None

    if not re.fullmatch(r"IND\d+", sku or ""):
        return False, source, "SKU da Indiana ausente para conferir a imagem."
    return True, "ean" if image_eans else "sku", None


def register_image_candidate(
    catalog: CatalogoBase,
    *,
    image_url: str | None,
    pharmacy_name: str,
    sku: str | None,
    ean: str | None,
    product_url: str | None,
) -> bool:
    """Keep a scrape image as pending until the batch verifier checks HTTP data."""
    if not image_url:
        return False
    valid, source, reason = validate_image_association(
        image_url=image_url,
        pharmacy_name=pharmacy_name,
        sku=sku,
        ean=ean,
        product_url=product_url,
    )
    if not valid:
        if catalog.imagem_status != "verificada":
            catalog.imagem_motivo_rejeicao = reason
        return False
    if catalog.imagem_status == "verificada":
        return True
    catalog.imagem_url = image_url
    catalog.imagem_fonte = source
    catalog.imagem_sku_origem = sku
    catalog.imagem_ean = ean
    catalog.imagem_match = "ean" if embedded_eans(image_url) and ean else "sku"
    catalog.imagem_status = "pendente"
    catalog.imagem_motivo_rejeicao = None
    return True


def select_vtex_item_image(
    item: dict,
    *,
    expected_ean: str | None,
    expected_sku: str | None = None,
) -> str | None:
    """Select an item image while rejecting files explicitly labeled as another EAN."""
    item_ean = str(item.get("ean") or "").strip()
    item_sku = str(item.get("itemId") or "").strip()
    if expected_ean and item_ean != expected_ean:
        return None
    if expected_sku and item_sku != expected_sku:
        return None
    if not expected_ean and not expected_sku:
        return None
    images = item.get("images") or []
    candidates: list[tuple[int, str]] = []
    for image in images:
        url = str(image.get("imageUrl") or "").strip()
        if not url or image_rejection_reason(url):
            continue
        ids = embedded_eans(url)
        if ids and expected_ean not in ids:
            continue
        candidates.append((0 if expected_ean in ids else 1, url))
    if not candidates:
        return None
    candidates.sort(key=lambda value: value[0])
    return candidates[0][1]


def select_araujo_product_image(
    html: str, *, sku: str, ean: str | None, product_url: str
) -> str | None:
    """Read the product photo, not the generic thumbnail in Araújo listings."""
    soup = BeautifulSoup(html, "html.parser")
    candidates = [
        tag.get("content")
        for tag in soup.select('meta[property="og:image"], meta[name="twitter:image"]')
    ]
    for tag in soup.select('img[src], img[data-src]'):
        candidates.extend((tag.get("data-src"), tag.get("src")))
    for candidate in candidates:
        if not candidate:
            continue
        url = urljoin(product_url, unescape(str(candidate).strip()))
        valid, _, _ = validate_image_association(
            image_url=url,
            pharmacy_name="Araujo",
            sku=sku,
            ean=ean,
            product_url=product_url,
        )
        if valid:
            return url
    return None


async def verify_image_url(
    url: str,
    *,
    timeout_seconds: float = 10,
    max_bytes: int = MAX_IMAGE_BYTES,
) -> ImageCheck:
    """Fetch a bounded image prefix, validating redirects, MIME and file signature."""
    source = source_for_url(url)
    reason = image_rejection_reason(url)
    if reason:
        return ImageCheck(False, source=source, reason=reason)

    current_url = url
    headers = {
        "Accept": "image/avif,image/webp,image/png,image/jpeg;q=0.9,*/*;q=0.1",
        "Range": "bytes=0-65535",
    }
    async with httpx.AsyncClient(
        timeout=timeout_seconds, follow_redirects=False
    ) as client:
        for _ in range(4):
            if image_rejection_reason(current_url):
                return ImageCheck(
                    False,
                    source=source,
                    final_url=current_url,
                    reason="Redirecionamento para URL não autorizada.",
                )
            try:
                async with client.stream(
                    "GET", current_url, headers=headers
                ) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            return ImageCheck(
                                False,
                                source=source,
                                status_code=response.status_code,
                                reason="Redirecionamento sem destino.",
                            )
                        current_url = urljoin(current_url, location)
                        continue
                    if response.status_code not in {200, 206}:
                        return ImageCheck(
                            False,
                            source=source,
                            status_code=response.status_code,
                            final_url=current_url,
                            reason=f"A fonte respondeu HTTP {response.status_code}.",
                        )
                    content_type = (
                        response.headers.get("content-type", "")
                        .split(";", 1)[0]
                        .lower()
                    )
                    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
                        return ImageCheck(
                            False,
                            source=source,
                            status_code=response.status_code,
                            final_url=current_url,
                            reason="A resposta não tem MIME de imagem compatível.",
                        )
                    content_length = response.headers.get("content-length")
                    if content_length:
                        try:
                            too_large = int(content_length) > max_bytes
                        except ValueError:
                            return ImageCheck(
                                False,
                                source=source,
                                status_code=response.status_code,
                                final_url=current_url,
                                reason="Tamanho informado pela fonte é inválido.",
                            )
                        if too_large:
                            return ImageCheck(
                                False,
                                source=source,
                                status_code=response.status_code,
                                final_url=current_url,
                                reason="Imagem excede o limite de tamanho.",
                            )
                    prefix = bytearray()
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > max_bytes:
                            return ImageCheck(
                                False,
                                source=source,
                                status_code=response.status_code,
                                final_url=current_url,
                                reason="Imagem excede o limite de tamanho.",
                            )
                        if len(prefix) < 16:
                            prefix.extend(chunk[: 16 - len(prefix)])
                        if len(prefix) >= 16:
                            break
                    data = bytes(prefix)
                    valid_signature = (
                        data.startswith(b"\xff\xd8\xff")
                        or data.startswith(b"\x89PNG\r\n\x1a\n")
                        or (data.startswith(b"RIFF") and data[8:12] == b"WEBP")
                    )
                    if not valid_signature:
                        return ImageCheck(
                            False,
                            source=source,
                            status_code=response.status_code,
                            final_url=current_url,
                            reason=("Assinatura incompatível com uma imagem aceita."),
                        )
                    return ImageCheck(
                        True,
                        source=source,
                        status_code=response.status_code,
                        final_url=current_url,
                    )
            except httpx.HTTPError as exc:
                return ImageCheck(
                    False,
                    source=source,
                    final_url=current_url,
                    reason=f"Falha de rede: {type(exc).__name__}.",
                )
    return ImageCheck(
        False, source=source, final_url=current_url, reason="Redirecionamentos demais."
    )
