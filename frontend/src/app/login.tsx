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
  useWindowDimensions,
  View,
} from 'react-native';

import { Screen } from '../components/Screen';
import { useAppContext } from '../context/AppContext';
import { palette, radius, spacing } from '../theme';

export default function LoginScreen() {
  const { continueAsGuest, signIn } = useAppContext();

  const { width } = useWindowDimensions();

  const isWeb = Platform.OS === 'web';
  const isWide = isWeb && width >= 900;

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
            <Pressable style={styles.backButton} onPress={() => router.replace('/')}>
              <Ionicons name="chevron-back" size={22} color={palette.text} />
            </Pressable>

            <View style={styles.logoBox}>
              <Text style={styles.logoText}>P</Text>
            </View>

            <Text style={[styles.heroTitle, !isWide && styles.heroTitleMobile]}>
              Bem-vindo ao Preço Bão
            </Text>

            <Text style={styles.heroSubtitle}>
              Compare medicamentos, acompanhe preços e encontre ofertas nas farmácias disponíveis.
            </Text>

            <View style={styles.benefits}>
              <View style={styles.benefitItem}>
                <View style={styles.benefitIcon}>
                  <Ionicons name="search-outline" size={18} color={palette.primary} />
                </View>
                <Text style={styles.benefitText}>Busca rápida de medicamentos</Text>
              </View>

              <View style={styles.benefitItem}>
                <View style={styles.benefitIcon}>
                  <Ionicons name="heart-outline" size={18} color={palette.primary} />
                </View>
                <Text style={styles.benefitText}>Favoritos para usuários logados</Text>
              </View>

              <View style={styles.benefitItem}>
                <View style={styles.benefitIcon}>
                  <Ionicons name="pricetag-outline" size={18} color={palette.primary} />
                </View>
                <Text style={styles.benefitText}>Comparação de menor preço</Text>
              </View>
            </View>
          </View>

          <View style={[styles.card, isWide && styles.cardWeb]}>
            <View style={styles.cardHeader}>
              <Text style={styles.title}>Entrar</Text>

              <Text style={styles.subtitle}>
                Acesse sua conta ou continue como convidado.
              </Text>
            </View>

            <View style={styles.form}>
              <View
                style={[
                  styles.inputWrapper,
                  emailFocused && styles.inputWrapperFocused,
                ]}
              >
                <Ionicons name="mail-outline" size={20} color={palette.primary} />

                <TextInput
                  value={email}
                  onChangeText={setEmail}
                  placeholder="Email"
                  placeholderTextColor={palette.muted}
                  autoCapitalize="none"
                  keyboardType="email-address"
                  textContentType="emailAddress"
                  style={[styles.input, isWeb && styles.inputWeb]}
                  onFocus={() => setEmailFocused(true)}
                  onBlur={() => setEmailFocused(false)}
                />
              </View>

              <View
                style={[
                  styles.inputWrapper,
                  passwordFocused && styles.inputWrapperFocused,
                ]}
              >
                <Ionicons name="lock-closed-outline" size={20} color={palette.primary} />

                <TextInput
                  value={password}
                  onChangeText={setPassword}
                  placeholder="Senha"
                  placeholderTextColor={palette.muted}
                  secureTextEntry={!showPassword}
                  textContentType="password"
                  style={[styles.input, isWeb && styles.inputWeb]}
                  onFocus={() => setPasswordFocused(true)}
                  onBlur={() => setPasswordFocused(false)}
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
            </View>

            {feedback ? (
              <View
                style={[
                  styles.feedbackBox,
                  feedback.type === 'error'
                    ? styles.feedbackError
                    : styles.feedbackSuccess,
                ]}
              >
                <Ionicons
                  name={
                    feedback.type === 'error'
                      ? 'alert-circle-outline'
                      : 'checkmark-circle-outline'
                  }
                  size={19}
                  color={feedback.type === 'error' ? palette.danger : palette.success}
                />

                <Text style={styles.feedbackText}>{feedback.text}</Text>
              </View>
            ) : null}

            <Pressable
              style={[
                styles.button,
                isSubmitting && styles.buttonDisabled,
              ]}
              onPress={handleLogin}
              disabled={isSubmitting}
            >
              <Text style={styles.buttonText}>
                {isSubmitting ? 'Entrando...' : 'Entrar'}
              </Text>
            </Pressable>

            <Pressable
              style={styles.guestButton}
              onPress={() => {
                continueAsGuest();
                router.replace('/home');
              }}
            >
              <Text style={styles.guestButtonText}>Continuar como convidado</Text>
            </Pressable>

            <View style={styles.dividerRow}>
              <View style={styles.divider} />
              <Text style={styles.dividerText}>ou</Text>
              <View style={styles.divider} />
            </View>

            <Pressable
              style={styles.createAccountButton}
              onPress={() => router.push('/signup' as never)}
            >
              <Text style={styles.createAccountText}>Criar conta</Text>
            </Pressable>

            <Text style={styles.helperText}>
              Usuário teste: teste@precobao.com / 123456
            </Text>
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

  benefits: {
    marginTop: spacing.xl,
    gap: spacing.md,
  },

  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },

  benefitIcon: {
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
  },

  benefitText: {
    color: palette.text,
    fontSize: 15,
    fontWeight: '700',
  },

  card: {
    width: '100%',
    maxWidth: 460,
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

  feedbackBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    borderRadius: radius.lg,
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

  guestButton: {
    height: 52,
    borderRadius: radius.pill,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.md,
  },

  guestButtonText: {
    color: palette.primary,
    fontSize: 15,
    fontWeight: '800',
  },

  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.lg,
  },

  divider: {
    flex: 1,
    height: 1,
    backgroundColor: palette.border,
  },

  dividerText: {
    color: palette.textSoft,
    fontSize: 13,
    fontWeight: '700',
  },

  createAccountButton: {
    height: 52,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: palette.primary,
    backgroundColor: palette.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.lg,
  },

  createAccountText: {
    color: palette.primary,
    fontSize: 15,
    fontWeight: '800',
  },

  helperText: {
    color: palette.textSoft,
    textAlign: 'center',
    marginTop: spacing.md,
    fontSize: 13,
    lineHeight: 19,
  },
});