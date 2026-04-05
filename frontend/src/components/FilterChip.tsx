import { Pressable, StyleSheet, Text } from 'react-native';

import { palette, radius, spacing } from '../theme';

type FilterChipProps = {
  label: string;
  active: boolean;
  onPress: () => void;
};

export function FilterChip({ label, active, onPress }: FilterChipProps) {
  return (
    <Pressable style={[styles.chip, active && styles.chipActive]} onPress={onPress}>
      <Text style={[styles.label, active && styles.labelActive]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    minHeight: 40,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: palette.primary,
    backgroundColor: palette.surface,
    justifyContent: 'center',
    paddingHorizontal: spacing.md,
    marginBottom: spacing.sm,
  },
  chipActive: {
    backgroundColor: '#81B8EF',
  },
  label: {
    color: palette.text,
    fontSize: 14,
  },
  labelActive: {
    color: palette.surface,
    fontWeight: '600',
  },
});
