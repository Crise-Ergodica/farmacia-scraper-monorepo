import { Ionicons } from '@expo/vector-icons';
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

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [feedback, setFeedback] = useState<{ type: 'error' | 'success' | 'info'; text: string } | null>(null);

  const isWeb = Platform.OS === 'web';

  const validate = () => {
    if (!name.trim() || !email.trim() || !password.trim() || !confirmPassword.trim()) {
      return 'Preencha todos os campos.';
    }

    if (name.trim().length < 3) {
      return 'O nome precisa ter pelo menos 3 caracteres.';
    }

    if (!email.includes('@')) {
      return 'Digite um email válido.';
    }

    if (password.length < 6) {
      return 'A senha precisa ter no mínimo 6 caracteres.';
    }

    if (password !== confirmPassword) {
      return 'As senhas não coincidem.';
    }

    return null;
  };

  const handleRegister = async () => {
    setFeedback(null);

    const validationError = validate();

    if (validationError) {
      setFeedback({
        type: 'error',
        text: validationError,
      });
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

    setFeedback({
      type: result.ok ? 'info' : 'error',
      text: result.message,
    });
  };

  return (
    <Screen hideBottomNav scroll={false} contentStyle={styles.screenContent}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <View style={[styles.box, isWeb && styles.boxWeb]}>
          <View style={styles.header}>
            <Text style={styles.title}>Cadastro</Text>
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

            <View style={styles.passwordWrapper}>
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder="Senha"
                placeholderTextColor={palette.primary}
                style={[styles.passwordInput, isWeb && styles.inputWeb]}
                autoCapitalize="none"
                secureTextEntry={!showPassword}
              />
              <Pressable onPress={() => setShowPassword((current) => !current)}>
                <Ionicons
                  name={showPassword ? 'eye-outline' : 'eye-off-outline'}
                  size={22}
                  color={palette.primary}
                />
              </Pressable>
            </View>

            <View style={styles.passwordWrapper}>
              <TextInput
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                placeholder="Confirmar senha"
                placeholderTextColor={palette.primary}
                style={[styles.passwordInput, isWeb && styles.inputWeb]}
                autoCapitalize="none"
                secureTextEntry={!showConfirmPassword}
              />
              <Pressable onPress={() => setShowConfirmPassword((current) => !current)}>
                <Ionicons
                  name={showConfirmPassword ? 'eye-outline' : 'eye-off-outline'}
                  size={22}
                  color={palette.primary}
                />
              </Pressable>
            </View>
          </View>

          {feedback ? (
            <View
              style={[
                styles.feedbackBox,
                feedback.type === 'error' ? styles.feedbackError : styles.feedbackInfo,
              ]}
            >
              <Text style={styles.feedbackText}>{feedback.text}</Text>
            </View>
          ) : null}

          <Pressable
            style={[styles.button, isSubmitting && styles.buttonDisabled]}
            onPress={handleRegister}
            disabled={isSubmitting}
          >
            <Text style={styles.buttonText}>
              {isSubmitting ? 'Enviando...' : 'Cadastrar'}
            </Text>
          </Pressable>

          <Pressable onPress={() => router.replace('/login')}>
            <Text style={styles.secondaryLink}>Voltar para login</Text>
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
    maxWidth: 460,
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
    outlineStyle: 'none',
  },
  passwordWrapper: {
    height: 52,
    borderWidth: 1,
    borderColor: palette.primary,
    borderRadius: radius.sm,
    backgroundColor: palette.surface,
    paddingHorizontal: spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
  },
  passwordInput: {
    flex: 1,
    color: palette.text,
    fontSize: 16,
  },
  feedbackBox: {
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    marginTop: spacing.lg,
  },
  feedbackError: {
    backgroundColor: '#FFF1F1',
    borderWidth: 1,
    borderColor: '#F0B7B7',
  },
  feedbackInfo: {
    backgroundColor: '#EEF6FF',
    borderWidth: 1,
    borderColor: '#CFE4FF',
  },
  feedbackText: {
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