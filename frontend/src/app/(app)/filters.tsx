import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { FilterChip } from '../../components/FilterChip';
import { Screen } from '../../components/Screen';
import { SearchBar } from '../../components/SearchBar';
import { useAppContext } from '../../context/AppContext';
import { palette, radius, spacing } from '../../theme';

export default function FiltersScreen() {
  const router = useRouter();
  const { selectedFilters, filterOptions, toggleFilter } = useAppContext();
  const [search, setSearch] = useState('Farma+');

  return (
    <Screen>
      <SearchBar
        value={search}
        onChangeText={setSearch}
        onBack={() => router.back()}
        onFilter={() => undefined}
      />

      <View style={styles.list}>
        {filterOptions.map((option) => (
          <FilterChip
            key={option}
            label={option}
            active={selectedFilters.includes(option)}
            onPress={() => toggleFilter(option)}
          />
        ))}
      </View>

      <Pressable style={styles.applyButton} onPress={() => router.back()}>
        <Text style={styles.applyText}>Aplicar</Text>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  list: {
    marginTop: spacing.lg,
  },
  applyButton: {
    minHeight: 46,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.xl,
  },
  applyText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '700',
  },
});
