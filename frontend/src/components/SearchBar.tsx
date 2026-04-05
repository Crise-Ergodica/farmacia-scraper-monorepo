import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import {
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
  placeholder = 'Farma+',
  ...textInputProps
}: SearchBarProps) {
  return (
    <View style={styles.row}>
      {onBack ? (
        <Pressable style={styles.backButton} onPress={onBack}>
          <Ionicons name="arrow-back" size={18} color={palette.primary} />
        </Pressable>
      ) : null}

      <View style={styles.container}>
        <Ionicons name="search-outline" size={18} color={palette.primary} />

        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={palette.primary}
          style={styles.input}
          returnKeyType="search"
          onSubmitEditing={onSubmit}
          {...textInputProps}
        />

        {onFilter ? (
          <Pressable onPress={onFilter} hitSlop={8}>
            <Text style={styles.filterText}>Filter</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  backButton: {
    width: 28,
    height: 28,
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
  input: {
    flex: 1,
    color: palette.text,
    fontSize: 16,
    paddingVertical: spacing.sm,
  },
  filterText: {
    color: palette.primary,
    fontSize: 13,
    fontWeight: '600',
  },
});
