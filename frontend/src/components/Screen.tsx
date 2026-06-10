import { Ionicons } from '@expo/vector-icons';
import { router, usePathname } from 'expo-router';
import React, { ReactNode, useMemo, useState } from 'react';
import {
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleProp,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from 'react-native';

import { useAppContext } from '../context/AppContext';
import { palette, radius, shadow, spacing } from '../theme';

type ScreenProps = {
  children: ReactNode;
  hideBottomNav?: boolean;
  scroll?: boolean;
  contentStyle?: StyleProp<ViewStyle>;
};

export function Screen({
  children,
  hideBottomNav = false,
  scroll = true,
  contentStyle,
}: ScreenProps) {
  const pathname = usePathname();

  const { sessionMode, currentUserName, logout } = useAppContext();

  const [sidebarVisible, setSidebarVisible] = useState(false);

  const isWeb = Platform.OS === 'web';

  const activeTab = useMemo(() => {
    if (pathname.includes('/favorites')) return 'favorites';
    if (pathname.includes('/profile')) return 'profile';
    return 'home';
  }, [pathname]);

  const goTo = (path: string) => {
    setSidebarVisible(false);
    router.push(path as never);
  };

  const handleLogout = () => {
    setSidebarVisible(false);
    logout();
    router.replace('/login');
  };

  const contentStyles = [
    styles.content,
    isWeb && styles.contentWeb,
    hideBottomNav && styles.contentWithoutBottomNav,
    contentStyle,
  ];

  return (
    <View style={styles.root}>
      {scroll ? (
        <ScrollView
          style={styles.flex}
          contentContainerStyle={contentStyles}
          showsVerticalScrollIndicator={false}
        >
          {children}
        </ScrollView>
      ) : (
        <View style={[styles.flex, contentStyles]}>{children}</View>
      )}

      {!hideBottomNav ? (
        <View style={styles.bottomNavWrapper}>
          <View style={[styles.bottomNav, isWeb && styles.bottomNavWeb]}>
            <Pressable
              style={styles.navButton}
              onPress={() => setSidebarVisible(true)}
            >
              <Ionicons name="menu" size={22} color={palette.text} />
            </Pressable>

            <Pressable
              style={[
                styles.navButton,
                activeTab === 'home' && styles.navButtonActive,
              ]}
              onPress={() => router.push('/home')}
            >
              <Ionicons
                name="home"
                size={21}
                color={activeTab === 'home' ? palette.surface : palette.textSoft}
              />
            </Pressable>

            <Pressable
              style={[
                styles.navButton,
                activeTab === 'favorites' && styles.navButtonActive,
              ]}
              onPress={() => router.push('/favorites')}
            >
              <Ionicons
                name="heart"
                size={21}
                color={
                  activeTab === 'favorites' ? palette.surface : palette.textSoft
                }
              />
            </Pressable>

            <Pressable
              style={[
                styles.navButton,
                activeTab === 'profile' && styles.navButtonActive,
              ]}
              onPress={() => router.push('/profile')}
            >
              <Ionicons
                name="person"
                size={21}
                color={
                  activeTab === 'profile' ? palette.surface : palette.textSoft
                }
              />
            </Pressable>
          </View>
        </View>
      ) : null}

      <Modal
        transparent
        animationType="fade"
        visible={sidebarVisible}
        onRequestClose={() => setSidebarVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.sidebar, isWeb && styles.sidebarWeb]}>
            <View style={styles.sidebarHeader}>
              <View style={styles.sidebarLogo}>
                <Text style={styles.sidebarLogoText}>P</Text>
              </View>

              <View style={styles.sidebarHeaderText}>
                <Text style={styles.sidebarTitle}>Preço Bão</Text>

                <Text style={styles.sidebarSubtitle}>
                  {sessionMode === 'authenticated'
                    ? currentUserName || 'Usuário autenticado'
                    : 'Modo convidado'}
                </Text>
              </View>
            </View>

            <View style={styles.sidebarMenu}>
              <Pressable style={styles.sidebarItem} onPress={() => goTo('/home')}>
                <Ionicons name="home-outline" size={20} color={palette.primary} />
                <Text style={styles.sidebarItemText}>Home</Text>
              </Pressable>

              <Pressable
                style={styles.sidebarItem}
                onPress={() => goTo('/favorites')}
              >
                <Ionicons
                  name="heart-outline"
                  size={20}
                  color={palette.primary}
                />
                <Text style={styles.sidebarItemText}>Favoritos</Text>
              </Pressable>

              <Pressable
                style={styles.sidebarItem}
                onPress={() => goTo('/profile')}
              >
                <Ionicons
                  name="person-outline"
                  size={20}
                  color={palette.primary}
                />
                <Text style={styles.sidebarItemText}>Perfil</Text>
              </Pressable>

              {sessionMode !== 'authenticated' ? (
                <>
                  <Pressable
                    style={styles.sidebarItem}
                    onPress={() => goTo('/login')}
                  >
                    <Ionicons
                      name="log-in-outline"
                      size={20}
                      color={palette.primary}
                    />
                    <Text style={styles.sidebarItemText}>Fazer login</Text>
                  </Pressable>

                  <Pressable
                    style={styles.sidebarItem}
                    onPress={() => goTo('/signup')}
                  >
                    <Ionicons
                      name="person-add-outline"
                      size={20}
                      color={palette.primary}
                    />
                    <Text style={styles.sidebarItemText}>Criar conta</Text>
                  </Pressable>
                </>
              ) : (
                <Pressable style={styles.sidebarItem} onPress={handleLogout}>
                  <Ionicons name="exit-outline" size={20} color={palette.danger} />
                  <Text style={[styles.sidebarItemText, styles.logoutText]}>
                    Sair
                  </Text>
                </Pressable>
              )}
            </View>
          </View>

          <Pressable
            style={styles.modalBackdrop}
            onPress={() => setSidebarVisible(false)}
          />
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: palette.background,
  },

  flex: {
    flex: 1,
  },

  content: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.lg,
    paddingBottom: 118,
  },

  contentWeb: {
    maxWidth: 1240,
    width: '100%',
    alignSelf: 'center',
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.xl,
  },

  contentWithoutBottomNav: {
    paddingBottom: spacing.lg,
  },

  bottomNavWrapper: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 18,
    alignItems: 'center',
    paddingHorizontal: spacing.md,
  },

  bottomNav: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: 'rgba(255,255,255,0.96)',
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.sm,
    ...shadow.soft,
  },

  bottomNavWeb: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },

  navButton: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: palette.surfaceAlt,
  },

  navButtonActive: {
    backgroundColor: palette.primary,
  },

  modalOverlay: {
    flex: 1,
    flexDirection: 'row',
  },

  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.28)',
  },

  sidebar: {
    width: 294,
    backgroundColor: palette.surface,
    paddingTop: 30,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
    borderTopRightRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
    ...shadow.medium,
  },

  sidebarWeb: {
    width: 330,
  },

  sidebarHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginBottom: spacing.xl,
  },

  sidebarLogo: {
    width: 46,
    height: 46,
    borderRadius: radius.md,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  sidebarLogoText: {
    color: palette.surface,
    fontSize: 24,
    fontWeight: '800',
  },

  sidebarHeaderText: {
    flex: 1,
  },

  sidebarTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: palette.text,
  },

  sidebarSubtitle: {
    marginTop: 3,
    fontSize: 13,
    color: palette.textSoft,
  },

  sidebarMenu: {
    gap: spacing.sm,
  },

  sidebarItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: 50,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    backgroundColor: palette.surfaceAlt,
  },

  sidebarItemText: {
    fontSize: 15,
    fontWeight: '700',
    color: palette.text,
  },

  logoutText: {
    color: palette.danger,
  },
});