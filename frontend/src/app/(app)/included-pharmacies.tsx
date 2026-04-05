import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Screen } from '../../components/Screen';
import { palette, radius, spacing } from '../../theme';

const pharmacies = ['Farmácia 1', 'Farmácia 2', 'Farmácia 3', 'Farmácia 4', 'Farmácia 5', 'Farmácia 6'];

export default function IncludedPharmaciesScreen() {
  return (
    <Screen>
      <Text style={styles.title}>Farmácias inclusas</Text>

      <View style={styles.card}>
        {pharmacies.map((pharmacy) => (
          <View key={pharmacy} style={styles.row}>
            <Text style={styles.name}>{pharmacy}</Text>
            <Text style={styles.status}>Ativa</Text>
          </View>
        ))}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: {
    fontSize: 28,
    color: palette.primary,
    fontWeight: '700',
    marginTop: spacing.md,
    marginBottom: spacing.lg,
  },
  card: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#ECECEC',
  },
  name: {
    color: palette.text,
    fontSize: 16,
  },
  status: {
    color: palette.success,
    fontWeight: '700',
  },
});
