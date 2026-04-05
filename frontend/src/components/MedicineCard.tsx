import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { getLowestOffer, Medicine, pharmacyColors } from '../data/mockData';
import { palette, radius, spacing } from '../theme';

type MedicineCardProps = {
  medicine: Medicine;
  onPress: () => void;
  compact?: boolean;
};

export function MedicineCard({ medicine, onPress, compact = false }: MedicineCardProps) {
  const lowest = getLowestOffer(medicine);

  return (
    <Pressable style={[styles.card, compact && styles.compactCard]} onPress={onPress}>
      <View style={[styles.imageBox, compact && styles.compactImageBox]}>
        <Ionicons name="image-outline" size={compact ? 24 : 34} color={palette.textSoft} />
      </View>

      <Text style={styles.name} numberOfLines={1}>
        {medicine.name}
      </Text>
      <Text style={[styles.pharmacy, { color: pharmacyColors[lowest.pharmacy] ?? palette.primary }]}>
        {lowest.pharmacy}
      </Text>
      <Text style={styles.price}>${lowest.price.toFixed(2)}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '31%',
  },
  compactCard: {
    width: '31%',
  },
  imageBox: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: radius.md,
    backgroundColor: '#E9E9E9',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  compactImageBox: {
    aspectRatio: 1,
  },
  name: {
    color: palette.text,
    fontSize: 12,
    marginBottom: 2,
  },
  pharmacy: {
    fontSize: 10,
    marginBottom: 4,
  },
  price: {
    color: palette.text,
    fontWeight: '700',
    fontSize: 14,
  },
});
