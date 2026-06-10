import { zodResolver } from '@hookform/resolvers/zod';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import React, { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from 'react-native';
import { z } from 'zod';

import { Screen } from '../components/Screen';
import { useAppContext } from '../context/AppContext';
import { palette, radius, spacing } from '../theme';

const signupSchema = z
  .object({
    name: z.string().trim().min(2, 'O nome deve ter no mínimo 2 caracteres'),
    email: z.string().email('Digite um email válido'),
    password: z.string().min(8, 'A senha deve ter no mínimo 8 caracteres'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'As senhas não coincidem',
    path: ['confirmPassword'],
  });

type SignupFormValues = z.infer<typeof signupSchema>;

export default function SignupScreen() {
  const { registerUser } = useAppContext();

  const { width } = useWindowDimensions();

  const isWeb = Platform.OS === 'web';
  const isWide = isWeb && width >= 900;

  const {
    control,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [focusedField, setFocusedField] = useState<string | null>(null);

  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'error' | 'success'>('error');

  const onSubmit = async (data: SignupFormValues) => {
    setMessage('');
    setMessageType('error');

    const result = await registerUser({
      name: data.name,
      email: data.email,
      password: data.password,
      confirmPassword: data.confirmPassword,
    });

    if (result.ok) {
      setMessageType('success');
      setMessage(result.message);
      setTimeout(() => {
        router.replace('/(app)/home' as never);
      }, 1000);
    } else {
      setMessageType('error');
      setMessage(result.message);
      setError('root', { message: result.message });
    }
  };

  return (
    <Screen
      hideBottomNav
      scroll
      contentStyle={[styles.screenContent, isWide && styles.screenContentWeb]}
    >
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={[styles.page, isWide && styles.pageWeb]}>
          <View style={[styles.hero, !isWide && styles.heroMobile]}>
            <Pressable style={styles.backButton} onPress={() => router.replace('/login')}>
              <Ionicons name="chevron-back" size={22} color={palette.text} />
            </Pressable>

            <View style={styles.logoBox}>
              <Text style={styles.logoText}>P</Text>
            </View>

            <Text style={[styles.heroTitle, !isWide && styles.heroTitleMobile]}>
              Crie sua conta
            </Text>

            <Text style={styles.heroSubtitle}>
              Salve seus medicamentos favoritos e tenha uma experiência mais personalizada.
            </Text>

            <View style={styles.infoPanel}>
              <View style={styles.infoRow}>
                <Ionicons name="checkmark-circle-outline" size={21} color={palette.success} />
                <Text style={styles.infoText}>Cadastro simples e rápido</Text>
              </View>

              <View style={styles.infoRow}>
                <Ionicons name="heart-outline" size={21} color={palette.primary} />
                <Text style={styles.infoText}>Favoritos vinculados à sua conta</Text>
              </View>

              <View style={styles.infoRow}>
                <Ionicons name="shield-checkmark-outline" size={21} color={palette.primary} />
                <Text style={styles.infoText}>Pronto para autenticação real do backend</Text>
              </View>
            </View>
          </View>

          <View style={[styles.card, isWide && styles.cardWeb]}>
            <View style={styles.cardHeader}>
              <Text style={styles.title}>Criar conta</Text>

              <Text style={styles.subtitle}>
                Preencha os dados abaixo para iniciar seu cadastro.
              </Text>
            </View>

            <View style={styles.form}>
              <View>
                <Controller
                  control={control}
                  name="name"
                  render={({ field: { onChange, onBlur, value } }) => (
                    <View
                      style={[
                        styles.inputWrapper,
                        focusedField === 'name' && styles.inputWrapperFocused,
                        errors.name && styles.inputWrapperError,
                      ]}
                    >
                      <Ionicons name="person-outline" size={20} color={palette.primary} />
                      <TextInput
                        value={value}
                        onChangeText={onChange}
                        placeholder="Nome"
                        placeholderTextColor={palette.muted}
                        textContentType="name"
                        style={[styles.input, isWeb && styles.inputWeb]}
                        onFocus={() => setFocusedField('name')}
                        onBlur={() => {
                          setFocusedField(null);
                          onBlur();
                        }}
                      />
                    </View>
                  )}
                />
                {errors.name && <Text style={styles.helperText}>{errors.name.message}</Text>}
              </View>

              <View>
                <Controller
                  control={control}
                  name="email"
                  render={({ field: { onChange, onBlur, value } }) => (
                    <View
                      style={[
                        styles.inputWrapper,
                        focusedField === 'email' && styles.inputWrapperFocused,
                        errors.email && styles.inputWrapperError,
                      ]}
                    >
                      <Ionicons name="mail-outline" size={20} color={palette.primary} />
                      <TextInput
                        value={value}
                        onChangeText={onChange}
                        placeholder="Email"
                        placeholderTextColor={palette.muted}
                        autoCapitalize="none"
                        keyboardType="email-address"
                        textContentType="emailAddress"
                        style={[styles.input, isWeb && styles.inputWeb]}
                        onFocus={() => setFocusedField('email')}
                        onBlur={() => {
                          setFocusedField(null);
                          onBlur();
                        }}
                      />
                    </View>
                  )}
                />
                {errors.email && <Text style={styles.helperText}>{errors.email.message}</Text>}
              </View>

              <View>
                <Controller
                  control={control}
                  name="password"
                  render={({ field: { onChange, onBlur, value } }) => (
                    <View
                      style={[
                        styles.inputWrapper,
                        focusedField === 'password' && styles.inputWrapperFocused,
                        errors.password && styles.inputWrapperError,
                      ]}
                    >
                      <Ionicons name="lock-closed-outline" size={20} color={palette.primary} />
                      <TextInput
                        value={value}
                        onChangeText={onChange}
                        placeholder="Senha"
                        placeholderTextColor={palette.muted}
                        secureTextEntry={!showPassword}
                        textContentType="newPassword"
                        style={[styles.input, isWeb && styles.inputWeb]}
                        onFocus={() => setFocusedField('password')}
                        onBlur={() => {
                          setFocusedField(null);
                          onBlur();
                        }}
                      />
                      <Pressable
                        style={styles.eyeButton}
                        onPress={() => setShowPassword((current) => !current)}
                      >
                        <Ionicons
                          name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                          size={21}
                          color={palette.textSoft}
                        />
                      </Pressable>
                    </View>
                  )}
                />
                {errors.password && <Text style={styles.helperText}>{errors.password.message}</Text>}
              </View>

              <View>
                <Controller
                  control={control}
                  name="confirmPassword"
                  render={({ field: { onChange, onBlur, value } }) => (
                    <View
                      style={[
                        styles.inputWrapper,
                        focusedField === 'confirmPassword' && styles.inputWrapperFocused,
                        errors.confirmPassword && styles.inputWrapperError,
                      ]}
                    >
                      <Ionicons name="lock-closed-outline" size={20} color={palette.primary} />
                      <TextInput
                        value={value}
                        onChangeText={onChange}
                        placeholder="Confirmar senha"
                        placeholderTextColor={palette.muted}
                        secureTextEntry={!showConfirmPassword}
                        textContentType="newPassword"
                        style={[styles.input, isWeb && styles.inputWeb]}
                        onFocus={() => setFocusedField('confirmPassword')}
                        onBlur={() => {
                          setFocusedField(null);
                          onBlur();
                        }}
                      />
                      <Pressable
                        style={styles.eyeButton}
                        onPress={() => setShowConfirmPassword((current) => !current)}
                      >
                        <Ionicons
                          name={showConfirmPassword ? 'eye-off-outline' : 'eye-outline'}
                          size={21}
                          color={palette.textSoft}
                        />
                      </Pressable>
                    </View>
                  )}
                />
                {errors.confirmPassword && <Text style={styles.helperText}>{errors.confirmPassword.message}</Text>}
              </View>
            </View>

            {message ? (
              <View
                style={[
                  styles.messageBox,
                  messageType === 'success'
                    ? styles.messageSuccess
                    : styles.messageError,
                ]}
              >
                <Ionicons
                  name={
                    messageType === 'success'
                      ? 'checkmark-circle-outline'
                      : 'alert-circle-outline'
                  }
                  size={19}
                  color={messageType === 'success' ? palette.success : palette.danger}
                />

                <Text style={styles.messageText}>{message}</Text>
              </View>
            ) : null}

            <Pressable
              style={[styles.button, isSubmitting && styles.buttonDisabled]}
              onPress={handleSubmit(onSubmit)}
              disabled={isSubmitting}
            >
              <Text style={styles.buttonText}>
                {isSubmitting ? 'Enviando...' : 'Cadastrar'}
              </Text>
            </Pressable>

            <Pressable
              style={styles.loginButton}
              onPress={() => router.replace('/login' as never)}
            >
              <Text style={styles.loginButtonText}>Já tenho conta</Text>
            </Pressable>
          </View>
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
    flexGrow: 1,
    justifyContent: 'center',
    paddingBottom: spacing.xl,
  },

  screenContentWeb: {
    minHeight: '100vh' as any,
  },

  page: {
    width: '100%',
    gap: spacing.lg,
  },

  pageWeb: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 56,
  },

  hero: {
    flex: 1,
    maxWidth: 520,
  },

  heroMobile: {
    maxWidth: '100%',
  },

  backButton: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },

  logoBox: {
    width: 68,
    height: 68,
    borderRadius: 22,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.lg,
    shadowColor: '#0F172A',
    shadowOpacity: 0.12,
    shadowRadius: 18,
    shadowOffset: {
      width: 0,
      height: 10,
    },
    elevation: 5,
  },

  logoText: {
    color: palette.surface,
    fontSize: 38,
    fontWeight: '900',
  },

  heroTitle: {
    color: palette.text,
    fontSize: 46,
    lineHeight: 52,
    fontWeight: '900',
    maxWidth: 500,
  },

  heroTitleMobile: {
    fontSize: 32,
    lineHeight: 38,
  },

  heroSubtitle: {
    color: palette.textSoft,
    fontSize: 16,
    lineHeight: 24,
    marginTop: spacing.md,
    maxWidth: 480,
  },

  infoPanel: {
    marginTop: spacing.xl,
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: 24,
    padding: spacing.lg,
    gap: spacing.md,
  },

  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },

  infoText: {
    flex: 1,
    color: palette.text,
    fontSize: 15,
    fontWeight: '700',
  },

  card: {
    width: '100%',
    maxWidth: 480,
    alignSelf: 'center',
    backgroundColor: palette.surface,
    borderRadius: 28,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.lg,
    shadowColor: '#0F172A',
    shadowOpacity: 0.1,
    shadowRadius: 24,
    shadowOffset: {
      width: 0,
      height: 14,
    },
    elevation: 6,
  },

  cardWeb: {
    padding: spacing.xl,
  },

  cardHeader: {
    marginBottom: spacing.xl,
  },

  title: {
    color: palette.text,
    fontSize: 31,
    fontWeight: '900',
  },

  subtitle: {
    color: palette.textSoft,
    fontSize: 15,
    lineHeight: 22,
    marginTop: spacing.xs,
  },

  form: {
    gap: spacing.md,
  },

  inputWrapper: {
    minHeight: 56,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: radius.lg,
    backgroundColor: palette.surface,
    paddingHorizontal: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },

  inputWrapperFocused: {
    borderColor: palette.primary,
    borderWidth: 2,
  },

  inputWrapperError: {
    borderColor: palette.danger,
    borderWidth: 1,
  },

  helperText: {
    color: palette.danger,
    fontSize: 13,
    marginTop: spacing.xs,
    paddingHorizontal: spacing.sm,
  },

  input: {
    flex: 1,
    color: palette.text,
    fontSize: 16,
    paddingVertical: spacing.sm,
  },

  inputWeb: {
    fontSize: 17,
    outlineWidth: 0,
    outlineColor: 'transparent',
    outlineStyle: 'none' as any,
  },

  eyeButton: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    justifyContent: 'center',
    alignItems: 'center',
  },

  messageBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    marginTop: spacing.lg,
  },

  messageError: {
    backgroundColor: '#FFF1F1',
    borderWidth: 1,
    borderColor: '#F0B7B7',
  },

  messageSuccess: {
    backgroundColor: '#F1FFF4',
    borderWidth: 1,
    borderColor: '#B9E4C1',
  },

  messageText: {
    flex: 1,
    color: palette.text,
    fontSize: 14,
    lineHeight: 20,
  },

  button: {
    height: 54,
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
    fontWeight: '800',
  },

  loginButton: {
    height: 52,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: palette.primary,
    backgroundColor: palette.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.md,
  },

  loginButtonText: {
    color: palette.primary,
    fontSize: 15,
    fontWeight: '800',
  },
});