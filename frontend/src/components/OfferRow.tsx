import { Pressable, StyleSheet, Text, View } from 'react-native';

import { palette, spacing } from '../theme';

type OfferRowProps = {
  medicineName: string;
  pharmacy: string | number; // Agora aceita o farmacia_id que vem do backend
  price: number | string;    // Agora aceita a string do Decimal do backend
  color?: string;
  onPress?: () => void;
};

function OfferRowContent({ medicineName, pharmacy, price, color }: OfferRowProps) {
  // Conversão segura: garante que price seja tratado como número
  const safePrice = Number(price);
  const priceDisplay = isNaN(safePrice) ? '--' : safePrice.toFixed(2);
  
  // Tratamento para exibir o ID da farmácia caso o nome não esteja disponível no join
  const pharmacyDisplay = typeof pharmacy === 'number' ? `Farmácia ID: ${pharmacy}` : pharmacy;

  return (
    <>
      <View>
        <Text style={styles.name}>{medicineName}</Text>
        <Text style={[styles.pharmacy, color ? { color } : null]}>{pharmacyDisplay}</Text>
      </View>
      <Text style={styles.price}>R$ {priceDisplay}</Text>
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