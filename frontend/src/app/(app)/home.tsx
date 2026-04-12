import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { Platform, StyleSheet, Text, useWindowDimensions, View } from 'react-native';

import { MedicineCard } from '../../components/MedicineCard';
import { Screen } from '../../components/Screen';
import { SearchBar } from '../../components/SearchBar';
import { useAppContext } from '../../context/AppContext';
import { palette, spacing } from '../../theme';

export default function HomeScreen() {
  const router = useRouter();
  const { recentMedicines, cheapestMedicines, markAsViewed } = useAppContext();
  const [search, setSearch] = useState('');
  const { width } = useWindowDimensions();
  const isWeb = Platform.OS === 'web';

  const recentLimit = isWeb ? (width >= 1200 ? 5 : 4) : 3;
  const cheapestLimit = isWeb ? (width >= 1200 ? 10 : 8) : 6;

  const goToSearch = () => {
    router.push({ pathname: '/search', params: { q: search } });
  };

  const goToDetail = (id: string) => {
    markAsViewed(id);
    router.push(`/medicine/${id}`);
  };

  return (
    <Screen>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onSubmit={goToSearch}
        onFilter={() => router.push('/filters')}
      />

      <View style={styles.section}>
        <Text style={[styles.title, isWeb && styles.titleWeb]}>Vistos Recentemente</Text>

        <View style={[styles.grid, isWeb && styles.gridWeb]}>
          {recentMedicines.slice(0, recentLimit).map((medicine) => (
            <MedicineCard
              key={medicine.id}
              medicine={medicine}
              onPress={() => goToDetail(medicine.id)}
              compact
            />
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={[styles.title, isWeb && styles.titleWeb]}>Mais Baratos</Text>

        <View style={[styles.grid, isWeb && styles.gridWeb]}>
          {cheapestMedicines.slice(0, cheapestLimit).map((medicine) => (
            <MedicineCard
              key={medicine.id}
              medicine={medicine}
              onPress={() => goToDetail(medicine.id)}
              compact
            />
          ))}
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: {
    marginTop: spacing.xl,
  },
  title: {
    color: palette.text,
    fontSize: 20,
    fontWeight: '700',
    marginBottom: spacing.md,
  },
  titleWeb: {
    fontSize: 32,
    marginBottom: 24,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    rowGap: spacing.lg,
    columnGap: spacing.md,
  },
  gridWeb: {
    rowGap: 28,
    columnGap: 24,
  },
});