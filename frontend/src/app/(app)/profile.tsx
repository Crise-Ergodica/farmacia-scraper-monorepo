import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Screen } from '../../components/Screen';
import { useAppContext } from '../../context/AppContext';
import { palette, radius, spacing } from '../../theme';

export default function ProfileScreen() {
  const { sessionMode } = useAppContext();

  return (
    <Screen>
      <View style={styles.card}>
        <Text style={styles.title}>Perfil</Text>
        <Text style={styles.label}>Modo atual</Text>
        <Text style={styles.value}>{sessionMode === 'guest' ? 'Convidado' : 'Logado'}</Text>

        <Text style={styles.description}>
          Essa tela já está pronta para receber seus dados reais quando o backend e a autenticação forem definidos.
        </Text>

        <Pressable style={styles.button}>
          <Text style={styles.buttonText}>Editar depois</Text>
        </Pressable>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: {
    marginTop: spacing.lg,
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  title: {
    fontSize: 28,
    color: palette.primary,
    fontWeight: '700',
    marginBottom: spacing.lg,
  },
  label: {
    fontSize: 14,
    color: palette.textSoft,
  },
  value: {
    fontSize: 20,
    color: palette.text,
    fontWeight: '700',
    marginTop: spacing.xs,
    marginBottom: spacing.lg,
  },
  description: {
    color: palette.textSoft,
    lineHeight: 22,
  },
  button: {
    minHeight: 44,
    marginTop: spacing.xl,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    color: palette.surface,
    fontWeight: '700',
  },
});
