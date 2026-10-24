"""API DTO construction with external image references."""

from app.models.catalogo import CatalogoBase
from app.schemas.catalogo import CatalogoComOfertasOut
from app.services.image_registry import resolve_catalog_images


def with_registry_images(medicine: CatalogoBase) -> CatalogoComOfertasOut:
    urls = resolve_catalog_images(medicine.id, getattr(medicine, "ofertas", []))
    result = CatalogoComOfertasOut.model_validate(medicine)
    offers = [offer.model_copy(update={"imagem_url": None}) for offer in result.ofertas]
    return result.model_copy(
        update={
            "imagem_urls": urls,
            "imagem_url": urls[0] if urls else None,
            "imagem_fonte": None,
            "imagem_status": None,
            "imagem_motivo_rejeicao": None,
            "ofertas": offers,
        }
    )
