import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import React, { useState } from 'react';

import {
  Image,
  Platform,
  Pressable,
  StyleSheet,
  Switch,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';

import { Screen } from '../../components/Screen';
import { useAppContext } from '../../context/AppContext';
import { palette, radius, shadow, spacing } from '../../theme';
import { Oferta } from '../../types/api';

type OfertaComExtras = Oferta & {
  farmacia_nome?: string;
  farmacia?: {
    nome_fantasia?: string;
    razao_social?: string;
  };
};

function getLowestOfferFromBackend(offers?: Oferta[]) {
  if (!offers?.length) {
    return undefined;
  }

  return [...offers].sort((a, b) => Number(a.preco) - Number(b.preco))[0];
}

function formatPrice(value?: number) {
  if (value === undefined || !Number.isFinite(value)) {
    return '--';
  }

  return `R$ ${value.toFixed(2).replace('.', ',')}`;
}

function getPharmacyName(offer?: OfertaComExtras) {
  if (!offer) {
    return 'Sem ofertas';
  }

  return (
    offer.farmacia_nome ||
    offer.farmacia?.nome_fantasia ||
    offer.farmacia?.razao_social ||
    'Farmácia disponível'
  );
}

export default function FavoritesScreen() {
  const router = useRouter();

  const { width } = useWindowDimensions();

  const {
    favoriteMedicines,
    toggleFavorite,
    markAsViewed,
    sessionMode,
  } = useAppContext();

  const [notificationMap, setNotificationMap] = useState<Record<number, boolean>>(
    {}
  );

  const [hoveredId, setHoveredId] = useState<number | null>(null);

  const isWeb = Platform.OS === 'web';
  const isDesktop = isWeb && width >= 1180;
  const isTablet = isWeb && width >= 820 && width < 1180;

  const isAuthenticated = sessionMode === 'authenticated';

  const cardWidth = isDesktop ? '31.5%' : isTablet ? '48%' : '100%';

  const handleOpenMedicine = (id: number) => {
    markAsViewed(id);
    router.push(`/medicine/${id}`);
  };

  const handleToggleNotification = (id: number) => {
    setNotificationMap((current) => ({
      ...current,
      [id]: !(current[id] ?? true),
    }));
  };

  if (!isAuthenticated) {
    return (
      <Screen>
        <View style={styles.lockedPage}>
          <View style={styles.lockedCard}>
            <View style={styles.lockedIconBox}>
              <Ionicons name="heart-outline" size={42} color={palette.primary} />
            </View>

            <Text style={styles.lockedTitle}>Favoritos</Text>

            <Text style={styles.lockedText}>
              Entre na sua conta para salvar remédios favoritos, acompanhar preços e ativar alertas.
            </Text>

            <View style={styles.lockedInfoBox}>
              <View style={styles.lockedInfoRow}>
                <Ionicons
                  name="checkmark-circle-outline"
                  size={20}
                  color={palette.success}
                />

                <Text style={styles.lockedInfoText}>
                  Favoritos ficam disponíveis apenas para usuários autenticados.
                </Text>
              </View>

              <View style={styles.lockedInfoRow}>
                <Ionicons
                  name="notifications-outline"
                  size={20}
                  color={palette.primary}
                />

                <Text style={styles.lockedInfoText}>
                  Depois do login, você poderá ativar notificações de menor preço.
                </Text>
              </View>
            </View>

            <View style={styles.lockedActions}>
              <Pressable
                style={styles.primaryButton}
                onPress={() => router.push('/login' as never)}
              >
                <Text style={styles.primaryButtonText}>Fazer login</Text>
              </Pressable>

              <Pressable
                style={styles.secondaryButton}
                onPress={() => router.push('/signup' as never)}
              >
                <Text style={styles.secondaryButtonText}>Criar conta</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <View style={[styles.headerCard, isDesktop && styles.headerCardDesktop]}>
        <View style={styles.headerContent}>
          <View style={styles.headerBadge}>
            <Ionicons name="heart" size={16} color={palette.primary} />

            <Text style={styles.headerBadgeText}>Meus favoritos</Text>
          </View>

          <Text style={[styles.title, isDesktop && styles.titleDesktop]}>
            Favoritos
          </Text>

          <Text style={styles.subtitle}>
            Acompanhe seus remédios salvos, veja o menor preço atual e controle notificações.
          </Text>
        </View>

        <View style={styles.headerCounter}>
          <Text style={styles.counterValue}>{favoriteMedicines.length}</Text>

          <Text style={styles.counterLabel}>
            {favoriteMedicines.length === 1 ? 'remédio salvo' : 'remédios salvos'}
          </Text>
        </View>
      </View>

      {favoriteMedicines.length === 0 ? (
        <View style={styles.emptyState}>
          <View style={styles.emptyIconBox}>
            <Ionicons name="heart-outline" size={42} color={palette.primary} />
          </View>

          <Text style={styles.emptyTitle}>Nenhum favorito salvo</Text>

          <Text style={styles.emptyText}>
            Toque no coração de um remédio para salvar aqui e acompanhar os preços com mais facilidade.
          </Text>

          <Pressable
            style={styles.emptyButton}
            onPress={() => router.push('/home' as never)}
          >
            <Ionicons name="search-outline" size={18} color={palette.surface} />

            <Text style={styles.emptyButtonText}>Procurar remédios</Text>
          </Pressable>
        </View>
      ) : (
        <View style={[styles.grid, isWeb && styles.gridWeb]}>
          {favoriteMedicines.map((medicine) => {
            const lowest = getLowestOfferFromBackend(medicine.ofertas);
            const notificationsEnabled = notificationMap[medicine.id] ?? true;
            const imageUrl = lowest?.imagem_url;
            const price = lowest ? Number(lowest.preco) : undefined;
            const isHovered = hoveredId === medicine.id;

            return (
              <Pressable
                key={medicine.id}
                onHoverIn={() => {
                  if (isWeb) {
                    setHoveredId(medicine.id);
                  }
                }}
                onHoverOut={() => {
                  if (isWeb) {
                    setHoveredId(null);
                  }
                }}
                style={[
                  styles.card,
                  {
                    width: cardWidth,
                  },
                  isWeb && styles.cardWeb,
                  isWeb && styles.cardTransition,
                  isHovered && styles.cardHovered,
                ]}
              >
                <Pressable
                  style={[
                    styles.imageBox,
                    imageUrl && styles.imageBoxWithImage,
                  ]}
                  onPress={() => handleOpenMedicine(medicine.id)}
                >
                  <Pressable
                    style={styles.removeButton}
                    onPress={(event) => {
                      event.stopPropagation();
                      toggleFavorite(medicine.id);
                    }}
                  >
                    <Ionicons name="heart" size={18} color={palette.surface} />
                  </Pressable>

                  {imageUrl ? (
                    <Image
                      source={{ uri: imageUrl }}
                      style={styles.productImage}
                      resizeMode="contain"
                    />
                  ) : (
                    <View style={styles.imageFallback}>
                      <Ionicons
                        name="medical-outline"
                        size={48}
                        color={palette.primary}
                      />
                    </View>
                  )}
                </Pressable>

                <View style={styles.cardContent}>
                  <View style={styles.notificationRow}>
                    <View style={styles.notificationTextBox}>
                      <Text style={styles.notificationTitle}>
                        Alerta de preço
                      </Text>

                      <Text
                        style={[
                          styles.notificationLabel,
                          notificationsEnabled
                            ? styles.notificationEnabled
                            : styles.notificationDisabled,
                        ]}
                      >
                        {notificationsEnabled
                          ? 'Receber notificação de menor preço'
                          : 'Notificação desativada'}
                      </Text>
                    </View>

                    <View style={styles.switchWrapper}>
                      <Switch
                        value={notificationsEnabled}
                        onValueChange={() => handleToggleNotification(medicine.id)}
                        trackColor={{
                          false: '#D8D8D8',
                          true: '#9FE3A5',
                        }}
                        thumbColor={notificationsEnabled ? '#34C759' : '#F4F4F4'}
                        style={isWeb ? styles.switchWeb : undefined}
                      />
                    </View>
                  </View>

                  <Pressable
                    style={styles.infoPressArea}
                    onPress={() => handleOpenMedicine(medicine.id)}
                  >
                    <Text
                      numberOfLines={2}
                      style={[styles.name, isWeb && styles.nameWeb]}
                    >
                      {medicine.nome}
                    </Text>

                    <View style={styles.pharmacyRow}>
                      <Ionicons
                        name="storefront-outline"
                        size={15}
                        color={palette.primary}
                      />

                      <Text
                        numberOfLines={1}
                        style={[styles.pharmacy, isWeb && styles.pharmacyWeb]}
                      >
                        {getPharmacyName(lowest as OfertaComExtras)}
                      </Text>
                    </View>

                    <View style={styles.priceRow}>
                      <View>
                        <Text style={styles.priceLabel}>Menor preço</Text>

                        <Text style={[styles.price, isWeb && styles.priceWeb]}>
                          {formatPrice(price)}
                        </Text>
                      </View>

                      <View style={styles.openButton}>
                        <Ionicons
                          name="chevron-forward"
                          size={18}
                          color={palette.surface}
                        />
                      </View>
                    </View>
                  </Pressable>
                </View>
              </Pressable>
            );
          })}
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  headerCard: {
    backgroundColor: palette.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.lg,
    gap: spacing.lg,
    marginBottom: spacing.lg,
    ...shadow.soft,
  },

  headerCardDesktop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.xl,
  },

  headerContent: {
    flex: 1,
  },

  headerBadge: {
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

  headerBadgeText: {
    color: palette.primary,
    fontSize: 12,
    fontWeight: '900',
  },

  title: {
    color: palette.text,
    fontSize: 32,
    lineHeight: 38,
    fontWeight: '900',
  },

  titleDesktop: {
    fontSize: 42,
    lineHeight: 48,
  },

  subtitle: {
    marginTop: spacing.sm,
    color: palette.textSoft,
    fontSize: 15,
    lineHeight: 22,
    maxWidth: 680,
  },

  headerCounter: {
    backgroundColor: '#F8FBFF',
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E2EDFA',
    padding: spacing.lg,
  },

  counterValue: {
    color: palette.primaryDark,
    fontSize: 34,
    fontWeight: '900',
  },

  counterLabel: {
    marginTop: 2,
    color: palette.textSoft,
    fontSize: 13,
    fontWeight: '800',
  },

  lockedPage: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: spacing.xl,
  },

  lockedCard: {
    width: '100%',
    maxWidth: 560,
    backgroundColor: palette.surface,
    borderRadius: 30,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.xl,
    alignItems: 'center',
    ...shadow.medium,
  },

  lockedIconBox: {
    width: 86,
    height: 86,
    borderRadius: 30,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },

  lockedTitle: {
    color: palette.text,
    fontSize: 32,
    fontWeight: '900',
    textAlign: 'center',
  },

  lockedText: {
    marginTop: spacing.sm,
    textAlign: 'center',
    color: palette.textSoft,
    fontSize: 15,
    lineHeight: 22,
    maxWidth: 440,
  },

  lockedInfoBox: {
    width: '100%',
    backgroundColor: '#F8FBFF',
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: '#E2EDFA',
    padding: spacing.lg,
    gap: spacing.md,
    marginTop: spacing.xl,
  },

  lockedInfoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },

  lockedInfoText: {
    flex: 1,
    color: palette.text,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '600',
  },

  lockedActions: {
    width: '100%',
    gap: spacing.md,
    marginTop: spacing.xl,
  },

  primaryButton: {
    width: '100%',
    minHeight: 52,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  primaryButtonText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '900',
  },

  secondaryButton: {
    width: '100%',
    minHeight: 52,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: palette.primary,
    backgroundColor: palette.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },

  secondaryButtonText: {
    color: palette.primary,
    fontSize: 16,
    fontWeight: '900',
  },

  emptyState: {
    backgroundColor: palette.surface,
    borderRadius: 30,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.lg,
    ...shadow.soft,
  },

  emptyIconBox: {
    width: 82,
    height: 82,
    borderRadius: 28,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },

  emptyTitle: {
    fontSize: 24,
    fontWeight: '900',
    color: palette.text,
    textAlign: 'center',
  },

  emptyText: {
    marginTop: spacing.sm,
    fontSize: 15,
    color: palette.textSoft,
    textAlign: 'center',
    maxWidth: 440,
    lineHeight: 22,
  },

  emptyButton: {
    marginTop: spacing.xl,
    minHeight: 50,
    paddingHorizontal: spacing.xl,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },

  emptyButtonText: {
    color: palette.surface,
    fontSize: 15,
    fontWeight: '900',
  },

  grid: {
    gap: spacing.lg,
  },

  gridWeb: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    rowGap: 28,
    columnGap: 28,
  },

  card: {
    backgroundColor: palette.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: palette.border,
    overflow: 'hidden',
    padding: spacing.md,
    ...shadow.soft,
  },

  cardWeb: {
    minHeight: 470,
    cursor: 'default' as any,
  },

  cardTransition: {
    transitionDuration: '180ms' as any,
    transitionProperty: 'transform, box-shadow, border-color' as any,
    transitionTimingFunction: 'ease-out' as any,
  },

  cardHovered: {
    borderColor: palette.primary,
    transform: [
      {
        translateY: -6,
      },
      {
        scale: 1.01,
      },
    ],
    shadowOpacity: 0.15,
    shadowRadius: 26,
    shadowOffset: {
      width: 0,
      height: 14,
    },
    elevation: 8,
  },

  imageBox: {
    width: '100%',
    height: 250,
    borderRadius: radius.lg,
    backgroundColor: palette.surfaceBlue,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    marginBottom: spacing.md,
    overflow: 'hidden',
    cursor: 'pointer' as any,
  },

  imageBoxWithImage: {
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: '#E8E8E8',
  },

  productImage: {
    width: '100%',
    height: '100%',
  },

  imageFallback: {
    width: '72%',
    height: '72%',
    borderRadius: radius.xl,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
  },

  removeButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: palette.danger,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 3,
    borderWidth: 2,
    borderColor: palette.surface,
  },

  cardContent: {
    gap: spacing.md,
  },

  notificationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
    backgroundColor: '#F8FBFF',
    borderWidth: 1,
    borderColor: '#E2EDFA',
    borderRadius: radius.lg,
    padding: spacing.md,
  },

  notificationTextBox: {
    flex: 1,
  },

  notificationTitle: {
    color: palette.text,
    fontSize: 13,
    fontWeight: '900',
  },

  notificationLabel: {
    marginTop: 2,
    fontSize: 12,
    lineHeight: 17,
    fontWeight: '700',
  },

  notificationEnabled: {
    color: palette.success,
  },

  notificationDisabled: {
    color: palette.textSoft,
  },

  switchWrapper: {
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 56,
  },

  switchWeb: {
    transform: [{ scaleX: 1.08 }, { scaleY: 1.08 }],
  },

  infoPressArea: {
    gap: spacing.sm,
    cursor: 'pointer' as any,
  },

  name: {
    fontSize: 20,
    lineHeight: 26,
    fontWeight: '900',
    color: palette.text,
  },

  nameWeb: {
    fontSize: 22,
    lineHeight: 29,
  },

  pharmacyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },

  pharmacy: {
    flex: 1,
    fontSize: 13,
    fontWeight: '800',
    color: palette.primary,
  },

  pharmacyWeb: {
    fontSize: 14,
  },

  priceRow: {
    marginTop: spacing.xs,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    gap: spacing.md,
  },

  priceLabel: {
    color: palette.textSoft,
    fontSize: 12,
    fontWeight: '800',
    marginBottom: 2,
  },

  price: {
    fontSize: 28,
    fontWeight: '900',
    color: palette.text,
  },

  priceWeb: {
    fontSize: 32,
  },

  openButton: {
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
});