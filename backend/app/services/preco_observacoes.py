"""Shared policy for offer observations and price-change history."""

from datetime import datetime, timezone
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
    preco_observado = Decimal(str(preco))
    if not preco_observado.is_finite() or preco_observado <= 0:
        return None

    changed = (
        oferta.observado_em is None
        or preco_anterior is None
        or Decimal(str(preco_anterior)) != preco_observado
    )

    oferta.preco = preco_observado
    oferta.observado_em = observado_em
    if not changed:
        return None

    data_registro = (
        observado_em.astimezone(timezone.utc).replace(tzinfo=None)
        if observado_em.tzinfo is not None
        else observado_em
    )

    return HistoricoPreco(
        medicamento_id=medicamento_id,
        farmacia_id=farmacia_id,
        oferta_id=oferta.id,
        preco=preco_observado,
        data_registro=data_registro,
        origem=origem[:40],
        disponivel=oferta.disponivel,
    )
