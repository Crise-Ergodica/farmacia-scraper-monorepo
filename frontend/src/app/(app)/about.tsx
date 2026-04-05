import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Screen } from '../../components/Screen';
import { palette, radius, spacing } from '../../theme';

export default function AboutScreen() {
  return (
    <Screen>
      <Text style={styles.title}>Saiba mais</Text>
      <View style={styles.card}>
        <Text style={styles.paragraph}>
          Esse frontend foi estruturado para comparar medicamentos, listar farmácias disponíveis e mostrar histórico de preço.
        </Text>
        <Text style={styles.paragraph}>
          Quando o backend estiver pronto, basta trocar os dados mockados por chamadas de API no mesmo fluxo de navegação.
        </Text>
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
  paragraph: {
    color: palette.textSoft,
    lineHeight: 22,
  },
});
