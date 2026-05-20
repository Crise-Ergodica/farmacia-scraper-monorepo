import { Ionicons } from '@expo/vector-icons';
import { router, useRouter } from 'expo-router';
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
import { palette, radius, spacing } from '../../theme';
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
    `Farmácia ID: ${offer.farmacia_id}`
  );
}

export default function FavoritesScreen() {
  const routerNav = useRouter();
  const { width } = useWindowDimensions();
  const { favoriteMedicines, toggleFavorite, markAsViewed, sessionMode } = useAppContext();

  const [notificationMap, setNotificationMap] = useState<Record<number, boolean>>({});

  const isWeb = Platform.OS === 'web';
  const isDesktop = isWeb && width >= 1200;
  const isTablet = isWeb && width >= 900 && width < 1200;

  const cardWidth = isDesktop ? 320 : isTablet ? 280 : '100%';

  const handleOpenMedicine = (id: number) => {
    markAsViewed(id);
    routerNav.push(`/medicine/${id}`);
  };

  const handleToggleNotification = (id: number) => {
    setNotificationMap((current) => ({
      ...current,
      [id]: !(current[id] ?? true),
    }));
  };

  if (sessionMode !== 'authenticated') {
    return (
      <Screen>
        <View style={styles.lockedWrapper}>
          <Ionicons name="lock-closed-outline" size={50} color={palette.primary} />
          <Text style={[styles.title, isWeb && styles.titleWeb]}>Favoritos</Text>
          <Text style={styles.lockedText}>
            Recurso para usuários autenticados. Deseja criar uma conta ou logar em
            uma conta existente?
          </Text>

          <Pressable style={styles.primaryButton} onPress={() => router.push('/signup' as any)}>
            <Text style={styles.primaryButtonText}>Criar conta</Text>
          </Pressable>

          <Pressable style={styles.secondaryButton} onPress={() => router.push('/login' as any)}>
            <Text style={styles.secondaryButtonText}>Fazer login</Text>
          </Pressable>
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <Text style={[styles.title, isWeb && styles.titleWeb]}>Favoritos</Text>

      {favoriteMedicines.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="heart-outline" size={42} color={palette.primary} />
          <Text style={styles.emptyTitle}>Nenhum favorito salvo</Text>
          <Text style={styles.emptyText}>
            Adicione remédios aos favoritos para acompanhar preços e alertas.
          </Text>
        </View>
      ) : (
        <View style={[styles.grid, isWeb && styles.gridWeb]}>
          {favoriteMedicines.map((medicine) => {
            const lowest = getLowestOfferFromBackend(medicine.ofertas);
            const notificationsEnabled = notificationMap[medicine.id] ?? true;
            const imageUrl = lowest?.imagem_url;
            const price = lowest ? Number(lowest.preco) : undefined;

            return (
              <View
                key={medicine.id}
                style={[
                  styles.card,
                  isWeb && styles.cardWeb,
                  { width: cardWidth },
                ]}
              >
                <View style={[styles.imageBox, imageUrl && styles.imageBoxWithImage]}>
                  <Pressable
                    style={styles.imageOpenButton}
                    onPress={() => handleOpenMedicine(medicine.id)}
                  />

                  <Pressable
                    style={styles.removeButton}
                    onPress={() => toggleFavorite(medicine.id)}
                  >
                    <Ionicons name="trash-outline" size={16} color={palette.surface} />
                  </Pressable>

                  {imageUrl ? (
                    <Image
                      source={{ uri: imageUrl }}
                      style={styles.productImage}
                      resizeMode="contain"
                    />
                  ) : (
                    <Ionicons
                      name="image-outline"
                      size={isWeb ? 34 : 28}
                      color={palette.textSoft}
                    />
                  )}
                </View>

                <View style={styles.cardContent}>
                  <View style={styles.notificationRow}>
                    <Text style={[styles.notificationLabel, isWeb && styles.notificationLabelWeb]}>
                      Receber notificação de menor preço?
                    </Text>

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
                    <Text style={[styles.name, isWeb && styles.nameWeb]} numberOfLines={2}>
                      {medicine.nome}
                    </Text>

                    <Text style={[styles.pharmacy, isWeb && styles.pharmacyWeb]}>
                      {getPharmacyName(lowest as OfertaComExtras)}
                    </Text>

                    <Text style={[styles.price, isWeb && styles.priceWeb]}>
                      {formatPrice(price)}
                    </Text>
                  </Pressable>
                </View>
              </View>
            );
          })}
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: {
    color: palette.primary,
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  titleWeb: {
    fontSize: 40,
    marginBottom: 28,
  },
  lockedWrapper: {
    width: '100%',
    maxWidth: 540,
    alignSelf: 'center',
    alignItems: 'center',
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E7E7E7',
    padding: spacing.xl,
    marginTop: spacing.xl,
  },
  lockedText: {
    textAlign: 'center',
    color: palette.text,
    fontSize: 16,
    lineHeight: 24,
    marginBottom: spacing.xl,
  },
  primaryButton: {
    width: '100%',
    minHeight: 50,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  primaryButtonText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    width: '100%',
    minHeight: 50,
    borderRadius: radius.pill,
    borderWidth: 1.5,
    borderColor: palette.primary,
    backgroundColor: palette.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: palette.primary,
    fontSize: 16,
    fontWeight: '700',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 56,
    gap: spacing.md,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: palette.text,
  },
  emptyText: {
    fontSize: 15,
    color: palette.textSoft,
    textAlign: 'center',
    maxWidth: 420,
    lineHeight: 24,
  },
  grid: {
    gap: spacing.lg,
  },
  gridWeb: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    rowGap: 28,
    columnGap: 28,
  },
  card: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E5E5E5',
    overflow: 'hidden',
  },
  cardWeb: {
    padding: 14,
  },
  imageBox: {
    width: '100%',
    height: 290,
    borderRadius: radius.lg,
    backgroundColor: '#ECECEC',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    marginBottom: spacing.md,
    overflow: 'hidden',
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
  imageOpenButton: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 1,
  },
  removeButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 30,
    height: 30,
    borderRadius: radius.pill,
    backgroundColor: palette.danger,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 3,
  },
  cardContent: {
    gap: spacing.sm,
  },
  notificationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
  },
  notificationLabel: {
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
    color: '#69C36D',
    fontWeight: '600',
  },
  notificationLabelWeb: {
    fontSize: 14,
    lineHeight: 20,
  },
  switchWrapper: {
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 56,
  },
  switchWeb: {
    transform: [{ scaleX: 1.15 }, { scaleY: 1.15 }],
  },
  infoPressArea: {
    gap: spacing.xs,
  },
  name: {
    fontSize: 18,
    fontWeight: '500',
    color: palette.text,
  },
  nameWeb: {
    fontSize: 24,
    lineHeight: 30,
  },
  pharmacy: {
    fontSize: 13,
    fontWeight: '600',
    color: palette.primary,
  },
  pharmacyWeb: {
    fontSize: 15,
  },
  price: {
    fontSize: 28,
    fontWeight: '700',
    color: palette.text,
  },
  priceWeb: {
    fontSize: 34,
  },
});