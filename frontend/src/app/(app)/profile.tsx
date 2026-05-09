import { router } from 'expo-router';
import React from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { Screen } from '../../components/Screen';
import { useAppContext } from '../../context/AppContext';
import { palette, radius, spacing } from '../../theme';

export default function ProfileScreen() {
  const { sessionMode, currentUserName, currentUserEmail, logout } = useAppContext();
  const isWeb = Platform.OS === 'web';

  const handleLogout = () => {
    logout();
    router.replace('/login');
  };

  return (
    <Screen>
      <View style={[styles.card, isWeb && styles.cardWeb]}>
        <Text style={[styles.title, isWeb && styles.titleWeb]}>Perfil</Text>

        <Text style={styles.label}>Modo atual</Text>
        <Text style={[styles.mode, isWeb && styles.modeWeb]}>
          {sessionMode === 'guest' ? 'Convidado' : 'Usuário autenticado'}
        </Text>

        {sessionMode === 'authenticated' ? (
          <>
            <Text style={styles.infoLabel}>Nome</Text>
            <Text style={styles.infoValue}>{currentUserName || 'Usuário Teste'}</Text>

            <Text style={styles.infoLabel}>Email</Text>
            <Text style={styles.infoValue}>{currentUserEmail || 'teste@precobao.com'}</Text>
          </>
        ) : (
          <Text style={styles.description}>
            Você está navegando como convidado. Para testar a área autenticada, use o
            usuário teste.
          </Text>
        )}

        <Pressable style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>Editar depois</Text>
        </Pressable>

        <Pressable style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>Sair</Text>
        </Pressable>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    backgroundColor: palette.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#E8E8E8',
    padding: spacing.lg,
  },
  cardWeb: {
    maxWidth: 1160,
    alignSelf: 'center',
    padding: 24,
  },
  title: {
    color: palette.primary,
    fontSize: 28,
    fontWeight: '700',
    marginBottom: spacing.lg,
  },
  titleWeb: {
    fontSize: 40,
  },
  label: {
    color: palette.textSoft,
    fontSize: 16,
    marginBottom: 6,
  },
  mode: {
    color: palette.text,
    fontSize: 28,
    fontWeight: '700',
    marginBottom: spacing.lg,
  },
  modeWeb: {
    fontSize: 36,
  },
  infoLabel: {
    color: palette.textSoft,
    fontSize: 15,
    marginTop: spacing.sm,
    marginBottom: 4,
  },
  infoValue: {
    color: palette.text,
    fontSize: 18,
    fontWeight: '600',
  },
  description: {
    color: palette.textSoft,
    fontSize: 16,
    lineHeight: 24,
    marginBottom: spacing.xl,
  },
  primaryButton: {
    minHeight: 50,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.xl,
    marginBottom: spacing.md,
  },
  primaryButtonText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  logoutButton: {
    minHeight: 50,
    borderRadius: radius.pill,
    borderWidth: 1.5,
    borderColor: '#E35D5D',
    backgroundColor: '#FFF5F5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoutButtonText: {
    color: '#D64545',
    fontSize: 16,
    fontWeight: '700',
  },
});