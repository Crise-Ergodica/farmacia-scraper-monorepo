"""Shared policy for offer observations and price-change history."""

from datetime import datetime
from decimal import Decimal

from app.models.historico import HistoricoPreco
from app.models.oferta_farmacia import OfertaFarmacia


def registrar_observacao_preco(
    oferta: OfertaFarmacia,
    *,
    preco: Decimal,
    observado_em: datetime,
    origem: str,
    farmacia_id: int,
    medicamento_id: int,
    preco_anterior: Decimal | None,
) -> HistoricoPreco | None:
    """Update the last observation; append history only for a price change.

    This is a change-event history. Unchanged prices do not create false chart
    movements; ``OfertaFarmacia.observado_em`` preserves the newest observation.
    The caller owns transaction commit/rollback.
    """
    changed = (
        oferta.observado_em is None
        or preco_anterior is None
        or Decimal(preco_anterior) != Decimal(preco)
    )

    oferta.preco = preco
    oferta.observado_em = observado_em
    if not changed:
        return None

    return HistoricoPreco(
        medicamento_id=medicamento_id,
        farmacia_id=farmacia_id,
        oferta_id=oferta.id,
        preco=preco,
        data_registro=observado_em.replace(tzinfo=None),
        origem=origem[:40],
        disponivel=oferta.disponivel,
    )
