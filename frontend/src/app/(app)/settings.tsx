import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Screen } from '../../components/Screen';
import { palette, radius, spacing } from '../../theme';

export default function SettingsScreen() {
  return (
    <Screen>
      <Text style={styles.title}>Settings</Text>
      <View style={styles.card}>
        <Text style={styles.item}>Notificações de menor preço</Text>
        <Text style={styles.item}>Tema claro</Text>
        <Text style={styles.item}>Idioma</Text>
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
    gap: spacing.md,
  },
  item: {
    color: palette.text,
    fontSize: 16,
  },
});
