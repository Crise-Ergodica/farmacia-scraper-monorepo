import { Ionicons } from '@expo/vector-icons';
import React, { useRef, useState } from 'react';
import {
  Animated,
  Image,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';

import { useAppContext } from '../context/AppContext';
import { palette, radius, shadow, spacing } from '../theme';
import { Medicamento } from '../types/api';
import { AuthRequiredModal } from './AuthRequiredModal';

type MedicineCardProps = {
  medicine: Medicamento;
  onPress: () => void;
  compact?: boolean;
};

export function MedicineCard({
  medicine,
  onPress,
  compact = false,
}: MedicineCardProps) {
  const { width } = useWindowDimensions();

  const isWeb = Platform.OS === 'web';

  const { sessionMode, favoriteIds, toggleFavorite } = useAppContext();

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isFavoriteHovered, setIsFavoriteHovered] = useState(false);

  const favoriteScale = useRef(new Animated.Value(1)).current;

  const lowest =
    medicine.ofertas && medicine.ofertas.length > 0
      ? medicine.ofertas.reduce(
          (min, curr) => (Number(curr.preco) < Number(min.preco) ? curr : min),
          medicine.ofertas[0]
        )
      : null;

  const compactWidth =
    isWeb && width >= 1280
      ? '23.4%'
      : isWeb && width >= 980
      ? '31.5%'
      : isWeb
      ? '48%'
      : '31%';

  const priceDisplay = lowest
    ? `R$ ${Number(lowest.preco).toFixed(2).replace('.', ',')}`
    : '--';

  const imageUrl = lowest?.imagem_url;

  const isFavorite = favoriteIds.includes(medicine.id);

  const runFavoriteAnimation = () => {
    favoriteScale.stopAnimation();

    Animated.sequence([
      Animated.timing(favoriteScale, {
        toValue: 1.28,
        duration: 120,
        useNativeDriver: true,
      }),
      Animated.spring(favoriteScale, {
        toValue: 1,
        friction: 3,
        tension: 120,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const handleFavoritePress = () => {
    runFavoriteAnimation();

    if (sessionMode !== 'authenticated') {
      setShowAuthModal(true);
      return;
    }

    toggleFavorite(medicine.id);
  };

  return (
    <>
      <Pressable
        onPress={onPress}
        onHoverIn={() => {
          if (isWeb) {
            setIsHovered(true);
          }
        }}
        onHoverOut={() => {
          if (isWeb) {
            setIsHovered(false);
          }
        }}
        style={[
          styles.card,
          compact ? styles.compactCard : styles.fullCard,
          compact && { width: compactWidth },
          isWeb && styles.cardWeb,
          isWeb && styles.cardTransition,
          isHovered && styles.cardHovered,
        ]}
      >
        <Pressable
          style={[
            styles.favoriteButton,
            isWeb && styles.favoriteButtonTransition,
            isFavoriteHovered && styles.favoriteButtonHovered,
            isFavorite && styles.favoriteButtonActive,
          ]}
          onPress={handleFavoritePress}
          onHoverIn={() => {
            if (isWeb) {
              setIsFavoriteHovered(true);
            }
          }}
          onHoverOut={() => {
            if (isWeb) {
              setIsFavoriteHovered(false);
            }
          }}
        >
          <Animated.View
            style={[
              styles.favoriteAnimatedContent,
              {
                transform: [
                  {
                    scale: favoriteScale,
                  },
                ],
              },
              isFavorite && styles.favoriteAnimatedContentActive,
            ]}
          >
            <Ionicons
              name={isFavorite ? 'heart' : 'heart-outline'}
              size={19}
              color={isFavorite ? palette.danger : palette.textSoft}
            />
          </Animated.View>
        </Pressable>

        <View
          style={[
            styles.imageBox,
            compact && styles.compactImageBox,
            compact && isWeb && styles.compactImageBoxWeb,
            isWeb && styles.imageTransition,
            isHovered && styles.imageBoxHovered,
          ]}
        >
          {imageUrl ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.medicineImage}
              resizeMode="contain"
            />
          ) : (
            <View style={styles.imageFallback}>
              <Ionicons
                name="medical-outline"
                size={compact && isWeb ? 58 : 38}
                color={palette.primary}
              />
            </View>
          )}
        </View>

        <View style={styles.info}>
          <Text numberOfLines={2} style={[styles.name, isWeb && styles.nameWeb]}>
            {medicine.nome}
          </Text>

          <Text
            numberOfLines={1}
            style={[styles.pharmacy, isWeb && styles.pharmacyWeb]}
          >
            {medicine.laboratorio || 'Não informado'}
          </Text>

          <View style={styles.footer}>
            <View>
              <Text style={styles.priceLabel}>Menor preço</Text>

              <Text style={[styles.price, isWeb && styles.priceWeb]}>
                {priceDisplay}
              </Text>
            </View>
          </View>
        </View>
      </Pressable>

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
    borderColor: palette.border,
    borderRadius: radius.xl,
    padding: spacing.md,
    cursor: 'pointer' as any,
    ...shadow.soft,
  },

  cardTransition: {
    transitionDuration: '180ms' as any,
    transitionProperty: 'transform, box-shadow, border-color' as any,
    transitionTimingFunction: 'ease-out' as any,
  },

  cardHovered: {
    borderColor: palette.primary,
    transform: [
      {
        translateY: -6,
      },
      {
        scale: 1.015,
      },
    ],
    shadowOpacity: 0.16,
    shadowRadius: 28,
    shadowOffset: {
      width: 0,
      height: 16,
    },
    elevation: 8,
  },

  favoriteButton: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    zIndex: 3,
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(255,255,255,0.96)',
    borderWidth: 1,
    borderColor: palette.border,
    justifyContent: 'center',
    alignItems: 'center',
  },

  favoriteButtonTransition: {
    transitionDuration: '180ms' as any,
    transitionProperty: 'transform, background-color, border-color, box-shadow' as any,
    transitionTimingFunction: 'ease-out' as any,
  },

  favoriteButtonHovered: {
    backgroundColor: palette.primarySoft,
    borderColor: palette.primary,
    transform: [
      {
        scale: 1.08,
      },
    ],
    shadowOpacity: 0.14,
    shadowRadius: 12,
    shadowOffset: {
      width: 0,
      height: 6,
    },
    elevation: 6,
  },

  favoriteButtonActive: {
    backgroundColor: '#FFF3F3',
    borderColor: '#F2B5B5',
  },

  favoriteAnimatedContent: {
    width: 30,
    height: 30,
    borderRadius: radius.pill,
    justifyContent: 'center',
    alignItems: 'center',
  },

  favoriteAnimatedContentActive: {
    backgroundColor: '#FFECEC',
  },

  imageBox: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: radius.lg,
    backgroundColor: palette.surfaceBlue,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
    overflow: 'hidden',
  },

  imageTransition: {
    transitionDuration: '180ms' as any,
    transitionProperty: 'background-color, transform' as any,
    transitionTimingFunction: 'ease-out' as any,
  },

  imageBoxHovered: {
    backgroundColor: palette.primarySoft,
    transform: [
      {
        scale: 1.02,
      },
    ],
  },

  compactImageBox: {
    aspectRatio: 1,
  },

  compactImageBoxWeb: {
    aspectRatio: undefined,
    height: 220,
    borderRadius: radius.lg,
    marginBottom: spacing.md,
  },

  medicineImage: {
    width: '100%',
    height: '100%',
    borderRadius: radius.md,
  },

  imageFallback: {
    width: '72%',
    height: '72%',
    borderRadius: radius.xl,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
  },

  info: {
    gap: spacing.xs,
  },

  name: {
    color: palette.text,
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 2,
  },

  nameWeb: {
    fontSize: 17,
    lineHeight: 23,
    marginBottom: 2,
  },

  pharmacy: {
    fontSize: 10,
    color: palette.textSoft,
    marginBottom: 4,
  },

  pharmacyWeb: {
    fontSize: 13,
    marginBottom: 8,
  },

  footer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'flex-start',
    gap: spacing.sm,
  },

  priceLabel: {
    fontSize: 11,
    color: palette.textSoft,
    fontWeight: '600',
    marginBottom: 2,
  },

  price: {
    color: palette.primaryDark,
    fontWeight: '900',
    fontSize: 14,
  },

  priceWeb: {
    fontSize: 26,
  },
});