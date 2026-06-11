import { Ionicons } from '@expo/vector-icons';
import React, { useMemo } from 'react';
import {
  Image,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useAppContext } from '../context/AppContext';
import { palette, radius, spacing } from '../theme';
import { Medicamento } from '../types/api';

type MedicineCardProps = {
  medicine: Medicamento;
  onPress?: () => void;
  compact?: boolean;
};

function formatPrice(value: number) {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

export function MedicineCard({
  medicine,
  onPress,
  compact = false,
}: MedicineCardProps) {
  const { favoriteIds, toggleFavorite, sessionMode } = useAppContext();

  const isWeb = Platform.OS === 'web';
  const isFavorite = favoriteIds.includes(medicine.id);

  const lowestOffer = useMemo(() => {
    if (!medicine.ofertas || medicine.ofertas.length === 0) {
      return null;
    }

    return medicine.ofertas.reduce((lowest, current) =>
      Number(current.preco) < Number(lowest.preco) ? current : lowest
    );
  }, [medicine.ofertas]);

  const imageUrl = lowestOffer?.imagem_url || medicine.ofertas?.[0]?.imagem_url;
  const subtitle = medicine.laboratorio?.trim() || 'Não informado';

  const handleFavoritePress = (event?: any) => {
    event?.stopPropagation?.();
    event?.preventDefault?.();

    if (sessionMode !== 'authenticated') {
      return;
    }

    toggleFavorite(medicine.id);
  };

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed, hovered }) => [
        styles.card,
        compact && styles.cardCompact,
        compact && !isWeb && styles.cardCompactMobile,
        compact && isWeb && styles.cardCompactWeb,
        isWeb && hovered && styles.cardHovered,
        pressed && styles.cardPressed,
      ]}
    >
      <View style={styles.imageWrapper}>
        <View
          style={[
            styles.imageBox,
            compact && styles.imageBoxCompact,
            compact && !isWeb && styles.imageBoxCompactMobile,
          ]}
        >
          {imageUrl ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.image}
              resizeMode="contain"
            />
          ) : (
            <View style={styles.imagePlaceholder}>
              <Ionicons
                name="medical-outline"
                size={28}
                color={palette.primary}
              />
            </View>
          )}
        </View>

        <Pressable
          onPress={handleFavoritePress}
          hitSlop={8}
          style={({ pressed, hovered }) => [
            styles.favoriteButton,
            isWeb && hovered && styles.favoriteButtonHovered,
            pressed && styles.favoriteButtonPressed,
            sessionMode !== 'authenticated' && styles.favoriteButtonDisabled,
          ]}
        >
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={compact && !isWeb ? 16 : 18}
            color={isFavorite ? palette.primary : palette.textSoft}
          />
        </Pressable>
      </View>

      <Text
        numberOfLines={compact && !isWeb ? 3 : 2}
        style={[
          styles.title,
          compact && styles.titleCompact,
          compact && !isWeb && styles.titleCompactMobile,
        ]}
      >
        {medicine.nome}
      </Text>

      <Text
        numberOfLines={1}
        style={[
          styles.subtitle,
          compact && styles.subtitleCompact,
          compact && !isWeb && styles.subtitleCompactMobile,
        ]}
      >
        {subtitle}
      </Text>

      <View style={styles.priceBlock}>
        <Text
          style={[
            styles.priceLabel,
            compact && styles.priceLabelCompact,
            compact && !isWeb && styles.priceLabelCompactMobile,
          ]}
        >
          Menor preço
        </Text>

        <Text
          style={[
            styles.priceValue,
            compact && styles.priceValueCompact,
            compact && !isWeb && styles.priceValueCompactMobile,
          ]}
        >
          {lowestOffer ? formatPrice(Number(lowestOffer.preco)) : 'Não informado'}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    width: Platform.OS === 'web' ? 220 : 170,
    backgroundColor: palette.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.md,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: {
      width: 0,
      height: 4,
    },
    elevation: 3,
  },

  cardCompact: {
    padding: Platform.OS === 'web' ? spacing.md : 10,
  },

  cardCompactMobile: {
    width: '31.6%',
    minWidth: '31.6%',
    maxWidth: '31.6%',
    borderRadius: 20,
    padding: 8,
  },

  cardCompactWeb: {
    width: 220,
  },

  cardHovered: {
    transform: [
      {
        translateY: -3,
      },
    ],
    shadowOpacity: 0.1,
  },

  cardPressed: {
    opacity: 0.9,
    transform: [
      {
        scale: 0.985,
      },
    ],
  },

  imageWrapper: {
    position: 'relative',
  },

  imageBox: {
    height: 144,
    borderRadius: radius.lg,
    backgroundColor: '#F6F7FB',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },

  imageBoxCompact: {
    height: Platform.OS === 'web' ? 138 : 98,
  },

  imageBoxCompactMobile: {
    height: 82,
    borderRadius: 18,
  },

  image: {
    width: '84%',
    height: '84%',
  },

  imagePlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },

  favoriteButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: Platform.OS === 'web' ? 34 : 30,
    height: Platform.OS === 'web' ? 34 : 30,
    borderRadius: 999,
    backgroundColor: '#FFFFFFEE',
    borderWidth: 1,
    borderColor: palette.border,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
    elevation: 10,
  },

  favoriteButtonHovered: {
    backgroundColor: palette.primarySoft,
  },

  favoriteButtonPressed: {
    opacity: 0.85,
    transform: [
      {
        scale: 0.96,
      },
    ],
  },

  favoriteButtonDisabled: {
    opacity: 0.75,
  },

  title: {
    marginTop: spacing.md,
    fontSize: 18,
    lineHeight: 24,
    fontWeight: '700',
    color: palette.text,
  },

  titleCompact: {
    marginTop: 10,
    fontSize: Platform.OS === 'web' ? 16 : 13,
    lineHeight: Platform.OS === 'web' ? 22 : 18,
  },

  titleCompactMobile: {
    marginTop: 8,
    fontSize: 12,
    lineHeight: 16,
    minHeight: 48,
  },

  subtitle: {
    marginTop: 6,
    color: palette.textSoft,
    fontSize: 14,
    lineHeight: 20,
  },

  subtitleCompact: {
    fontSize: Platform.OS === 'web' ? 13 : 11,
    lineHeight: Platform.OS === 'web' ? 18 : 15,
  },

  subtitleCompactMobile: {
    marginTop: 4,
    fontSize: 10,
    lineHeight: 14,
  },

  priceBlock: {
    marginTop: spacing.sm,
  },

  priceLabel: {
    fontSize: 13,
    color: palette.textSoft,
    fontWeight: '600',
  },

  priceLabelCompact: {
    fontSize: Platform.OS === 'web' ? 12 : 10,
  },

  priceLabelCompactMobile: {
    fontSize: 9,
  },

  priceValue: {
    marginTop: 4,
    fontSize: 24,
    color: palette.primary,
    fontWeight: '900',
  },

  priceValueCompact: {
    fontSize: Platform.OS === 'web' ? 22 : 16,
  },

  priceValueCompactMobile: {
    marginTop: 2,
    fontSize: 12,
    lineHeight: 15,
  },
});