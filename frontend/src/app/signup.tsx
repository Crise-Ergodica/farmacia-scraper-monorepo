import { router } from 'expo-router';
import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Screen } from '../components/Screen';
import { useAppContext } from '../context/AppContext';
import { palette, radius, spacing } from '../theme';

export default function SignupScreen() {
  const { registerUser } = useAppContext();
  const isWeb = Platform.OS === 'web';

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSignup = async () => {
    setMessage('');

    if (!name.trim() || !email.trim() || !password.trim() || !confirmPassword.trim()) {
      setMessage('Preencha todos os campos.');
      return;
    }

    if (!email.includes('@')) {
      setMessage('Digite um email válido.');
      return;
    }

    if (password.length < 6) {
      setMessage('A senha precisa ter pelo menos 6 caracteres.');
      return;
    }

    if (password !== confirmPassword) {
      setMessage('As senhas não coincidem.');
      return;
    }

    setIsSubmitting(true);

    const result = await registerUser({
      name,
      email,
      password,
      confirmPassword,
    });

    setIsSubmitting(false);
    setMessage(result.message);
  };

  return (
    <Screen hideBottomNav scroll={false} contentStyle={styles.screenContent}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <View style={[styles.box, isWeb && styles.boxWeb]}>
          <View style={styles.header}>
            <Text style={styles.title}>Criar conta</Text>
            <Text style={styles.subtitle}>Preparado para autenticação real</Text>
          </View>

          <View style={styles.form}>
            <TextInput
              value={name}
              onChangeText={setName}
              placeholder="Nome"
              placeholderTextColor={palette.primary}
              style={[styles.input, isWeb && styles.inputWeb]}
            />

            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="Email"
              placeholderTextColor={palette.primary}
              style={[styles.input, isWeb && styles.inputWeb]}
              autoCapitalize="none"
              keyboardType="email-address"
            />

            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="Senha"
              placeholderTextColor={palette.primary}
              style={[styles.input, isWeb && styles.inputWeb]}
              secureTextEntry
            />

            <TextInput
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="Confirmar senha"
              placeholderTextColor={palette.primary}
              style={[styles.input, isWeb && styles.inputWeb]}
              secureTextEntry
            />
          </View>

          {message ? (
            <View style={styles.messageBox}>
              <Text style={styles.messageText}>{message}</Text>
            </View>
          ) : null}

          <Pressable
            style={[styles.button, isSubmitting && styles.buttonDisabled]}
            onPress={handleSignup}
            disabled={isSubmitting}
          >
            <Text style={styles.buttonText}>
              {isSubmitting ? 'Enviando...' : 'Cadastrar'}
            </Text>
          </Pressable>

          <Pressable onPress={() => router.replace('/login' as any)}>
            <Text style={styles.secondaryLink}>Ir para login</Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  screenContent: {
    flex: 1,
    justifyContent: 'center',
  },
  box: {
    width: '100%',
    maxWidth: 440,
    alignSelf: 'center',
  },
  boxWeb: {
    backgroundColor: palette.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#E7E7E7',
    padding: 28,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  title: {
    color: palette.primary,
    fontSize: 28,
    fontWeight: '700',
  },
  subtitle: {
    color: palette.textSoft,
    fontSize: 14,
    marginTop: 6,
  },
  form: {
    gap: spacing.md,
  },
  input: {
    height: 52,
    borderWidth: 1,
    borderColor: palette.primary,
    borderRadius: radius.sm,
    backgroundColor: palette.surface,
    paddingHorizontal: spacing.sm,
    color: palette.text,
    fontSize: 16,
  },
  inputWeb: {
    fontSize: 17,
    outlineWidth: 0,
    outlineColor: 'transparent',
    outlineStyle: 'none' as any,
  },
  messageBox: {
    marginTop: spacing.lg,
    backgroundColor: '#EEF6FF',
    borderWidth: 1,
    borderColor: '#CFE4FF',
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  messageText: {
    color: palette.text,
    fontSize: 14,
    lineHeight: 20,
  },
  button: {
    height: 52,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.xl,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryLink: {
    color: palette.primary,
    textAlign: 'center',
    marginTop: spacing.md,
    fontWeight: '700',
  },
});