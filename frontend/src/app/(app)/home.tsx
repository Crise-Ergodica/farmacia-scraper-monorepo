import { useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';

import {
  ActivityIndicator,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { MedicineCard } from '../../components/MedicineCard';
import { Screen } from '../../components/Screen';
import { SearchBar } from '../../components/SearchBar';
import { useAppContext } from '../../context/AppContext';
import { Medicamento } from '../../types/api';
import { palette, radius, spacing } from '../../theme';

const PHARMACIES = [
  { id: 1, name: 'Farmácia Indiana' },
  { id: 2, name: 'Drogaria Araújo' },
] as const;

export default function HomeScreen() {
  const router = useRouter();

  const isWeb = Platform.OS === 'web';

  const {
    isLoading,
    markAsViewed,
    searchMedicines,
    selectedFilters,
  } = useAppContext();

  const [search, setSearch] = useState('');

  const [pageByPharmacy, setPageByPharmacy] = useState<Record<number, number>>({
    1: 1,
    2: 1,
  });

  const itemsPerPage = isWeb ? 8 : 4;

  useEffect(() => {
    setPageByPharmacy({
      1: 1,
      2: 1,
    });
  }, [search, selectedFilters]);

  const medicinesByPharmacy = useMemo(() => {
    const baseList = searchMedicines(search);

    const result: Record<number, Medicamento[]> = {};

    for (const pharmacy of PHARMACIES) {
      result[pharmacy.id] = baseList
        .filter((medicine) =>
          (medicine.ofertas || []).some(
            (offer) => offer.farmacia_id === pharmacy.id
          )
        )
        .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
    }

    return result;
  }, [search, searchMedicines]);

  const totalResults = useMemo(() => {
    return Object.values(medicinesByPharmacy).reduce(
      (total, medicines) => total + medicines.length,
      0
    );
  }, [medicinesByPharmacy]);

  const openDetail = (medicineId: number) => {
    markAsViewed(medicineId);
    router.push(`/medicine/${medicineId}`);
  };

  const goToPage = (pharmacyId: number, page: number, totalPages: number) => {
    const safePage = Math.max(1, Math.min(page, totalPages));

    setPageByPharmacy((current) => ({
      ...current,
      [pharmacyId]: safePage,
    }));
  };

  const renderPharmacySection = (pharmacyId: number, pharmacyName: string) => {
    const pharmacyMedicines = medicinesByPharmacy[pharmacyId] || [];

    const totalPages = Math.max(
      1,
      Math.ceil(pharmacyMedicines.length / itemsPerPage)
    );

    const currentPage = Math.min(pageByPharmacy[pharmacyId] || 1, totalPages);

    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;

    const paginatedItems = pharmacyMedicines.slice(start, end);

    return (
      <View key={pharmacyId} style={styles.section}>
        <View style={styles.sectionHeader}>
          <View>
            <Text style={[styles.title, isWeb && styles.titleWeb]}>
              {pharmacyName}
            </Text>

            <Text style={styles.countText}>
              {pharmacyMedicines.length} medicamento(s) encontrado(s)
            </Text>
          </View>
        </View>

        {pharmacyMedicines.length === 0 ? (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyText}>
              Nenhum medicamento encontrado nessa farmácia.
            </Text>
          </View>
        ) : (
          <>
            <View style={[styles.grid, isWeb && styles.gridWeb]}>
              {paginatedItems.map((medicine) => (
                <MedicineCard
                  key={`${pharmacyId}-${medicine.id}`}
                  medicine={medicine}
                  onPress={() => openDetail(medicine.id)}
                  compact
                />
              ))}
            </View>

            {totalPages > 1 ? (
              <View style={styles.pagination}>
                <Pressable
                  style={({ pressed, hovered }) => [
                    styles.pageButton,
                    isWeb && hovered && styles.pageButtonHovered,
                    pressed && styles.pageButtonPressed,
                    currentPage === 1 && styles.pageButtonDisabled,
                  ]}
                  disabled={currentPage === 1}
                  onPress={() =>
                    goToPage(pharmacyId, currentPage - 1, totalPages)
                  }
                >
                  <Text
                    style={[
                      styles.pageButtonText,
                      currentPage === 1 && styles.pageButtonTextDisabled,
                    ]}
                  >
                    Anterior
                  </Text>
                </Pressable>

                <Text style={styles.pageInfo}>
                  Página {currentPage} de {totalPages}
                </Text>

                <Pressable
                  style={({ pressed, hovered }) => [
                    styles.pageButton,
                    isWeb && hovered && styles.pageButtonHovered,
                    pressed && styles.pageButtonPressed,
                    currentPage === totalPages && styles.pageButtonDisabled,
                  ]}
                  disabled={currentPage === totalPages}
                  onPress={() =>
                    goToPage(pharmacyId, currentPage + 1, totalPages)
                  }
                >
                  <Text
                    style={[
                      styles.pageButtonText,
                      currentPage === totalPages &&
                        styles.pageButtonTextDisabled,
                    ]}
                  >
                    Próxima
                  </Text>
                </Pressable>
              </View>
            ) : null}
          </>
        )}
      </View>
    );
  };

  if (isLoading) {
    return (
      <Screen contentStyle={styles.loadingContainer}>
        <ActivityIndicator size="large" color={palette.primary} />

        <Text style={styles.loadingText}>Carregando medicamentos...</Text>
      </Screen>
    );
  }

  return (
    <Screen>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onSubmit={() => {}}
        onFilter={() => router.push('/filters')}
        placeholder="Preço Bão"
      />

      {totalResults === 0 ? (
        <View style={styles.noResultsBox}>
          <Text style={styles.noResultsTitle}>
            Nenhum remédio foi encontrado
          </Text>

          <Text style={styles.noResultsText}>
            Tente alterar a busca ou remover os filtros selecionados.
          </Text>
        </View>
      ) : (
        PHARMACIES.map((pharmacy) =>
          renderPharmacySection(pharmacy.id, pharmacy.name)
        )
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: {
    marginTop: spacing.xl,
  },

  sectionHeader: {
    marginBottom: spacing.md,
  },

  title: {
    fontSize: 28,
    color: palette.primary,
    fontWeight: '700',
  },

  titleWeb: {
    fontSize: 34,
  },

  countText: {
    marginTop: 6,
    fontSize: 14,
    color: palette.textSoft,
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

  emptyBox: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E6E6E6',
    padding: spacing.lg,
  },

  emptyText: {
    fontSize: 15,
    color: palette.textSoft,
  },

  noResultsBox: {
    marginTop: spacing.xl,
    backgroundColor: palette.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.xl,
    alignItems: 'center',
  },

  noResultsTitle: {
    color: palette.text,
    fontSize: 22,
    fontWeight: '900',
    textAlign: 'center',
  },

  noResultsText: {
    marginTop: spacing.sm,
    color: palette.textSoft,
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
  },

  pagination: {
    marginTop: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
  },

  pageButton: {
    minWidth: 100,
    height: 42,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  pageButtonHovered: {
    backgroundColor: palette.primaryDark,
    transform: [
      {
        translateY: -2,
      },
    ],
  },

  pageButtonPressed: {
    opacity: 0.86,
    transform: [
      {
        scale: 0.98,
      },
    ],
  },

  pageButtonDisabled: {
    backgroundColor: '#D7D7D7',
  },

  pageButtonText: {
    color: palette.surface,
    fontWeight: '700',
    fontSize: 14,
  },

  pageButtonTextDisabled: {
    color: '#7C7C7C',
  },

  pageInfo: {
    fontSize: 14,
    color: palette.text,
    fontWeight: '600',
  },

  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
    paddingTop: spacing.xl * 2,
  },

  loadingText: {
    marginTop: spacing.md,
    color: palette.textSoft,
    fontSize: 16,
  },
});