import { Pressable, StyleSheet, Text, View } from 'react-native';

import { palette, spacing } from '../theme';

type OfferRowProps = {
  medicineName: string;
  pharmacy: string;
  price: number;
  color?: string;
  onPress?: () => void;
};

function OfferRowContent({ medicineName, pharmacy, price, color }: OfferRowProps) {
  return (
    <>
      <View>
        <Text style={styles.name}>{medicineName}</Text>
        <Text style={[styles.pharmacy, color ? { color } : null]}>{pharmacy}</Text>
      </View>
      <Text style={styles.price}>${price.toFixed(2)}</Text>
    </>
  );
}

export function OfferRow(props: OfferRowProps) {
  if (props.onPress) {
    return (
      <Pressable style={styles.row} onPress={props.onPress}>
        <OfferRowContent {...props} />
      </Pressable>
    );
  }

  return (
    <View style={styles.row}>
      <OfferRowContent {...props} />
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#DFDFDF',
  },
  name: {
    fontSize: 18,
    color: palette.text,
    marginBottom: 2,
  },
  pharmacy: {
    fontSize: 12,
  },
  price: {
    fontWeight: '700',
    fontSize: 18,
    color: palette.text,
    marginLeft: spacing.md,
  },
});
