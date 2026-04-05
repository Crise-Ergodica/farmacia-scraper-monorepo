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

  const handleLogin = () => {
    if (!email.trim() && !password.trim()) {
      continueAsGuest();
    } else {
      signIn(email);
    }

    router.replace('/home');
  };

  return (
    <Screen hideBottomNav scroll={false} contentStyle={styles.screenContent}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Log In</Text>
          <Text style={styles.subtitle}>Opcional</Text>
        </View>

        <View style={styles.form}>
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="Email"
            placeholderTextColor={palette.primary}
            style={styles.input}
            autoCapitalize="none"
            keyboardType="email-address"
          />

          <View style={styles.passwordWrapper}>
            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="Password"
              placeholderTextColor={palette.primary}
              style={styles.passwordInput}
              autoCapitalize="none"
              secureTextEntry={!showPassword}
            />

            <Pressable onPress={() => setShowPassword((current) => !current)}>
              <Ionicons name={showPassword ? 'eye-outline' : 'eye-off-outline'} size={22} color={palette.primary} />
            </Pressable>
          </View>
        </View>

        <Pressable style={styles.button} onPress={handleLogin}>
          <Text style={styles.buttonText}>Log In</Text>
        </Pressable>

        <Text style={styles.helperText}>Forgot your password?</Text>
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
  input: {
    height: 44,
    borderWidth: 1,
    borderColor: palette.primary,
    borderRadius: radius.sm,
    backgroundColor: palette.surface,
    paddingHorizontal: spacing.sm,
    color: palette.text,
  },
  passwordWrapper: {
    height: 44,
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
  },
  button: {
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: spacing.xl,
  },
  buttonText: {
    color: palette.surface,
    fontSize: 16,
    fontWeight: '700',
  },
  helperText: {
    color: palette.primary,
    textAlign: 'center',
    marginTop: spacing.md,
    fontWeight: '600',
  },
});
