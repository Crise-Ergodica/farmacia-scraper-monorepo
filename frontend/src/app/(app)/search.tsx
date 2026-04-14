import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { MedicineCard } from '../../components/MedicineCard';
import { OfferRow } from '../../components/OfferRow';
import { Screen } from '../../components/Screen';
import { SearchBar } from '../../components/SearchBar';
import { useAppContext } from '../../context/AppContext';
import { palette, spacing } from '../../theme';

export default function SearchScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ q?: string }>();
  // Inicialização padrão vazia caso não haja query
  const [search, setSearch] = useState(typeof params.q === 'string' ? params.q : '');
  const { buildSearchRows, cheapestMedicines, markAsViewed } = useAppContext();

  useEffect(() => {
    if (typeof params.q === 'string') {
      setSearch(params.q || '');
    }
  }, [params.q]);

  const rows = useMemo(() => buildSearchRows(search), [buildSearchRows, search]);

  // CORREÇÃO: medicineId agora é estritamente do tipo number
  const openDetail = (medicineId: number) => {
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
            // CORREÇÃO: Chaves do banco de dados relacional
            key={`${row.medicineId}-${row.farmaciaId}-${index}`}
            medicineName={row.medicineNome}
            pharmacy={row.farmaciaId}
            price={row.preco}
            color={palette.primary} // Fallback seguro de cor
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
              onPress={() => openDetail(medicine.id)} // Passando o ID numérico corretamente
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
    fontSize: 20,
    fontWeight: '700',
    color: palette.text,
    marginBottom: spacing.md,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    rowGap: spacing.lg,
    columnGap: spacing.md,
  },
});