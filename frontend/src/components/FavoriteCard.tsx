import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { getLowestOffer, Medicine, pharmacyColors } from '../data/mockData';
import { palette, radius, spacing } from '../theme';

type FavoriteCardProps = {
  medicine: Medicine;
  onOpen: () => void;
  onRemove: () => void;
};

export function FavoriteCard({ medicine, onOpen, onRemove }: FavoriteCardProps) {
  const lowest = getLowestOffer(medicine);

  return (
    <Pressable style={styles.card} onPress={onOpen}>
      <Pressable style={styles.deleteButton} onPress={onRemove}>
        <Ionicons name="trash-outline" size={14} color={palette.surface} />
      </Pressable>

      <View style={styles.imageBox} />

      <Text style={styles.notifyLeft}>{"Receber notificação\nde menor preço?"}</Text>
      <View style={styles.notifyRow}>
        <Text style={styles.notifyRight}> </Text>
        <View style={styles.switchTrack}>
          <View style={styles.switchThumb} />
        </View>
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
    marginBottom: spacing.lg,
    position: 'relative',
  },
  deleteButton: {
    position: 'absolute',
    top: 6,
    right: 6,
    zIndex: 2,
    width: 22,
    height: 22,
    borderRadius: radius.pill,
    backgroundColor: palette.danger,
    justifyContent: 'center',
    alignItems: 'center',
  },
  imageBox: {
    width: '100%',
    aspectRatio: 0.85,
    borderRadius: radius.md,
    backgroundColor: '#E9E9E9',
    marginBottom: spacing.xs,
  },
  notifyLeft: {
    color: '#57C76B',
    fontSize: 8,
    lineHeight: 10,
  },
  notifyRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: spacing.xs,
  },
  notifyRight: {
    color: '#57C76B',
    fontSize: 8,
  },
  switchTrack: {
    width: 18,
    height: 10,
    borderRadius: radius.pill,
    backgroundColor: '#D5F2DA',
    justifyContent: 'center',
    paddingHorizontal: 1,
  },
  switchThumb: {
    width: 8,
    height: 8,
    borderRadius: radius.pill,
    backgroundColor: '#57C76B',
    alignSelf: 'flex-end',
  },
  name: {
    fontSize: 12,
    color: palette.text,
  },
  pharmacy: {
    fontSize: 10,
    marginTop: 2,
  },
  price: {
    fontSize: 14,
    fontWeight: '700',
    color: palette.text,
    marginTop: 6,
  },
});
