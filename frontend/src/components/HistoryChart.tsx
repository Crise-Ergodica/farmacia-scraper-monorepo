import { StyleSheet, Text, View } from 'react-native';

import { OfferHistory, pharmacyColors } from '../data/mockData';
import { palette, radius, spacing } from '../theme';

type HistoryChartProps = {
  series: { pharmacy: string; history: OfferHistory[] }[];
};

export function HistoryChart({ series }: HistoryChartProps) {
  const allValues = series.flatMap((item) => item.history.map((point) => point.value));
  const maxValue = Math.max(...allValues, 1);
  const labels = series[0]?.history.map((item) => item.label) ?? [];

  return (
    <View style={styles.card}>
      <View style={styles.legendRow}>
        {series.map((item) => (
          <View key={item.pharmacy} style={styles.legendItem}>
            <View
              style={[styles.legendDot, { backgroundColor: pharmacyColors[item.pharmacy] ?? palette.primary }]}
            />
            <Text style={styles.legendText}>{item.pharmacy}</Text>
          </View>
        ))}
      </View>

      <View style={styles.chartArea}>
        {labels.map((label, index) => (
          <View key={label} style={styles.column}>
            <View style={styles.barGroup}>
              {series.map((item) => {
                const value = item.history[index]?.value ?? 0;
                const height = Math.max((value / maxValue) * 130, 10);

                return (
                  <View
                    key={`${item.pharmacy}-${label}`}
                    style={[
                      styles.bar,
                      {
                        height,
                        backgroundColor: pharmacyColors[item.pharmacy] ?? palette.primary,
                      },
                    ]}
                  />
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
    backgroundColor: palette.surfaceAlt,
    borderRadius: radius.lg,
    padding: spacing.md,
    marginTop: spacing.sm,
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
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: radius.pill,
  },
  legendText: {
    fontSize: 11,
    color: palette.textSoft,
  },
  chartArea: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    minHeight: 160,
  },
  column: {
    flex: 1,
    alignItems: 'center',
  },
  barGroup: {
    height: 140,
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 4,
  },
  bar: {
    width: 10,
    borderTopLeftRadius: radius.sm,
    borderTopRightRadius: radius.sm,
  },
  axisLabel: {
    marginTop: spacing.xs,
    fontSize: 11,
    color: palette.textSoft,
  },
});
