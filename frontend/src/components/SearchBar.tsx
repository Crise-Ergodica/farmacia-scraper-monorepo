import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import {
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
} from 'react-native';

import { palette, radius, shadow, spacing } from '../theme';

type SearchBarProps = {
  value: string;
  onChangeText: (value: string) => void;
  onSubmit?: () => void;
  onBack?: () => void;
  onFilter?: () => void;
  placeholder?: string;
} & Omit<TextInputProps, 'value' | 'onChangeText'>;

export function SearchBar({
  value,
  onChangeText,
  onSubmit,
  onBack,
  onFilter,
  placeholder = 'Preço Bão',
  ...textInputProps
}: SearchBarProps) {
  const isWeb = Platform.OS === 'web';

  const [focused, setFocused] = useState(false);

  return (
    <View style={styles.row}>
      {onBack ? (
        <Pressable style={styles.backButton} onPress={onBack}>
          <Ionicons name="chevron-back" size={25} color={palette.text} />
        </Pressable>
      ) : null}

      <View
        style={[
          styles.container,
          isWeb && styles.containerWeb,
          focused && styles.containerFocused,
        ]}
      >
        <Ionicons name="search" size={21} color={palette.primary} />

        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={palette.muted}
          returnKeyType="search"
          onSubmitEditing={onSubmit}
          style={[styles.input, isWeb && styles.inputWeb]}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          {...textInputProps}
        />

        {onFilter ? (
          <Pressable style={styles.filterButton} onPress={onFilter}>
            <Ionicons name="options-outline" size={18} color={palette.surface} />

            {isWeb ? (
              <Text style={styles.filterText}>Filtros</Text>
            ) : null}
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },

  backButton: {
    width: 42,
    height: 42,
    borderRadius: radius.pill,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.border,
  },

  container: {
    flex: 1,
    minHeight: 52,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: radius.pill,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingLeft: spacing.md,
    paddingRight: spacing.xs,
    backgroundColor: palette.surface,
    ...shadow.soft,
  },

  containerWeb: {
    minHeight: 60,
    paddingLeft: spacing.lg,
    paddingRight: spacing.sm,
  },

  containerFocused: {
    borderColor: palette.primary,
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

  filterButton: {
    minHeight: 40,
    minWidth: 42,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    paddingHorizontal: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xs,
  },

  filterText: {
    color: palette.surface,
    fontSize: 14,
    fontWeight: '800',
  },
});