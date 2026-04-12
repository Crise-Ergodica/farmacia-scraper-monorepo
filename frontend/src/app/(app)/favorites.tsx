import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import React, { useMemo, useState } from 'react';
import {
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
import { getLowestOffer, medicines, pharmacyColors } from '../../data/mockData';
import { palette, radius, spacing } from '../../theme';

export default function FavoritesScreen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const { favoriteIds, toggleFavorite, markAsViewed } = useAppContext();

  const favoriteMedicines = useMemo(
    () => medicines.filter((medicine) => favoriteIds.includes(medicine.id)),
    [favoriteIds]
  );

  const [notificationMap, setNotificationMap] = useState<Record<string, boolean>>(
    Object.fromEntries(favoriteIds.map((id) => [id, true]))
  );

  const isWeb = Platform.OS === 'web';
  const isDesktop = isWeb && width >= 1200;
  const isTablet = isWeb && width >= 900 && width < 1200;

  const cardWidth = isDesktop ? 320 : isTablet ? 280 : '100%';

  const handleOpenMedicine = (id: string) => {
    markAsViewed(id);
    router.push(`/medicine/${id}`);
  };

  const handleToggleNotification = (id: string) => {
    setNotificationMap((current) => ({
      ...current,
      [id]: !current[id],
    }));
  };

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
            const lowest = getLowestOffer(medicine);
            const notificationsEnabled = notificationMap[medicine.id] ?? true;

            return (
              <View
                key={medicine.id}
                style={[
                  styles.card,
                  isWeb && styles.cardWeb,
                  { width: cardWidth },
                ]}
              >
                <View style={styles.imageBox}>
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

                  <Ionicons
                    name="image-outline"
                    size={isWeb ? 34 : 28}
                    color={palette.textSoft}
                  />
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
                      {medicine.name}
                    </Text>

                    <Text
                      style={[
                        styles.pharmacy,
                        isWeb && styles.pharmacyWeb,
                        { color: pharmacyColors[lowest.pharmacy] ?? palette.primary },
                      ]}
                    >
                      {lowest.pharmacy}
                    </Text>

                    <Text style={[styles.price, isWeb && styles.priceWeb]}>
                      ${lowest.price.toFixed(2)}
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
    backgroundColor: '#EB5B54',
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