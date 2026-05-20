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

import { palette, radius, spacing } from '../theme';

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
          <Ionicons name="arrow-back" size={20} color={palette.primary} />
        </Pressable>
      ) : null}

      <View
        style={[
          styles.container,
          isWeb && styles.containerWeb,
          focused && styles.containerFocused,
        ]}
      >
        <Ionicons name="search-outline" size={20} color={palette.primary} />

        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={palette.primary}
          style={[styles.input, isWeb && styles.inputWeb]}
          returnKeyType="search"
          onSubmitEditing={onSubmit}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          {...textInputProps}
        />

        {onFilter ? (
          <Pressable onPress={onFilter} hitSlop={8}>
            <Text style={[styles.filterText, isWeb && styles.filterTextWeb]}>Filter</Text>
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
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  container: {
    flex: 1,
    minHeight: 46,
    borderWidth: 1.5,
    borderColor: palette.primary,
    borderRadius: radius.pill,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    backgroundColor: palette.surface,
  },
  containerWeb: {
    minHeight: 54,
    paddingHorizontal: 16,
  },
  containerFocused: {
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
  filterText: {
    color: palette.primary,
    fontSize: 13,
    fontWeight: '600',
  },
  filterTextWeb: {
    fontSize: 14,
  },
});