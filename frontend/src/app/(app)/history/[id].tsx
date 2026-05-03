import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import {
  Platform,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';

import {
  HistoryChart,
  HistoryChartSeries,
} from '../../../components/HistoryChart';
import { OfferRow } from '../../../components/OfferRow';
import { Screen } from '../../../components/Screen';
import { SearchBar } from '../../../components/SearchBar';
import { useAppContext } from '../../../context/AppContext';
import {
  HistoricoPrecoSerie,
  Medicamento,
  Oferta,
} from '../../../types/api';
import { palette, radius, spacing } from '../../../theme';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const PHARMACY_COLORS = [
  '#1688F6',
  '#34A853',
  '#F2994A',
  '#9B51E0',
  '#EB5757',
  '#2D9CDB',
  '#27AE60',
  '#BB6BD9',
];

type HistoricoResponseItem =
  | HistoricoPrecoSerie
  | {
      farmacia_id: number;
      farmacia_nome?: string;
      data_registro: string;
      preco_registrado?: number;
      preco?: number;
    };

function formatPrice(value?: number) {
  if (value === undefined || !Number.isFinite(value)) {
    return 'Sem preço';
  }

  return `R$ ${value.toFixed(2).replace('.', ',')}`;
}

function formatDateLabel(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return 'Atual';
  }

  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
  });
}

function getPharmacyName(offer?: Oferta) {
  if (!offer) {
    return 'Farmácia';
  }

  return (
    offer.farmacia_nome ||
    offer.farmacia?.nome_fantasia ||
    offer.farmacia?.razao_social ||
    `Farmácia ${offer.farmacia_id}`
  );
}

function getColorByIndex(index: number) {
  return PHARMACY_COLORS[index % PHARMACY_COLORS.length];
}

function buildFallbackSeries(medicine: Medicamento): HistoryChartSeries[] {
  const offers = [...(medicine.ofertas || [])].sort(
    (a, b) => Number(a.preco) - Number(b.preco)
  );

  return offers.map((offer, index) => ({
    key: String(offer.id),
    label: getPharmacyName(offer),
    color: getColorByIndex(index),
    history: [
      {
        label: 'Atual',
        value: Number(offer.preco),
      },
    ],
  }));
}

function normalizeHistoryPayload(payload: HistoricoResponseItem[]): HistoryChartSeries[] {
  if (!Array.isArray(payload) || payload.length === 0) {
    return [];
  }

  // formato 1: [{ farmacia_id, farmacia_nome, historico: [...] }]
  if ('historico' in payload[0]) {
    return (payload as HistoricoPrecoSerie[]).map((item, index) => ({
      key: String(item.farmacia_id),
      label: item.farmacia_nome || `Farmácia ${item.farmacia_id}`,
      color: getColorByIndex(index),
      history: [...item.historico]
        .sort(
          (a, b) =>
            new Date(a.data_registro).getTime() - new Date(b.data_registro).getTime()
        )
        .map((point) => ({
          label: formatDateLabel(point.data_registro),
          value: Number(point.preco),
        })),
    }));
  }

  // formato 2: flat list
  const grouped = new Map<
    number,
    {
      pharmacyName: string;
      points: { data_registro: string; preco: number }[];
    }
  >();

  (payload as HistoricoResponseItem[]).forEach((item) => {
    if (!('farmacia_id' in item)) return;

    const price = Number(item.preco_registrado ?? item.preco ?? 0);
    const pharmacyId = item.farmacia_id;
    const pharmacyName = item.farmacia_nome || `Farmácia ${pharmacyId}`;

    if (!grouped.has(pharmacyId)) {
      grouped.set(pharmacyId, {
        pharmacyName,
        points: [],
      });
    }

    grouped.get(pharmacyId)?.points.push({
      data_registro: item.data_registro,
      preco: price,
    });
  });

  return Array.from(grouped.entries()).map(([pharmacyId, value], index) => ({
    key: String(pharmacyId),
    label: value.pharmacyName,
    color: getColorByIndex(index),
    history: value.points
      .sort(
        (a, b) =>
          new Date(a.data_registro).getTime() - new Date(b.data_registro).getTime()
      )
      .map((point) => ({
        label: formatDateLabel(point.data_registro),
        value: Number(point.preco),
      })),
  }));
}

export default function HistoryScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const { getMedicineById, isLoading } = useAppContext();
  const [search, setSearch] = useState('Preço Bão');
  const [series, setSeries] = useState<HistoryChartSeries[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [historyMessage, setHistoryMessage] = useState('');
  const { width } = useWindowDimensions();

  const medicineId = useMemo(() => {
    const rawId = Array.isArray(params.id) ? params.id[0] : params.id;
    const parsedId = Number(rawId);

    return Number.isFinite(parsedId) ? parsedId : null;
  }, [params.id]);

  const medicine = useMemo(() => {
    if (medicineId === null) return undefined;
    return getMedicineById(medicineId);
  }, [getMedicineById, medicineId]);

  const currentOffers = useMemo(() => {
    if (!medicine?.ofertas?.length) return [];
    return [...medicine.ofertas].sort((a, b) => Number(a.preco) - Number(b.preco));
  }, [medicine]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!medicine || medicineId === null) {
        setSeries([]);
        setIsLoadingHistory(false);
        return;
      }

      setIsLoadingHistory(true);
      setHistoryMessage('');

      try {
        const response = await fetch(`${API_URL}/catalogo/${medicineId}/historico`);

        if (!response.ok) {
          throw new Error('Endpoint de histórico ainda não disponível');
        }

        const data = await response.json();
        const normalized = normalizeHistoryPayload(data);

        if (!normalized.length) {
          throw new Error('Sem histórico retornado');
        }

        setSeries(normalized);
      } catch (error) {
        setSeries(buildFallbackSeries(medicine));
        setHistoryMessage(
          'Ainda não há endpoint de histórico real disponível. Exibindo o preço atual por farmácia.'
        );
      } finally {
        setIsLoadingHistory(false);
      }
    };

    fetchHistory();
  }, [medicine, medicineId]);

  const isDesktop = Platform.OS === 'web' && width >= 1100;
  const isTablet = Platform.OS === 'web' && width >= 800 && width < 1100;

  const summaryCardWidth = isDesktop ? '31%' : isTablet ? '48%' : '100%';

  if (isLoading) {
    return (
      <Screen>
        <Text style={styles.feedbackText}>Carregando catálogo...</Text>
      </Screen>
    );
  }

  if (!medicine) {
    return (
      <Screen>
        <SearchBar
          value={search}
          onChangeText={setSearch}
          onSubmit={() => router.push({ pathname: '/search', params: { q: search } })}
          onBack={() => router.back()}
        />

        <View style={styles.notFoundBox}>
          <Text style={styles.notFoundTitle}>Histórico não encontrado</Text>
          <Text style={styles.notFoundText}>
            Não foi possível localizar esse medicamento no catálogo carregado.
          </Text>
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onSubmit={() => router.push({ pathname: '/search', params: { q: search } })}
        onBack={() => router.back()}
      />

      <View style={styles.headerBox}>
        <Text style={styles.title}>{medicine.nome}</Text>
        <Text style={styles.subtitle}>
          Histórico de preços por farmácia
        </Text>
      </View>

      {!!currentOffers.length && (
        <View style={styles.summaryGrid}>
          {currentOffers.map((offer, index) => (
            <View
              key={offer.id}
              style={[styles.summaryCard, { width: summaryCardWidth }]}
            >
              <View style={styles.summaryTopRow}>
                <View
                  style={[
                    styles.summaryDot,
                    { backgroundColor: getColorByIndex(index) },
                  ]}
                />
                <Text style={styles.summaryPharmacy}>{getPharmacyName(offer)}</Text>
              </View>

              <Text style={styles.summaryPrice}>{formatPrice(Number(offer.preco))}</Text>
              <Text style={styles.summaryStock}>
                {offer.disponivel ? 'Disponível' : 'Indisponível'}
              </Text>
            </View>
          ))}
        </View>
      )}

      <Text style={styles.sectionTitle}>Evolução dos preços</Text>

      {historyMessage ? (
        <View style={styles.messageBox}>
          <Text style={styles.messageText}>{historyMessage}</Text>
        </View>
      ) : null}

      {isLoadingHistory ? (
        <Text style={styles.feedbackText}>Carregando histórico...</Text>
      ) : (
        <HistoryChart series={series} />
      )}

      {!!currentOffers.length && (
        <>
          <Text style={styles.sectionTitle}>Ofertas atuais</Text>

          <View style={styles.offersBox}>
            {currentOffers.map((offer, index) => (
              <OfferRow
                key={offer.id}
                medicineName={medicine.nome}
                pharmacy={getPharmacyName(offer)}
                price={Number(offer.preco)}
                color={getColorByIndex(index)}
              />
            ))}
          </View>
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  headerBox: {
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: palette.text,
  },
  subtitle: {
    marginTop: 6,
    fontSize: 15,
    color: palette.textSoft,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
    marginTop: spacing.md,
  },
  summaryCard: {
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: '#E6E6E6',
    borderRadius: radius.lg,
    padding: spacing.md,
  },
  summaryTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  summaryDot: {
    width: 12,
    height: 12,
    borderRadius: radius.pill,
  },
  summaryPharmacy: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: palette.text,
  },
  summaryPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: palette.text,
    marginBottom: 6,
  },
  summaryStock: {
    fontSize: 13,
    color: palette.success,
    fontWeight: '600',
  },
  sectionTitle: {
    marginTop: spacing.xl,
    fontSize: 24,
    color: palette.text,
    fontWeight: '700',
  },
  offersBox: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E6E6E6',
    paddingHorizontal: spacing.md,
    marginTop: spacing.sm,
  },
  messageBox: {
    marginTop: spacing.sm,
    backgroundColor: '#FFF8E8',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: '#F5D48A',
    padding: spacing.md,
  },
  messageText: {
    color: palette.textSoft,
    fontSize: 14,
    lineHeight: 20,
  },
  feedbackText: {
    marginTop: spacing.lg,
    fontSize: 16,
    color: palette.textSoft,
  },
  notFoundBox: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
    gap: spacing.md,
  },
  notFoundTitle: {
    fontSize: 24,
    color: palette.text,
    fontWeight: '700',
  },
  notFoundText: {
    fontSize: 15,
    color: palette.textSoft,
    textAlign: 'center',
  },
});