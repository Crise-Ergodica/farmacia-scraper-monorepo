import { useRouter } from 'expo-router';
import React, { useEffect, useMemo, useState } from 'react';

import {
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { FilterChip } from '../../components/FilterChip';
import { Screen } from '../../components/Screen';
import { SearchBar } from '../../components/SearchBar';
import {
  FilterKind,
  FilterOption,
  useAppContext,
} from '../../context/AppContext';
import { palette, radius, spacing } from '../../theme';

const SECTION_LABELS: Record<FilterKind, string> = {
  receita: 'Tipo de venda',
  categoria: 'Categorias',
  laboratorio: 'Laboratórios',
  principio_ativo: 'Princípios ativos',
};

const SECTION_ORDER: FilterKind[] = [
  'receita',
  'categoria',
  'laboratorio',
  'principio_ativo',
];

function normalizeText(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

export default function FiltersScreen() {
  const router = useRouter();

  const { selectedFilters, filterOptions, applyFilters, clearFilters } =
    useAppContext();

  const isWeb = Platform.OS === 'web';

  const [search, setSearch] = useState('');
  const [temporaryFilters, setTemporaryFilters] =
    useState<FilterOption[]>(selectedFilters);

  useEffect(() => {
    setTemporaryFilters(selectedFilters);
  }, [selectedFilters]);

  const goBackOrHome = () => {
    if (router.canGoBack()) {
      router.back();
      return;
    }

    router.replace('/home');
  };

  const filteredOptions = useMemo(() => {
    const normalizedSearch = normalizeText(search);

    if (!normalizedSearch) {
      return filterOptions;
    }

    return filterOptions.filter((option) =>
      normalizeText(option.label).includes(normalizedSearch)
    );
  }, [filterOptions, search]);

  const groupedOptions = useMemo(() => {
    const groups: Record<FilterKind, FilterOption[]> = {
      receita: [],
      categoria: [],
      laboratorio: [],
      principio_ativo: [],
    };

    for (const option of filteredOptions) {
      groups[option.type].push(option);
    }

    return groups;
  }, [filteredOptions]);

  const isSelected = (option: FilterOption) =>
    temporaryFilters.some((item) => item.id === option.id);

  const toggleTemporaryFilter = (option: FilterOption) => {
    setTemporaryFilters((current) =>
      current.some((item) => item.id === option.id)
        ? current.filter((item) => item.id !== option.id)
        : [...current, option]
    );
  };

  const handleApply = () => {
    applyFilters(temporaryFilters);
    goBackOrHome();
  };

  const handleClear = () => {
    setTemporaryFilters([]);
    clearFilters();
  };

  return (
    <Screen>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onBack={goBackOrHome}
        onFilter={() => undefined}
        placeholder="Buscar filtro"
      />

      <View style={styles.summaryBox}>
        <Text style={styles.summaryTitle}>Filtros</Text>

        <Text style={styles.summaryText}>
          {temporaryFilters.length > 0
            ? `${temporaryFilters.length} filtro(s) selecionado(s)`
            : 'Selecione uma opção enviada pelo backend'}
        </Text>
      </View>

      <View style={styles.list}>
        {SECTION_ORDER.map((section) => {
          const options = groupedOptions[section];

          if (!options.length) {
            return null;
          }

          return (
            <View key={section} style={styles.section}>
              <Text style={styles.sectionTitle}>{SECTION_LABELS[section]}</Text>

              <View style={[styles.chipGrid, isWeb && styles.chipGridWeb]}>
                {options.map((option) => (
                  <FilterChip
                    key={option.id}
                    label={option.label}
                    active={isSelected(option)}
                    onPress={() => toggleTemporaryFilter(option)}
                  />
                ))}
              </View>
            </View>
          );
        })}
      </View>

      <View style={styles.actionsRow}>
        <Pressable
          style={(state: { pressed: boolean; hovered?: boolean }) => [
            styles.clearButton,
            isWeb && state.hovered && styles.clearButtonHovered,
            state.pressed && styles.buttonPressed,
          ]}
          onPress={handleClear}
        >
          <Text style={styles.clearText}>Limpar</Text>
        </Pressable>

        <Pressable
          style={(state: { pressed: boolean; hovered?: boolean }) => [
            styles.applyButton,
            isWeb && state.hovered && styles.applyButtonHovered,
            state.pressed && styles.buttonPressed,
          ]}
          onPress={handleApply}
        >
          <Text style={styles.applyText}>Aplicar</Text>
        </Pressable>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  summaryBox: {
    marginTop: spacing.lg,
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: radius.xl,
    padding: spacing.lg,
  },

  summaryTitle: {
    color: palette.text,
    fontSize: 24,
    fontWeight: '900',
  },

  summaryText: {
    marginTop: 4,
    color: palette.textSoft,
    fontSize: 14,
    lineHeight: 20,
  },

  list: {
    marginTop: spacing.lg,
    gap: spacing.lg,
  },

  section: {
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: radius.xl,
    padding: spacing.lg,
  },

  sectionTitle: {
    color: palette.text,
    fontSize: 17,
    fontWeight: '900',
    marginBottom: spacing.md,
  },

  chipGrid: {
    gap: spacing.sm,
  },

  chipGridWeb: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'flex-start',
  },

  actionsRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.xl,
  },

  clearButton: {
    flex: 1,
    minHeight: 50,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: palette.primary,
    backgroundColor: palette.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },

  clearButtonHovered: {
    backgroundColor: palette.primarySoft,
  },

  clearText: {
    color: palette.primary,
    fontSize: 16,
    fontWeight: '900',
  },

  applyButton: {
    flex: 1,
    minHeight: 50,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  applyButtonHovered: {
    backgroundColor: palette.primaryDark,
  },

  applyText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '900',
  },

  buttonPressed: {
    opacity: 0.86,
    transform: [
      {
        scale: 0.98,
      },
    ],
  },
});