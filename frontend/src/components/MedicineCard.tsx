import { Ionicons } from '@expo/vector-icons';
import { Platform, Pressable, StyleSheet, Text, useWindowDimensions, View, Image } from 'react-native';

import { palette, radius, spacing } from '../theme';
import { Medicamento } from '../types/api';

type MedicineCardProps = {
  medicine: Medicamento;
  onPress: () => void;
  compact?: boolean;
};

export function MedicineCard({ medicine, onPress, compact = false }: MedicineCardProps) {
  const { width } = useWindowDimensions();
  const isWeb = Platform.OS === 'web';

  // Forçamos a conversão para Number durante a comparação de menor preço
  const lowest = medicine.ofertas && medicine.ofertas.length > 0
    ? medicine.ofertas.reduce((min, curr) => 
        (Number(curr.preco) < Number(min.preco) ? curr : min)
      , medicine.ofertas[0])
    : null;

  const compactWidth =
    isWeb && width >= 1400
      ? 220
      : isWeb && width >= 1100
      ? 240
      : isWeb && width >= 900
      ? 210
      : '31%';

  // Fallbacks e extração de dados
  const farmaciaDisplay = lowest ? `Farmácia ID: ${lowest.farmacia_id}` : 'Sem ofertas';
  const priceDisplay = lowest ? `R$ ${Number(lowest.preco).toFixed(2)}` : '--';
  const imageUrl = lowest?.imagem_url; // Extrai a URL da imagem da oferta

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
          // Se tiver imagem real, podemos deixar o fundo transparente ou branco
          imageUrl && { backgroundColor: '#FFFFFF' } 
        ]}
      >
        {imageUrl ? (
          <Image
            source={{ uri: imageUrl }}
            style={styles.medicineImage}
            resizeMode="contain" // Garante que a imagem não fique esticada
          />
        ) : (
          <Ionicons
            name="image-outline"
            size={isWeb ? 30 : compact ? 24 : 34}
            color={palette.textSoft}
          />
        )}
      </View>

      <Text style={[styles.name, isWeb && styles.nameWeb]} numberOfLines={2}>
        {medicine.nome}
      </Text>

      <Text
        style={[
          styles.pharmacy,
          isWeb && styles.pharmacyWeb,
          { color: palette.primary },
        ]}
      >
        {farmaciaDisplay}
      </Text>

      <Text style={[styles.price, isWeb && styles.priceWeb]}>
        {priceDisplay}
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
    overflow: 'hidden', 
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
  medicineImage: {
    width: '100%',
    height: '100%',
    borderRadius: radius.md,
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