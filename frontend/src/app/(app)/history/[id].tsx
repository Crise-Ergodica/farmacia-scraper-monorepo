import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';

import {
  ActivityIndicator,
  Platform,
  Pressable,
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
import { api } from '../../../services/api';

import { palette, radius, spacing } from '../../../theme';

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

function getLowestOffer(offers: Oferta[]) {
  if (!offers.length) {
    return undefined;
  }

  return [...offers].sort((a, b) => Number(a.preco) - Number(b.preco))[0];
}

function buildFallbackSeries(medicine: Medicamento): HistoryChartSeries[] {
  const offers = [...(medicine.ofertas || [])].sort(
    (a, b) => Number(a.preco) - Number(b.preco)
  );

  return offers.map((offer, index) => ({
    key: String(offer.id || offer.farmacia_id),
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

function normalizeHistoryPayload(
  payload: HistoricoResponseItem[]
): HistoryChartSeries[] {
  if (!Array.isArray(payload) || payload.length === 0) {
    return [];
  }

  if ('historico' in payload[0]) {
    return (payload as HistoricoPrecoSerie[]).map((item, index) => ({
      key: String(item.farmacia_id),
      label: item.farmacia_nome || `Farmácia ${item.farmacia_id}`,
      color: getColorByIndex(index),
      history: [...item.historico]
        .sort(
          (a, b) =>
            new Date(a.data_registro).getTime() -
            new Date(b.data_registro).getTime()
        )
        .map((point) => ({
          label: formatDateLabel(point.data_registro),
          value: Number(point.preco),
        })),
    }));
  }

  const grouped = new Map<
    number,
    {
      pharmacyName: string;
      points: {
        data_registro: string;
        preco: number;
      }[];
    }
  >();

  (payload as HistoricoResponseItem[]).forEach((item) => {
    if (!('farmacia_id' in item)) {
      return;
    }

    const record = item as {
      farmacia_id: number;
      farmacia_nome?: string;
      data_registro: string;
      preco_registrado?: number;
      preco?: number;
    };

    const price = Number(record.preco_registrado ?? record.preco ?? 0);
    const pharmacyId = record.farmacia_id;
    const pharmacyName = record.farmacia_nome || `Farmácia ${pharmacyId}`;

    if (!grouped.has(pharmacyId)) {
      grouped.set(pharmacyId, {
        pharmacyName,
        points: [],
      });
    }

    grouped.get(pharmacyId)?.points.push({
      data_registro: record.data_registro,
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
          new Date(a.data_registro).getTime() -
          new Date(b.data_registro).getTime()
      )
      .map((point) => ({
        label: formatDateLabel(point.data_registro),
        value: Number(point.preco),
      })),
  }));
}

export default function HistoryScreen() {
  const router = useRouter();

  const handleBack = () => {
  if (router.canGoBack()) {
    router.back();
    return;
  }

  router.replace('/home');
};

  const params = useLocalSearchParams<{
    id?: string | string[];
  }>();

  const { getMedicineById, isLoading } = useAppContext();

  const [search, setSearch] = useState('Preço Bão');
  const [series, setSeries] = useState<HistoryChartSeries[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [historyMessage, setHistoryMessage] = useState('');

  const { width } = useWindowDimensions();

  const isWeb = Platform.OS === 'web';
  const isDesktop = isWeb && width >= 1100;
  const isTablet = isWeb && width >= 800 && width < 1100;

  const medicineId = useMemo(() => {
    const rawId = Array.isArray(params.id) ? params.id[0] : params.id;
    const parsedId = Number(rawId);

    return Number.isFinite(parsedId) ? parsedId : null;
  }, [params.id]);

  const medicine = useMemo(() => {
    if (medicineId === null) {
      return undefined;
    }

    return getMedicineById(medicineId);
  }, [getMedicineById, medicineId]);

  const currentOffers = useMemo(() => {
    if (!medicine?.ofertas?.length) {
      return [];
    }

    return [...medicine.ofertas].sort((a, b) => Number(a.preco) - Number(b.preco));
  }, [medicine]);

  const lowestOffer = useMemo(() => getLowestOffer(currentOffers), [currentOffers]);

  const summaryCardWidth = isDesktop ? '31.5%' : isTablet ? '48%' : '100%';

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
        const response = await api.get(`/catalogo/${medicineId}/historico`);
        const data = response.data;
        const normalized = normalizeHistoryPayload(data);

        if (!normalized.length) {
          throw new Error('Sem histórico retornado');
        }

        setSeries(normalized);
      } catch (error) {
        setSeries(buildFallbackSeries(medicine));
        setHistoryMessage(
          'Ainda não há histórico real disponível. Exibindo o preço atual por farmácia.'
        );
      } finally {
        setIsLoadingHistory(false);
      }
    };

    fetchHistory();
  }, [medicine, medicineId]);

  if (isLoading) {
    return (
      <Screen contentStyle={styles.centerContent}>
        <ActivityIndicator size="large" color={palette.primary} />

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
          onSubmit={() =>
            router.push({
              pathname: '/search',
              params: {
                q: search,
              },
            })
          }
          onBack={handleBack}
        />

        <View style={styles.notFoundBox}>
          <View style={styles.notFoundIcon}>
            <Ionicons name="alert-circle-outline" size={36} color={palette.primary} />
          </View>

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
        onSubmit={() =>
          router.push({
            pathname: '/search',
            params: {
              q: search,
            },
          })
        }
        onBack={handleBack}
      />

      <View style={[styles.heroCard, isDesktop && styles.heroCardDesktop]}>
        <View style={styles.heroTextBox}>
          <View style={styles.heroBadge}>
            <Ionicons name="analytics-outline" size={16} color={palette.primary} />

            <Text style={styles.heroBadgeText}>Histórico de preços</Text>
          </View>

          <Text style={[styles.title, isDesktop && styles.titleDesktop]}>
            {medicine.nome}
          </Text>

          <Text style={styles.subtitle}>
            Veja a evolução dos preços por farmácia e compare com as ofertas atuais.
          </Text>
        </View>

        <View style={styles.heroPriceBox}>
          <Text style={styles.heroPriceLabel}>Menor preço atual</Text>

          <Text style={styles.heroPrice}>
            {lowestOffer ? formatPrice(Number(lowestOffer.preco)) : 'Sem preço'}
          </Text>

          <Text numberOfLines={1} style={styles.heroPharmacy}>
            {lowestOffer ? getPharmacyName(lowestOffer) : 'Nenhuma farmácia disponível'}
          </Text>
        </View>
      </View>

      {!!currentOffers.length && (
        <View style={styles.summaryGrid}>
          {currentOffers.slice(0, 3).map((offer, index) => (
            <View
              key={offer.id || `${offer.farmacia_id}-${index}`}
              style={[
                styles.summaryCard,
                {
                  width: summaryCardWidth,
                },
              ]}
            >
              <View style={styles.summaryTopRow}>
                <View
                  style={[
                    styles.summaryDot,
                    {
                      backgroundColor: getColorByIndex(index),
                    },
                  ]}
                />

                <Text numberOfLines={1} style={styles.summaryPharmacy}>
                  {getPharmacyName(offer)}
                </Text>
              </View>

              <Text style={styles.summaryPrice}>
                {formatPrice(Number(offer.preco))}
              </Text>

              <View
                style={[
                  styles.stockBadge,
                  offer.disponivel ? styles.stockAvailable : styles.stockUnavailable,
                ]}
              >
                <Text
                  style={[
                    styles.stockBadgeText,
                    offer.disponivel
                      ? styles.stockAvailableText
                      : styles.stockUnavailableText,
                  ]}
                >
                  {offer.disponivel ? 'Disponível' : 'Indisponível'}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      <View style={styles.sectionHeader}>
        <View>
          <Text style={styles.sectionTitle}>Evolução dos preços</Text>

          <Text style={styles.sectionSubtitle}>
            O gráfico será uma linha temporal quando o backend retornar vários pontos.
          </Text>
        </View>
      </View>

      {historyMessage ? (
        <View style={styles.messageBox}>
          <Ionicons name="information-circle-outline" size={20} color={palette.warning} />

          <Text style={styles.messageText}>{historyMessage}</Text>
        </View>
      ) : null}

      {isLoadingHistory ? (
        <View style={styles.loadingHistoryBox}>
          <ActivityIndicator size="small" color={palette.primary} />

          <Text style={styles.loadingHistoryText}>Carregando histórico...</Text>
        </View>
      ) : (
        <HistoryChart series={series} />
      )}

      {!!currentOffers.length && (
        <>
          <View style={styles.sectionHeader}>
            <View>
              <Text style={styles.sectionTitle}>Ofertas atuais</Text>

              <Text style={styles.sectionSubtitle}>
                Lista de preços disponíveis neste momento.
              </Text>
            </View>
          </View>

          <View style={styles.offersBox}>
            {currentOffers.map((offer, index) => (
              <OfferRow
                key={offer.id || `${offer.farmacia_id}-${index}`}
                medicineName={medicine.nome}
                pharmacy={getPharmacyName(offer)}
                price={offer.preco}
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
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
    paddingTop: spacing.xl * 2,
  },

  heroCard: {
    marginTop: spacing.lg,
    backgroundColor: palette.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.lg,
    gap: spacing.lg,
    shadowColor: '#0F172A',
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: {
      width: 0,
      height: 10,
    },
    elevation: 4,
  },

  heroCardDesktop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.xl,
  },

  heroTextBox: {
    flex: 1,
  },

  heroBadge: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    backgroundColor: palette.primarySoft,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 8,
    marginBottom: spacing.md,
  },

  heroBadgeText: {
    color: palette.primary,
    fontSize: 12,
    fontWeight: '900',
  },

  title: {
    fontSize: 28,
    lineHeight: 34,
    fontWeight: '900',
    color: palette.text,
  },

  titleDesktop: {
    fontSize: 40,
    lineHeight: 46,
  },

  subtitle: {
    marginTop: spacing.sm,
    fontSize: 15,
    lineHeight: 22,
    color: palette.textSoft,
    maxWidth: 660,
  },

  heroPriceBox: {
    backgroundColor: '#F8FBFF',
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E7EEF8',
    padding: spacing.lg,
    minWidth: 240,
  },

  heroPriceLabel: {
    color: palette.textSoft,
    fontSize: 13,
    fontWeight: '800',
  },

  heroPrice: {
    marginTop: 6,
    color: palette.primaryDark,
    fontSize: 32,
    fontWeight: '900',
  },

  heroPharmacy: {
    marginTop: 4,
    color: palette.text,
    fontSize: 14,
    fontWeight: '700',
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
    borderColor: palette.border,
    borderRadius: radius.xl,
    padding: spacing.lg,
    shadowColor: '#0F172A',
    shadowOpacity: 0.06,
    shadowRadius: 14,
    shadowOffset: {
      width: 0,
      height: 8,
    },
    elevation: 3,
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
    fontWeight: '800',
    color: palette.text,
  },

  summaryPrice: {
    fontSize: 25,
    fontWeight: '900',
    color: palette.text,
    marginBottom: spacing.sm,
  },

  stockBadge: {
    alignSelf: 'flex-start',
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 7,
  },

  stockAvailable: {
    backgroundColor: '#EAF8EF',
  },

  stockUnavailable: {
    backgroundColor: '#FFF1F1',
  },

  stockBadgeText: {
    fontSize: 12,
    fontWeight: '900',
  },

  stockAvailableText: {
    color: palette.success,
  },

  stockUnavailableText: {
    color: palette.danger,
  },

  sectionHeader: {
    marginTop: spacing.xl,
    marginBottom: spacing.sm,
  },

  sectionTitle: {
    fontSize: 24,
    color: palette.text,
    fontWeight: '900',
  },

  sectionSubtitle: {
    marginTop: 4,
    color: palette.textSoft,
    fontSize: 14,
    lineHeight: 20,
  },

  offersBox: {
    backgroundColor: palette.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: palette.border,
    paddingHorizontal: spacing.md,
    marginTop: spacing.sm,
    overflow: 'hidden',
  },

  messageBox: {
    marginTop: spacing.sm,
    marginBottom: spacing.sm,
    backgroundColor: '#FFF8E8',
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#F5D48A',
    padding: spacing.md,
    flexDirection: 'row',
    gap: spacing.sm,
    alignItems: 'flex-start',
  },

  messageText: {
    flex: 1,
    color: palette.text,
    fontSize: 14,
    lineHeight: 20,
  },

  loadingHistoryBox: {
    marginTop: spacing.sm,
    backgroundColor: palette.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },

  loadingHistoryText: {
    fontSize: 15,
    color: palette.textSoft,
    fontWeight: '700',
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

  notFoundIcon: {
    width: 70,
    height: 70,
    borderRadius: radius.xl,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
  },

  notFoundTitle: {
    fontSize: 24,
    color: palette.text,
    fontWeight: '900',
  },

  notFoundText: {
    fontSize: 15,
    color: palette.textSoft,
    textAlign: 'center',
    lineHeight: 22,
    maxWidth: 420,
  },
});