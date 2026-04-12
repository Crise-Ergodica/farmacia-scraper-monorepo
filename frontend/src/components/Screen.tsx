import React from 'react';
import {
  Platform,
  SafeAreaView,
  ScrollView,
  StyleProp,
  StyleSheet,
  View,
  ViewStyle,
} from 'react-native';

import { palette, spacing } from '../theme';
import { BottomNav } from './BottomNav';

type ScreenProps = {
  children: React.ReactNode;
  scroll?: boolean;
  contentStyle?: StyleProp<ViewStyle>;
  hideBottomNav?: boolean;
};

export function Screen({
  children,
  scroll = true,
  contentStyle,
  hideBottomNav = false,
}: ScreenProps) {
  const isWeb = Platform.OS === 'web';

  const innerContent = (
    <View
      style={[
        styles.content,
        isWeb && styles.contentWeb,
        !scroll && styles.fill,
        contentStyle,
      ]}
    >
      {children}
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      {scroll ? (
        <ScrollView
          style={styles.body}
          contentContainerStyle={styles.scrollContainer}
          showsVerticalScrollIndicator={false}
        >
          {innerContent}
        </ScrollView>
      ) : (
        <View style={styles.fill}>{innerContent}</View>
      )}

      {hideBottomNav ? null : <BottomNav />}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: palette.background,
  },
  body: {
    flex: 1,
  },
  fill: {
    flex: 1,
  },
  scrollContainer: {
    paddingBottom: spacing.xl,
  },
  content: {
    width: '100%',
    alignSelf: 'center',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    paddingBottom: spacing.xl,
  },
  contentWeb: {
    maxWidth: 1280,
    paddingHorizontal: 24,
    paddingTop: 20,
  },
});