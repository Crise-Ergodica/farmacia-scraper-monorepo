import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import {
  Image,
  Linking,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';

import { AuthRequiredModal } from '../../../components/AuthRequiredModal';
import { Screen } from '../../../components/Screen';
import { SearchBar } from '../../../components/SearchBar';
import { useAppContext } from '../../../context/AppContext';
import { palette, radius, spacing } from '../../../theme';
import { Oferta } from '../../../types/api';

type OfertaComExtras = Oferta & {
  farmacia_nome?: string;
  farmacia?: {
    nome_fantasia?: string;
    razao_social?: string;
  };
};

const PHARMACY_NAME_MAP: Record<number, string> = {
  1: 'Farmácia Indiana',
  2: 'Drogaria Araújo',
};

function getOfferPrice(offer?: Oferta) {
  if (!offer) return Infinity;
  return Number(offer.preco);
}

function formatPrice(value?: number) {
  if (value === undefined || !Number.isFinite(value)) {
    return 'Sem preço';
  }

  return `R$ ${value.toFixed(2).replace('.', ',')}`;
}

function normalizeUrl(url?: string) {
  if (!url) return '';

  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }

  return `https://${url}`;
}

function getPharmacyName(offer: OfertaComExtras) {
  return (
    offer.farmacia_nome ||
    offer.farmacia?.nome_fantasia ||
    offer.farmacia?.razao_social ||
    PHARMACY_NAME_MAP[offer.farmacia_id] ||
    `Farmácia ${offer.farmacia_id}`
  );
}

export default function MedicineDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string | string[] }>();

  const {
    getMedicineById,
    favoriteIds,
    toggleFavorite,
    markAsViewed,
    sessionMode,
  } = useAppContext();

  const [search, setSearch] = useState('Preço Bão');
  const [showAuthModal, setShowAuthModal] = useState(false);

  const { width } = useWindowDimensions();

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

  useEffect(() => {
    if (medicineId !== null) {
      markAsViewed(medicineId);
    }
  }, [medicineId, markAsViewed]);

  const offers = useMemo(() => {
    if (!medicine?.ofertas?.length) {
      return [];
    }

    return [...medicine.ofertas].sort((a, b) => getOfferPrice(a) - getOfferPrice(b));
  }, [medicine]);

  const lowest = offers[0];
  const isFavorite = medicineId !== null && favoriteIds.includes(medicineId);

  const isWeb = Platform.OS === 'web';
  const isDesktop = isWeb && width >= 1100;
  const isTablet = isWeb && width >= 850 && width < 1100;

  const imageUrl = lowest?.imagem_url;
  const productUrl = normalizeUrl(lowest?.url_origem);
  const lowestPrice = lowest ? Number(lowest.preco) : undefined;

  const handleToggleFavorite = () => {
    if (sessionMode !== 'authenticated') {
      setShowAuthModal(true);
      return;
    }

    if (medicineId !== null) {
      toggleFavorite(medicineId);
    }
  };

  const handleOpenProductSite = async (url?: string) => {
    const normalized = normalizeUrl(url);

    if (!normalized) {
      return;
    }

    try {
      const canOpen = await Linking.canOpenURL(normalized);

      if (canOpen) {
        await Linking.openURL(normalized);
      }
    } catch (error) {
      console.error('Erro ao abrir site do remédio:', error);
    }
  };

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
          <Ionicons name="alert-circle-outline" size={42} color={palette.primary} />
          <Text style={styles.notFoundTitle}>Medicamento não encontrado</Text>
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

      <View style={[styles.layout, isDesktop && styles.layoutDesktop]}>
        <View style={styles.mainColumn}>
          <View
            style={[
              styles.imageCard,
              isTablet && styles.imageCardTablet,
              isDesktop && styles.imageCardDesktop,
              imageUrl && styles.imageCardWithImage,
            ]}
          >
            {imageUrl ? (
              <Image source={{ uri: imageUrl }} style={styles.productImage} resizeMode="contain" />
            ) : (
              <Ionicons name="image-outline" size={isDesktop ? 64 : 52} color={palette.text} />
            )}
          </View>

          <View style={styles.headerRow}>
            <View style={styles.infoBlock}>
              <Text style={[styles.name, isDesktop && styles.nameDesktop]}>
                {medicine.nome}
              </Text>

              <Text style={[styles.price, isDesktop && styles.priceDesktop]}>
                {formatPrice(lowestPrice)}
              </Text>

              {lowest ? (
                <Text style={styles.lowestStoreText}>
                  Menor preço em {getPharmacyName(lowest as OfertaComExtras)}
                </Text>
              ) : (
                <Text style={styles.lowestStoreText}>Nenhuma oferta disponível</Text>
              )}
            </View>

            <Pressable style={styles.favoriteButton} onPress={handleToggleFavorite}>
              <Ionicons
                name={isFavorite ? 'heart' : 'heart-outline'}
                size={30}
                color={isFavorite ? palette.danger : palette.text}
              />
            </Pressable>
          </View>

          <Text style={styles.sectionLabel}>Descrição</Text>

          <View style={styles.descriptionBox}>
            <Text style={[styles.description, isDesktop && styles.descriptionDesktop]}>
              Princípio ativo: {medicine.principio_ativo || 'Não informado'}
            </Text>
            <Text style={[styles.description, isDesktop && styles.descriptionDesktop]}>
              Laboratório: {medicine.laboratorio || 'Não informado'}
            </Text>
            <Text style={[styles.description, isDesktop && styles.descriptionDesktop]}>
              Código de barras: {medicine.codigo_barras || 'Não informado'}
            </Text>
            <Text style={[styles.description, isDesktop && styles.descriptionDesktop]}>
              {medicine.exige_receita ? 'Exige receita médica.' : 'Venda livre.'}
            </Text>
          </View>

          <View style={styles.buttonGroup}>
            <Pressable
              style={[
                styles.siteButton,
                !productUrl && styles.disabledButton,
                isDesktop && styles.actionButtonDesktop,
              ]}
              disabled={!productUrl}
              onPress={() => handleOpenProductSite(productUrl)}
            >
              <Ionicons name="open-outline" size={20} color={palette.surface} />
              <Text style={styles.siteButtonText}>Ir para o site do remédio</Text>
            </Pressable>

            <Pressable
              style={[styles.historyButton, isDesktop && styles.actionButtonDesktop]}
              onPress={() => router.push(`/history/${medicine.id}`)}
            >
              <Ionicons name="stats-chart-outline" size={20} color={palette.primary} />
              <Text style={styles.historyButtonText}>Ver histórico de preços</Text>
            </Pressable>
          </View>
        </View>

        <View style={[styles.offersPanel, isDesktop && styles.offersPanelDesktop]}>
          <View style={styles.offersHeader}>
            <Text style={styles.offersTitle}>Outras farmácias disponíveis</Text>
            <Text style={styles.offersSubtitle}>{offers.length} ofertas encontradas</Text>
          </View>

          {lowest ? (
            <View style={styles.lowestBox}>
              <Text style={styles.lowestLabel}>Menor preço</Text>
              <Text style={styles.lowestPharmacy}>
                {getPharmacyName(lowest as OfertaComExtras)}
              </Text>
              <Text style={styles.lowestPrice}>{formatPrice(Number(lowest.preco))}</Text>
            </View>
          ) : null}

          <View style={styles.offersList}>
            {offers.map((offer) => {
              const pharmacyName = getPharmacyName(offer as OfertaComExtras);
              const offerUrl = normalizeUrl(offer.url_origem);

              return (
                <View key={offer.id} style={styles.offerRow}>
                  <View style={styles.offerLeft}>
                    <View style={styles.offerDot} />

                    <View style={styles.offerInfo}>
                      <Text style={styles.offerName} numberOfLines={1}>
                        {pharmacyName}
                      </Text>

                      <Text style={styles.offerPrice}>
                        {formatPrice(Number(offer.preco))}
                      </Text>
                    </View>
                  </View>

                  <Pressable
                    style={[styles.offerSiteButton, !offerUrl && styles.disabledSmallButton]}
                    disabled={!offerUrl}
                    onPress={() => handleOpenProductSite(offerUrl)}
                  >
                    <Text style={styles.offerSiteButtonText}>Abrir site</Text>
                  </Pressable>
                </View>
              );
            })}
          </View>
        </View>
      </View>

      <AuthRequiredModal
        visible={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  layout: {
    marginTop: spacing.md,
    gap: spacing.xl,
  },
  layoutDesktop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  mainColumn: {
    flex: 1,
  },
  imageCard: {
    width: '100%',
    aspectRatio: 1.35,
    borderRadius: radius.lg,
    backgroundColor: '#ECECEC',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  imageCardWithImage: {
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: '#E8E8E8',
  },
  imageCardTablet: {
    aspectRatio: 1.55,
  },
  imageCardDesktop: {
    height: 420,
    aspectRatio: undefined,
  },
  productImage: {
    width: '100%',
    height: '100%',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginTop: spacing.lg,
    gap: spacing.md,
  },
  infoBlock: {
    flex: 1,
  },
  favoriteButton: {
    width: 48,
    height: 48,
    borderRadius: radius.pill,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: '#E8E8E8',
  },
  name: {
    fontSize: 24,
    color: palette.text,
    fontWeight: '600',
    marginBottom: spacing.xs,
  },
  nameDesktop: {
    fontSize: 42,
    lineHeight: 48,
  },
  price: {
    fontSize: 24,
    color: palette.text,
    fontWeight: '700',
  },
  priceDesktop: {
    fontSize: 30,
  },
  lowestStoreText: {
    marginTop: 8,
    color: palette.textSoft,
    fontSize: 15,
  },
  sectionLabel: {
    fontSize: 20,
    fontWeight: '700',
    color: palette.text,
    marginTop: spacing.xl,
    marginBottom: spacing.sm,
  },
  descriptionBox: {
    gap: 6,
    maxWidth: 760,
  },
  description: {
    color: palette.textSoft,
    fontSize: 15,
    lineHeight: 24,
  },
  descriptionDesktop: {
    fontSize: 16,
    lineHeight: 28,
  },
  buttonGroup: {
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  actionButtonDesktop: {
    maxWidth: 760,
  },
  siteButton: {
    minHeight: 52,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  siteButtonText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  historyButton: {
    minHeight: 52,
    borderRadius: radius.pill,
    backgroundColor: palette.surface,
    borderWidth: 1.5,
    borderColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
    gap: spacing.sm,
  },
  historyButtonText: {
    color: palette.primary,
    fontSize: 16,
    fontWeight: '700',
  },
  disabledButton: {
    backgroundColor: palette.muted,
  },
  offersPanel: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E4E4E4',
    padding: spacing.md,
  },
  offersPanelDesktop: {
    width: 390,
    position: 'sticky' as any,
    top: 24,
  },
  offersHeader: {
    marginBottom: spacing.md,
  },
  offersTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: palette.text,
    marginBottom: 4,
  },
  offersSubtitle: {
    fontSize: 13,
    color: palette.textSoft,
  },
  lowestBox: {
    borderRadius: radius.md,
    backgroundColor: '#F5F9FF',
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  lowestLabel: {
    fontSize: 12,
    color: palette.textSoft,
    marginBottom: 4,
  },
  lowestPharmacy: {
    fontSize: 16,
    fontWeight: '700',
    color: palette.primary,
    marginBottom: 4,
  },
  lowestPrice: {
    fontSize: 28,
    fontWeight: '700',
    color: palette.text,
  },
  offersList: {
    gap: spacing.sm,
  },
  offerRow: {
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: '#F7F7F7',
    borderWidth: 1,
    borderColor: '#E6E6E6',
  },
  offerLeft: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },
  offerDot: {
    width: 12,
    height: 12,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    marginTop: 5,
  },
  offerInfo: {
    flex: 1,
  },
  offerName: {
    fontSize: 15,
    color: palette.text,
    fontWeight: '700',
    marginBottom: 8,
  },
  offerPrice: {
    fontSize: 22,
    fontWeight: '700',
    color: palette.text,
  },
  offerSiteButton: {
    minHeight: 38,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  offerSiteButtonText: {
    color: palette.surface,
    fontSize: 14,
    fontWeight: '700',
  },
  disabledSmallButton: {
    backgroundColor: palette.muted,
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