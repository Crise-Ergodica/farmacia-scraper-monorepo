import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { HistoryChart } from '../../../components/HistoryChart';
import { OfferRow } from '../../../components/OfferRow';
import { Screen } from '../../../components/Screen';
import { SearchBar } from '../../../components/SearchBar';
import { useAppContext } from '../../../context/AppContext';
import { getSortedOffers, pharmacyColors } from '../../../data/mockData';
import { palette, spacing } from '../../../theme';

export default function HistoryScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { getMedicineById } = useAppContext();
  const [search, setSearch] = useState('Farma+');

  const medicine = useMemo(() => getMedicineById(id), [getMedicineById, id]);

  if (!medicine) {
    return (
      <Screen>
        <Text>Histórico não encontrado.</Text>
      </Screen>
    );
  }

  const offers = getSortedOffers(medicine);

  return (
    <Screen>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onSubmit={() => router.push({ pathname: '/search', params: { q: search } })}
        onBack={() => router.back()}
      />

      <View style={styles.pricesGrid}>
        {offers.map((offer) => (
          <View key={offer.pharmacy} style={styles.priceCell}>
            <Text style={styles.medicineName}>{medicine.name}</Text>
            <Text style={[styles.pharmacyName, { color: pharmacyColors[offer.pharmacy] ?? palette.primary }]}>
              {offer.pharmacy}
            </Text>
            <Text style={styles.price}>${offer.price.toFixed(2)}</Text>
          </View>
        ))}
      </View>

      <Text style={styles.sectionTitle}>Histórico de preços</Text>
      <HistoryChart
        series={offers.map((offer) => ({
          pharmacy: offer.pharmacy,
          history: offer.history,
        }))}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  pricesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginTop: spacing.lg,
    rowGap: spacing.lg,
  },
  priceCell: {
    width: '31%',
  },
  medicineName: {
    fontSize: 12,
    color: palette.text,
    marginBottom: 2,
  },
  pharmacyName: {
    fontSize: 10,
    marginBottom: 4,
  },
  price: {
    fontSize: 14,
    fontWeight: '700',
    color: palette.text,
  },
  sectionTitle: {
    marginTop: spacing.xl,
    fontSize: 26,
    color: palette.text,
    fontWeight: '500',
  },
});
