import { useRouter } from 'expo-router';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { FavoriteCard } from '../../components/FavoriteCard';
import { Screen } from '../../components/Screen';
import { useAppContext } from '../../context/AppContext';
import { palette, spacing } from '../../theme';

export default function FavoritesScreen() {
  const router = useRouter();
  const { favoriteMedicines, toggleFavorite } = useAppContext();

  return (
    <Screen>
      <Text style={styles.title}>Favoritos</Text>

      <View style={styles.grid}>
        {favoriteMedicines.map((medicine) => (
          <FavoriteCard
            key={medicine.id}
            medicine={medicine}
            onOpen={() => router.push(`/medicine/${medicine.id}`)}
            onRemove={() => toggleFavorite(medicine.id)}
          />
        ))}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: {
    color: palette.primary,
    fontSize: 30,
    fontWeight: '500',
    textAlign: 'center',
    marginTop: spacing.md,
    marginBottom: spacing.xl,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
});
