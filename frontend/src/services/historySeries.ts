export type PharmacySeriesKey = { key: string };

function pharmacyIdFromSeriesKey(key: string) {
  return Number(key.split(':', 1)[0]);
}

export type HistoryPharmacyOption = { key: string; label: string; color: string; hasHistory: boolean };

export function formatPharmacyHistoryLabel(
  pharmacyName: string,
  point?: {
    contexto_local?: string | null;
    cep?: string | null;
    cidade?: string | null;
    uf?: string | null;
    loja_id?: string | null;
    loja_nome?: string | null;
  },
) {
  if (point?.cep) {
    const locality = [point.cidade, point.uf].filter(Boolean).join('/');
    return `Entrega ${locality || 'localidade'} · ${point.cep} · ${pharmacyName}`;
  }
  if (point?.contexto_local === 'online_sem_localizacao_confirmada') {
    return `Online · ${pharmacyName}`;
  }
  if (point?.contexto_local === 'retirada_loja_confirmada') {
    return `Retirada em unidade · ${pharmacyName}`;
  }
  return pharmacyName;
}

export function getHistoryPharmacyOptions<
  T extends PharmacySeriesKey & { label: string; color: string },
  O extends { farmacia_id: number; disponivel: boolean; preco: number | string },
>(
  offers: O[],
  series: T[],
  getOfferName: (offer: O) => string,
  colors: string[],
): HistoryPharmacyOption[] {
  const options = new Map<number, HistoryPharmacyOption>();
  for (const offer of offers) {
    if (!offer.disponivel || Number(offer.preco) <= 0) continue;
    const id = offer.farmacia_id;
    if (!options.has(id)) {
      options.set(id, {
        key: String(id),
        label: getOfferName(offer),
        color: colors[(id - 1) % colors.length],
        hasHistory: false,
      });
    }
  }
  for (const item of series) {
    const id = pharmacyIdFromSeriesKey(item.key);
    options.set(id, { key: item.key, label: item.label, color: item.color, hasHistory: true });
  }
  return [...options.values()];
}

export function getVisibleHistorySeries<T extends PharmacySeriesKey>(
  series: T[],
  selectedPharmacies: number[] | null,
): T[] {
  if (selectedPharmacies === null) return series;

  const selected = new Set(selectedPharmacies);
  return series.filter((item) => selected.has(pharmacyIdFromSeriesKey(item.key)));
}

export function toggleHistoryPharmacy<T extends PharmacySeriesKey>(
  selectedPharmacies: number[] | null,
  pharmacyId: number,
  series: T[],
): number[] | null {
  if (selectedPharmacies === null) return [pharmacyId];

  const selected = new Set(selectedPharmacies);
  if (selected.has(pharmacyId)) {
    selected.delete(pharmacyId);
  } else {
    selected.add(pharmacyId);
  }

  if (selected.size === 0 || series.every((item) => selected.has(pharmacyIdFromSeriesKey(item.key)))) {
    return null;
  }

  return [...selected];
}
