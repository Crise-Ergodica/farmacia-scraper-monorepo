import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Screen } from '../../../components/Screen';
import { SearchBar } from '../../../components/SearchBar';
import { useAppContext } from '../../../context/AppContext';
import { getLowestOffer, getSortedOffers, pharmacyColors } from '../../../data/mockData';
import { palette, radius, spacing } from '../../../theme';

export default function MedicineDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { getMedicineById, favoriteIds, toggleFavorite, markAsViewed } = useAppContext();
  const [search, setSearch] = useState('Farma+');

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

  return (
    <Screen>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onSubmit={() => router.push({ pathname: '/search', params: { q: search } })}
        onBack={() => router.back()}
      />

      <View style={styles.imageCard}>
        <Ionicons name="image-outline" size={68} color={palette.text} />
      </View>

      <View style={styles.headerRow}>
        <View style={styles.infoBlock}>
          <Text style={styles.name}>{medicine.name}</Text>
          <Text style={styles.price}>${lowest.price.toFixed(2)}</Text>
        </View>

        <Pressable onPress={() => toggleFavorite(medicine.id)}>
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={28}
            color={isFavorite ? palette.danger : palette.text}
          />
        </Pressable>
      </View>

      <View style={styles.offersRow}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.offersList}>
            {offers.map((offer) => (
              <View key={offer.pharmacy} style={styles.offerCard}>
                <Ionicons name="image-outline" size={18} color={palette.textSoft} />
                <Text style={[styles.offerPharmacy, { color: pharmacyColors[offer.pharmacy] ?? palette.primary }]}>
                  {offer.pharmacy}
                </Text>
                <Text style={styles.offerPrice}>${offer.price.toFixed(2)}</Text>
              </View>
            ))}
          </View>
        </ScrollView>

        <Text style={styles.offerHint}>Outras farmácias disponíveis</Text>
      </View>

      <Text style={styles.sectionLabel}>Descrição</Text>
      <Text style={styles.description}>{medicine.description}</Text>

      <Pressable style={styles.historyButton} onPress={() => router.push(`/history/${medicine.id}`)}>
        <Text style={styles.historyButtonText}>Ver histórico de preços</Text>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  imageCard: {
    width: '100%',
    aspectRatio: 1.25,
    borderRadius: radius.lg,
    backgroundColor: '#ECECEC',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginTop: spacing.lg,
  },
  infoBlock: {
    flex: 1,
  },
  name: {
    fontSize: 36,
    color: palette.text,
    fontWeight: '500',
    marginBottom: spacing.xs,
  },
  price: {
    fontSize: 26,
    color: palette.text,
    fontWeight: '700',
  },
  offersRow: {
    marginTop: spacing.md,
    alignItems: 'flex-end',
  },
  offersList: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  offerCard: {
    width: 56,
    height: 56,
    borderRadius: radius.sm,
    backgroundColor: '#F2F2F2',
    borderWidth: 1,
    borderColor: '#D0D0D0',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 2,
  },
  offerPharmacy: {
    fontSize: 8,
    textAlign: 'center',
  },
  offerPrice: {
    fontSize: 8,
    fontWeight: '700',
  },
  offerHint: {
    color: palette.textSoft,
    fontSize: 11,
    textAlign: 'right',
    marginTop: spacing.xs,
  },
  sectionLabel: {
    fontSize: 18,
    fontWeight: '700',
    color: palette.text,
    marginTop: spacing.xl,
    marginBottom: spacing.sm,
  },
  description: {
    color: palette.textSoft,
    fontSize: 14,
    lineHeight: 22,
  },
  historyButton: {
    marginTop: spacing.xl,
    minHeight: 48,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  historyButtonText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '700',
  },
});
