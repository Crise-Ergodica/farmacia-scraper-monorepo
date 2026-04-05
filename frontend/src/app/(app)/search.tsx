import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { MedicineCard } from '../../components/MedicineCard';
import { OfferRow } from '../../components/OfferRow';
import { Screen } from '../../components/Screen';
import { SearchBar } from '../../components/SearchBar';
import { useAppContext } from '../../context/AppContext';
import { pharmacyColors } from '../../data/mockData';
import { palette, spacing } from '../../theme';

export default function SearchScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ q?: string }>();
  const [search, setSearch] = useState(typeof params.q === 'string' ? params.q : 'Loratadina');
  const { buildSearchRows, cheapestMedicines, markAsViewed } = useAppContext();

  useEffect(() => {
    if (typeof params.q === 'string') {
      setSearch(params.q || 'Loratadina');
    }
  }, [params.q]);

  const rows = useMemo(() => buildSearchRows(search), [buildSearchRows, search]);

  const openDetail = (medicineId: string) => {
    markAsViewed(medicineId);
    router.push(`/medicine/${medicineId}`);
  };

  return (
    <Screen>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onSubmit={() => router.setParams({ q: search })}
        onFilter={() => router.push('/filters')}
      />

      <View style={styles.resultsWrapper}>
        {rows.map((row, index) => (
          <OfferRow
            key={`${row.medicineId}-${row.pharmacy}-${index}`}
            medicineName={row.medicineName}
            pharmacy={row.pharmacy}
            price={row.price}
            color={pharmacyColors[row.pharmacy]}
            onPress={() => openDetail(row.medicineId)}
          />
        ))}
      </View>

      <View style={styles.bottomSection}>
        <Text style={styles.bottomTitle}>Mais Baratos</Text>
        <View style={styles.grid}>
          {cheapestMedicines.slice(0, 3).map((medicine) => (
            <MedicineCard
              key={medicine.id}
              medicine={medicine}
              onPress={() => openDetail(medicine.id)}
              compact
            />
          ))}
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  resultsWrapper: {
    marginTop: spacing.md,
  },
  bottomSection: {
    marginTop: spacing.xl,
  },
  bottomTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: palette.textSoft,
    marginBottom: spacing.md,
  },
  grid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
});
