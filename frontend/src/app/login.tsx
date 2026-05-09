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

export default function LoginScreen() {
  const { continueAsGuest, signIn } = useAppContext();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: 'error' | 'success';
    text: string;
  } | null>(null);

  const isWeb = Platform.OS === 'web';

  const handleLogin = async () => {
    setFeedback(null);

    if (!email.trim() && !password.trim()) {
      continueAsGuest();
      router.replace('/home');
      return;
    }

    if (!email.trim() || !password.trim()) {
      setFeedback({
        type: 'error',
        text: 'Preencha email e senha ou entre como convidado deixando os dois vazios.',
      });
      return;
    }

    setIsSubmitting(true);

    const result = await signIn(email, password);

    setIsSubmitting(false);

    if (!result.ok) {
      setFeedback({
        type: 'error',
        text: result.message,
      });
      return;
    }

    setFeedback({
      type: 'success',
      text: result.message,
    });

    router.replace('/home');
  };

  return (
    <Screen hideBottomNav scroll={false} contentStyle={styles.screenContent}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <View style={[styles.box, isWeb && styles.boxWeb]}>
          <View style={styles.header}>
            <Text style={styles.title}>Log In</Text>
            <Text style={styles.subtitle}>Opcional</Text>
          </View>

          <View style={styles.form}>
            <View
              style={[
                styles.inputWrapper,
                emailFocused && styles.inputWrapperFocused,
                isWeb && styles.inputWrapperWeb,
              ]}
            >
              <TextInput
                value={email}
                onChangeText={setEmail}
                placeholder="Email"
                placeholderTextColor={palette.primary}
                style={[styles.input, isWeb && styles.inputWeb]}
                autoCapitalize="none"
                keyboardType="email-address"
                onFocus={() => setEmailFocused(true)}
                onBlur={() => setEmailFocused(false)}
              />
            </View>

            <View
              style={[
                styles.passwordWrapper,
                passwordFocused && styles.inputWrapperFocused,
                isWeb && styles.inputWrapperWeb,
              ]}
            >
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder="Password"
                placeholderTextColor={palette.primary}
                style={[styles.passwordInput, isWeb && styles.inputWeb]}
                autoCapitalize="none"
                secureTextEntry={!showPassword}
                onFocus={() => setPasswordFocused(true)}
                onBlur={() => setPasswordFocused(false)}
              />

              <Pressable onPress={() => setShowPassword((current) => !current)}>
                <Ionicons
                  name={showPassword ? 'eye-outline' : 'eye-off-outline'}
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
                feedback.type === 'error' ? styles.feedbackError : styles.feedbackSuccess,
              ]}
            >
              <Text style={styles.feedbackText}>{feedback.text}</Text>
            </View>
          ) : null}

          <Pressable
            style={[styles.button, isWeb && styles.buttonWeb, isSubmitting && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={isSubmitting}
          >
            <Text style={styles.buttonText}>
              {isSubmitting ? 'Entrando...' : 'Log In'}
            </Text>
          </Pressable>

          <Pressable onPress={() => router.push('/signup')}>
            <Text style={styles.secondaryLink}>Criar conta</Text>
          </Pressable>

          <Text style={styles.helperText}>
            Usuário teste: teste@precobao.com / 123456
          </Text>
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
    maxWidth: 420,
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
    lineHeight: 30,
  },
  subtitle: {
    color: palette.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  form: {
    gap: spacing.md,
  },
  inputWrapper: {
    height: 48,
    borderWidth: 1,
    borderColor: palette.primary,
    borderRadius: radius.sm,
    backgroundColor: palette.surface,
    paddingHorizontal: spacing.sm,
    justifyContent: 'center',
  },
  inputWrapperWeb: {
    height: 54,
  },
  inputWrapperFocused: {
    borderColor: palette.primary,
    borderWidth: 2,
  },
  input: {
    color: palette.text,
    fontSize: 16,
    paddingVertical: spacing.sm,
  },
  inputWeb: {
    fontSize: 17,
    outlineWidth: 0,
    outlineColor: 'transparent',
    outlineStyle: 'none',
  },
  passwordWrapper: {
    height: 48,
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
  feedbackSuccess: {
    backgroundColor: '#F1FFF4',
    borderWidth: 1,
    borderColor: '#B9E4C1',
  },
  feedbackText: {
    color: palette.text,
    fontSize: 14,
    lineHeight: 20,
  },
  button: {
    height: 48,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.xl,
  },
  buttonWeb: {
    height: 54,
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
  helperText: {
    color: palette.textSoft,
    textAlign: 'center',
    marginTop: spacing.md,
    fontSize: 13,
  },
});