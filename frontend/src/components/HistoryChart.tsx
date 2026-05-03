import React, { useMemo, useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { palette, radius, spacing } from '../theme';

export type HistoryChartPoint = {
  label: string;
  value: number;
};

export type HistoryChartSeries = {
  key: string;
  label: string;
  color: string;
  history: HistoryChartPoint[];
};

type HistoryChartProps = {
  series: HistoryChartSeries[];
};

function formatPrice(value: number) {
  return `R$ ${value.toFixed(2).replace('.', ',')}`;
}

export function HistoryChart({ series }: HistoryChartProps) {
  const [hoveredBarKey, setHoveredBarKey] = useState<string | null>(null);
  const isWeb = Platform.OS === 'web';

  const labels = useMemo(
    () =>
      Array.from(
        new Set(series.flatMap((item) => item.history.map((point) => point.label)))
      ),
    [series]
  );

  const allValues = series.flatMap((item) => item.history.map((point) => point.value));
  const maxValue = Math.max(...allValues, 1);

  if (!series.length || !labels.length) {
    return (
      <View style={styles.emptyCard}>
        <Text style={styles.emptyText}>Sem histórico de preços disponível.</Text>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <View style={styles.legendRow}>
        {series.map((item) => (
          <View key={item.key} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: item.color }]} />
            <Text style={styles.legendText}>{item.label}</Text>
          </View>
        ))}
      </View>

      <View style={styles.chartArea}>
        {labels.map((label) => (
          <View key={label} style={styles.column}>
            <View style={styles.barGroup}>
              {series.map((item) => {
                const point = item.history.find((historyItem) => historyItem.label === label);
                const value = point?.value ?? 0;
                const height = value > 0 ? Math.max((value / maxValue) * 150, 12) : 0;
                const barKey = `${item.key}-${label}`;
                const showValue = !isWeb || hoveredBarKey === barKey;

                return (
                  <View key={barKey} style={styles.barWrapper}>
                    {showValue && value > 0 ? (
                      <View style={[styles.valueBubble, isWeb && styles.valueBubbleWeb]}>
                        <Text style={styles.valueBubbleText}>{formatPrice(value)}</Text>
                      </View>
                    ) : null}

                    <Pressable
                      onHoverIn={() => {
                        if (isWeb) setHoveredBarKey(barKey);
                      }}
                      onHoverOut={() => {
                        if (isWeb) setHoveredBarKey(null);
                      }}
                      style={[
                        styles.bar,
                        {
                          height,
                          backgroundColor: item.color,
                          opacity: value > 0 ? 1 : 0.18,
                        },
                      ]}
                    />
                  </View>
                );
              })}
            </View>

            <Text style={styles.axisLabel}>{label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E6E6E6',
    padding: spacing.md,
    marginTop: spacing.sm,
  },
  emptyCard: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E6E6E6',
    padding: spacing.lg,
    marginTop: spacing.sm,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 15,
    color: palette.textSoft,
  },
  legendRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F6F6F6',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: radius.pill,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: radius.pill,
  },
  legendText: {
    fontSize: 12,
    color: palette.text,
    fontWeight: '600',
  },
  chartArea: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    minHeight: 220,
  },
  column: {
    flex: 1,
    alignItems: 'center',
  },
  barGroup: {
    height: 185,
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'center',
    gap: 8,
  },
  barWrapper: {
    alignItems: 'center',
    justifyContent: 'flex-end',
    minWidth: 34,
  },
  bar: {
    width: 18,
    borderTopLeftRadius: radius.sm,
    borderTopRightRadius: radius.sm,
  },
  valueBubble: {
    marginBottom: 8,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    borderColor: '#E1E1E1',
    borderRadius: radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 4,
    minWidth: 72,
    alignItems: 'center',
  },
  valueBubbleWeb: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  valueBubbleText: {
    fontSize: 11,
    fontWeight: '700',
    color: palette.text,
  },
  axisLabel: {
    marginTop: spacing.xs,
    fontSize: 11,
    color: palette.textSoft,
  },
});