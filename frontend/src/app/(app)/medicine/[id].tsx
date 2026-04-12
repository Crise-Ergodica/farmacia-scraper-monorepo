import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import {
  Platform,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';

import { Screen } from '../../../components/Screen';
import { SearchBar } from '../../../components/SearchBar';
import { useAppContext } from '../../../context/AppContext';
import { getLowestOffer, getSortedOffers, pharmacyColors } from '../../../data/mockData';
import { palette, radius, spacing } from '../../../theme';

export default function MedicineDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { getMedicineById, favoriteIds, toggleFavorite, markAsViewed } = useAppContext();
  const [search, setSearch] = useState('Preço Bão');
  const { width } = useWindowDimensions();

  const medicine = useMemo(() => getMedicineById(id), [getMedicineById, id]);

  useEffect(() => {
    if (id) {
      markAsViewed(id);
    }
  }, [id, markAsViewed]);

  if (!medicine) {
    return (
      <Screen>
        <Text>Medicamento não encontrado.</Text>
      </Screen>
    );
  }

  const lowest = getLowestOffer(medicine);
  const offers = getSortedOffers(medicine);
  const isFavorite = favoriteIds.includes(medicine.id);

  const isWeb = Platform.OS === 'web';
  const isDesktop = isWeb && width >= 1100;
  const isTablet = isWeb && width >= 850 && width < 1100;

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
            ]}
          >
            <Ionicons name="image-outline" size={isDesktop ? 64 : 52} color={palette.text} />
          </View>

          <View style={styles.headerRow}>
            <View style={styles.infoBlock}>
              <Text style={[styles.name, isDesktop && styles.nameDesktop]}>{medicine.name}</Text>
              <Text style={[styles.price, isDesktop && styles.priceDesktop]}>
                ${lowest.price.toFixed(2)}
              </Text>
            </View>

            <Pressable
              style={styles.favoriteButton}
              onPress={() => toggleFavorite(medicine.id)}
            >
              <Ionicons
                name={isFavorite ? 'heart' : 'heart-outline'}
                size={28}
                color={isFavorite ? palette.danger : palette.text}
              />
            </Pressable>
          </View>

          <Text style={styles.sectionLabel}>Descrição</Text>
          <Text style={[styles.description, isDesktop && styles.descriptionDesktop]}>
            {medicine.description}
          </Text>

          <Pressable
            style={[styles.historyButton, isDesktop && styles.historyButtonDesktop]}
            onPress={() => router.push(`/history/${medicine.id}`)}
          >
            <Text style={styles.historyButtonText}>Ver histórico de preços</Text>
          </Pressable>
        </View>

        <View style={[styles.offersPanel, isDesktop && styles.offersPanelDesktop]}>
          <View style={styles.offersHeader}>
            <Text style={styles.offersTitle}>Outras farmácias disponíveis</Text>
            <Text style={styles.offersSubtitle}>{offers.length} ofertas encontradas</Text>
          </View>

          <View style={styles.lowestBox}>
            <Text style={styles.lowestLabel}>Menor preço</Text>
            <Text
              style={[
                styles.lowestPharmacy,
                { color: pharmacyColors[lowest.pharmacy] ?? palette.primary },
              ]}
            >
              {lowest.pharmacy}
            </Text>
            <Text style={styles.lowestPrice}>${lowest.price.toFixed(2)}</Text>
          </View>

          <View style={styles.offersList}>
            {offers.map((offer) => (
              <View key={offer.pharmacy} style={styles.offerRow}>
                <View style={styles.offerLeft}>
                  <View
                    style={[
                      styles.offerDot,
                      { backgroundColor: pharmacyColors[offer.pharmacy] ?? palette.primary },
                    ]}
                  />
                  <View>
                    <Text style={styles.offerName}>{medicine.name}</Text>
                    <Text
                      style={[
                        styles.offerPharmacy,
                        { color: pharmacyColors[offer.pharmacy] ?? palette.primary },
                      ]}
                    >
                      {offer.pharmacy}
                    </Text>
                  </View>
                </View>

                <Text style={styles.offerPrice}>${offer.price.toFixed(2)}</Text>
              </View>
            ))}
          </View>
        </View>
      </View>
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
  },
  imageCardTablet: {
    aspectRatio: 1.55,
  },
  imageCardDesktop: {
    height: 420,
    aspectRatio: undefined,
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
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    justifyContent: 'center',
    alignItems: 'center',
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
    fontSize: 28,
  },
  sectionLabel: {
    fontSize: 20,
    fontWeight: '700',
    color: palette.text,
    marginTop: spacing.xl,
    marginBottom: spacing.sm,
  },
  description: {
    color: palette.textSoft,
    fontSize: 15,
    lineHeight: 24,
    maxWidth: 760,
  },
  descriptionDesktop: {
    fontSize: 16,
    lineHeight: 28,
  },
  historyButton: {
    marginTop: spacing.xl,
    minHeight: 50,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  historyButtonDesktop: {
    maxWidth: 760,
  },
  historyButtonText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  offersPanel: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E4E4E4',
    padding: spacing.md,
  },
  offersPanelDesktop: {
    width: 360,
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: '#F7F7F7',
    borderWidth: 1,
    borderColor: '#E6E6E6',
  },
  offerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    flex: 1,
  },
  offerDot: {
    width: 12,
    height: 12,
    borderRadius: radius.pill,
  },
  offerName: {
    fontSize: 14,
    color: palette.text,
    marginBottom: 2,
  },
  offerPharmacy: {
    fontSize: 13,
    fontWeight: '600',
  },
  offerPrice: {
    fontSize: 18,
    fontWeight: '700',
    color: palette.text,
    marginLeft: spacing.sm,
  },
});