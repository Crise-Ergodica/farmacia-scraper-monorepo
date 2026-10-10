import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';

import { MedicineCard } from '../../components/MedicineCard';
import { OfferRow } from '../../components/OfferRow';
import { Screen } from '../../components/Screen';
import { SearchBar } from '../../components/SearchBar';
import { useCatalogContext } from '../../context/AppContext';
import { palette, radius, spacing } from '../../theme';
import { Medicamento } from '../../types/api';

type SearchRow = { medicine: Medicamento; medicineId: number; medicineName: string; pharmacyId: number; pharmacyName: string; price: number };

export default function SearchScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ q?: string }>();
  const { loadCatalogPage, cheapestMedicines, cheapestError, selectedFilters, markAsViewed } = useCatalogContext();
  const { width } = useWindowDimensions();
  const [search, setSearch] = useState(typeof params.q === 'string' ? params.q : '');
  const [query, setQuery] = useState(typeof params.q === 'string' ? params.q : '');
  const [items, setItems] = useState<Medicamento[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [reload, setReload] = useState(0);
  const limit = 20;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  useEffect(() => {
    if (typeof params.q === 'string') {
      setSearch(params.q);
      setQuery(params.q);
    }
  }, [params.q]);

  useEffect(() => {
    const timer = setTimeout(() => setQuery(search.trim()), 300);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => { setPage(1); }, [query, selectedFilters]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(false);
    loadCatalogPage({ query, offset: (page - 1) * limit, limit, filters: selectedFilters })
      .then((result) => {
        if (!active) return;
        setItems(result.items);
        setTotal(result.total);
      })
      .catch(() => { if (active) setError(true); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [loadCatalogPage, query, page, selectedFilters, reload]);

  const rows = useMemo<SearchRow[]>(() => items
    .flatMap((medicine) => medicine.ofertas
      .filter((offer) => offer.disponivel)
      .map((offer) => ({
        medicine,
        medicineId: medicine.id,
        medicineName: medicine.nome,
        pharmacyId: offer.farmacia_id,
        pharmacyName: offer.farmacia_nome || offer.farmacia?.nome_fantasia || `Farmácia ${offer.farmacia_id}`,
        price: Number(offer.preco),
      })))
    .sort((a, b) => a.price - b.price), [items]);

  const openDetail = (id: number) => {
    markAsViewed(id);
    router.push(`/medicine/${id}`);
  };

  return (
    <Screen contentStyle={styles.screen}>
      <Text style={styles.eyebrow}>BUSCA DE MEDICAMENTOS</Text>
      <Text style={styles.title}>Compare ofertas</Text>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onSubmit={() => { setQuery(search.trim()); router.setParams({ q: search.trim() }); }}
        onFilter={() => router.push('/filters')}
        filterCount={selectedFilters.length}
      />
      <View style={styles.resultHeader}>
        <Text style={styles.resultCount}>{total.toLocaleString('pt-BR')} resultados</Text>
        {loading && <ActivityIndicator size="small" color={palette.primary} />}
      </View>
      {error ? (
        <View style={styles.messageBox}>
          <Text style={styles.message}>Não foi possível realizar a busca.</Text>
          <Pressable onPress={() => setReload((value) => value + 1)} accessibilityRole="button"><Text style={styles.retry}>Tentar novamente</Text></Pressable>
        </View>
      ) : !loading && rows.length === 0 ? (
        <View style={styles.messageBox}><Text style={styles.message}>Nenhuma oferta corresponde à busca e aos filtros.</Text></View>
      ) : (
        <View style={styles.rows}>
          {rows.map((row) => (
            <OfferRow key={`${row.medicineId}-${row.pharmacyId}`} medicine={row.medicine} medicineName={row.medicineName} pharmacy={row.pharmacyName} price={row.price} color={palette.primary} onPress={() => openDetail(row.medicineId)} />
          ))}
        </View>
      )}
      {totalPages > 1 && (
        <View style={styles.pagination}>
          <Pressable disabled={page <= 1 || loading} onPress={() => setPage((value) => Math.max(1, value - 1))} accessibilityRole="button"><Text style={styles.pageAction}>Anterior</Text></Pressable>
          <Text style={styles.pageInfo}>Página {page} de {totalPages}</Text>
          <Pressable disabled={page >= totalPages || loading} onPress={() => setPage((value) => Math.min(totalPages, value + 1))} accessibilityRole="button"><Text style={styles.pageAction}>Próxima</Text></Pressable>
        </View>
      )}
      <View style={styles.bottomSection}>
        <Text style={styles.sectionTitle}>Menores preços disponíveis</Text>
        {cheapestError ? <Text style={styles.message}>Não foi possível carregar os menores preços.</Text> : (
          <View style={[styles.grid, width <= 480 && styles.gridMobileList]}>
            {cheapestMedicines.map((medicine) => <MedicineCard key={medicine.id} medicine={medicine} onPress={() => openDetail(medicine.id)} compact />)}
          </View>
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: { paddingTop: spacing.lg },
  eyebrow: { color: palette.primaryDark, fontSize: 11, fontWeight: '800', letterSpacing: 1 },
  title: { color: palette.text, fontSize: 25, fontWeight: '800', marginVertical: spacing.sm },
  resultHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.md },
  resultCount: { color: palette.textSoft, fontSize: 13 },
  rows: { marginTop: spacing.sm },
  messageBox: { marginTop: spacing.md, padding: spacing.lg, borderRadius: radius.md, backgroundColor: palette.surface },
  message: { color: palette.textSoft, fontSize: 14 },
  retry: { color: palette.primaryDark, fontWeight: '700', marginTop: spacing.sm },
  pagination: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: spacing.lg, marginTop: spacing.md },
  pageAction: { color: palette.primaryDark, fontWeight: '700', padding: spacing.sm },
  pageInfo: { color: palette.textSoft, fontSize: 13 },
  bottomSection: { marginTop: spacing.xl },
  sectionTitle: { color: palette.text, fontSize: 19, fontWeight: '700', marginBottom: spacing.md },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  gridMobileList: { flexDirection: 'column', flexWrap: 'nowrap' },
});
