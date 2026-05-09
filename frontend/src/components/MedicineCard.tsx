import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import {
  Platform,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
  Image,
} from 'react-native';

import { useAppContext } from '../context/AppContext';
import { palette, radius, spacing } from '../theme';
import { Medicamento } from '../types/api';
import { AuthRequiredModal } from './AuthRequiredModal';

type MedicineCardProps = {
  medicine: Medicamento;
  onPress: () => void;
  compact?: boolean;
};

export function MedicineCard({ medicine, onPress, compact = false }: MedicineCardProps) {
  const { width } = useWindowDimensions();
  const isWeb = Platform.OS === 'web';

  const { sessionMode, favoriteIds, toggleFavorite } = useAppContext();
  const [showAuthModal, setShowAuthModal] = useState(false);

  const lowest =
    medicine.ofertas && medicine.ofertas.length > 0
      ? medicine.ofertas.reduce((min, curr) =>
          Number(curr.preco) < Number(min.preco) ? curr : min
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

  const farmaciaDisplay = lowest ? `Farmácia ID: ${lowest.farmacia_id}` : 'Sem ofertas';
  const priceDisplay = lowest
    ? `R$ ${Number(lowest.preco).toFixed(2).replace('.', ',')}`
    : '--';

  const imageUrl = lowest?.imagem_url;
  const isFavorite = favoriteIds.includes(medicine.id);

  const handleFavoritePress = () => {
    if (sessionMode !== 'authenticated') {
      setShowAuthModal(true);
      return;
    }

    toggleFavorite(medicine.id);
  };

  return (
    <>
      <View
        style={[
          styles.card,
          compact ? styles.compactCard : styles.fullCard,
          isWeb && styles.cardWeb,
          compact && { width: compactWidth },
        ]}
      >
        <Pressable style={styles.favoriteButton} onPress={handleFavoritePress}>
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={20}
            color={isFavorite ? palette.danger : palette.primary}
          />
        </Pressable>

        <Pressable onPress={onPress}>
          <View
            style={[
              styles.imageBox,
              compact && styles.compactImageBox,
              isWeb && compact && styles.compactImageBoxWeb,
              imageUrl && { backgroundColor: '#FFFFFF' },
            ]}
          >
            {imageUrl ? (
              <Image
                source={{ uri: imageUrl }}
                style={styles.medicineImage}
                resizeMode="contain"
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
      </View>

      <AuthRequiredModal
        visible={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </>
  );
}

const styles = StyleSheet.create({
  card: {
    minWidth: 0,
    position: 'relative',
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
  favoriteButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    zIndex: 3,
    width: 34,
    height: 34,
    borderRadius: radius.pill,
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: '#E7E7E7',
    justifyContent: 'center',
    alignItems: 'center',
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