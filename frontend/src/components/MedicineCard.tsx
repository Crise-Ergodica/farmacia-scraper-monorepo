import { Ionicons } from '@expo/vector-icons';
import { Platform, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';

import { getLowestOffer, Medicine, pharmacyColors } from '../data/mockData';
import { palette, radius, spacing } from '../theme';

type MedicineCardProps = {
  medicine: Medicine;
  onPress: () => void;
  compact?: boolean;
};

export function MedicineCard({ medicine, onPress, compact = false }: MedicineCardProps) {
  const lowest = getLowestOffer(medicine);
  const { width } = useWindowDimensions();
  const isWeb = Platform.OS === 'web';

  const compactWidth =
    isWeb && width >= 1400
      ? 220
      : isWeb && width >= 1100
      ? 240
      : isWeb && width >= 900
      ? 210
      : '31%';

  return (
    <Pressable
      style={[
        styles.card,
        compact ? styles.compactCard : styles.fullCard,
        isWeb && styles.cardWeb,
        compact && { width: compactWidth },
      ]}
      onPress={onPress}
    >
      <View
        style={[
          styles.imageBox,
          compact && styles.compactImageBox,
          isWeb && compact && styles.compactImageBoxWeb,
        ]}
      >
        <Ionicons
          name="image-outline"
          size={isWeb ? 30 : compact ? 24 : 34}
          color={palette.textSoft}
        />
      </View>

      <Text style={[styles.name, isWeb && styles.nameWeb]} numberOfLines={2}>
        {medicine.name}
      </Text>

      <Text
        style={[
          styles.pharmacy,
          isWeb && styles.pharmacyWeb,
          { color: pharmacyColors[lowest.pharmacy] ?? palette.primary },
        ]}
      >
        {lowest.pharmacy}
      </Text>

      <Text style={[styles.price, isWeb && styles.priceWeb]}>
        ${lowest.price.toFixed(2)}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    minWidth: 0,
  },
  fullCard: {
    width: '100%',
  },
  compactCard: {
    width: '31%',
  },
  cardWeb: {
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: '#E7E7E7',
    borderRadius: radius.lg,
    padding: 12,
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
  compactImageBoxWeb: {
    aspectRatio: undefined,
    height: 210,
    borderRadius: 18,
    marginBottom: 12,
  },
  name: {
    color: palette.text,
    fontSize: 12,
    marginBottom: 2,
  },
  nameWeb: {
    fontSize: 17,
    fontWeight: '500',
    lineHeight: 22,
    marginBottom: 4,
  },
  pharmacy: {
    fontSize: 10,
    marginBottom: 4,
  },
  pharmacyWeb: {
    fontSize: 13,
    marginBottom: 8,
  },
  price: {
    color: palette.text,
    fontWeight: '700',
    fontSize: 14,
  },
  priceWeb: {
    fontSize: 28,
  },
});