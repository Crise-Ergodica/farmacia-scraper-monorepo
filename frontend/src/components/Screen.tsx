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
import { palette, radius, spacing } from '../theme';

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

  const ContentWrapper = scroll ? ScrollView : View;

  return (
    <View style={styles.root}>
      <ContentWrapper
        style={styles.flex}
        contentContainerStyle={[
          styles.content,
          isWeb && styles.contentWeb,
          hideBottomNav && styles.contentWithoutBottomNav,
          contentStyle,
        ]}
        showsVerticalScrollIndicator={false}
      >
        {children}
      </ContentWrapper>

      {!hideBottomNav ? (
        <View style={styles.bottomNavWrapper}>
          <View style={styles.bottomNav}>
            <Pressable
              style={styles.navButton}
              onPress={() => setSidebarVisible(true)}
            >
              <Ionicons name="menu" size={22} color={palette.primary} />
            </Pressable>

            <Pressable
              style={[
                styles.navButton,
                activeTab === 'home' && styles.navButtonActive,
              ]}
              onPress={() => router.push('/home')}
            >
              <Ionicons
                name={activeTab === 'home' ? 'home' : 'home-outline'}
                size={22}
                color={activeTab === 'home' ? palette.surface : palette.primary}
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
                name={activeTab === 'profile' ? 'person' : 'person-outline'}
                size={22}
                color={activeTab === 'profile' ? palette.surface : palette.primary}
              />
            </Pressable>
          </View>
        </View>
      ) : null}

      <Modal
        visible={sidebarVisible}
        transparent
        animationType="fade"
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
                <Ionicons name="home-outline" size={20} color={palette.text} />
                <Text style={styles.sidebarItemText}>Home</Text>
              </Pressable>

              <Pressable style={styles.sidebarItem} onPress={() => goTo('/favorites')}>
                <Ionicons name="heart-outline" size={20} color={palette.text} />
                <Text style={styles.sidebarItemText}>Favoritos</Text>
              </Pressable>

              <Pressable style={styles.sidebarItem} onPress={() => goTo('/profile')}>
                <Ionicons name="person-outline" size={20} color={palette.text} />
                <Text style={styles.sidebarItemText}>Perfil</Text>
              </Pressable>

              {sessionMode !== 'authenticated' ? (
                <>
                  <Pressable style={styles.sidebarItem} onPress={() => goTo('/login')}>
                    <Ionicons name="log-in-outline" size={20} color={palette.text} />
                    <Text style={styles.sidebarItemText}>Fazer login</Text>
                  </Pressable>

                  <Pressable style={styles.sidebarItem} onPress={() => goTo('/signup')}>
                    <Ionicons name="person-add-outline" size={20} color={palette.text} />
                    <Text style={styles.sidebarItemText}>Criar conta</Text>
                  </Pressable>
                </>
              ) : (
                <Pressable style={styles.sidebarItem} onPress={handleLogout}>
                  <Ionicons name="log-out-outline" size={20} color="#D64545" />
                  <Text style={[styles.sidebarItemText, styles.logoutText]}>Sair</Text>
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
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    paddingBottom: 110,
  },
  contentWeb: {
    maxWidth: 1280,
    width: '100%',
    alignSelf: 'center',
    paddingHorizontal: 28,
    paddingTop: 20,
  },
  contentWithoutBottomNav: {
    paddingBottom: spacing.lg,
  },
  bottomNavWrapper: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 14,
    alignItems: 'center',
  },
  bottomNav: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: '#F5F5F5',
    borderWidth: 1,
    borderColor: '#E7E7E7',
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  navButton: {
    width: 42,
    height: 42,
    borderRadius: 999,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#E9E9E9',
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
    backgroundColor: 'rgba(0,0,0,0.18)',
  },
  sidebar: {
    width: 290,
    backgroundColor: palette.surface,
    paddingTop: 28,
    paddingHorizontal: 18,
    paddingBottom: 24,
    borderRightWidth: 1,
    borderRightColor: '#E7E7E7',
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 10,
    shadowOffset: { width: 2, height: 0 },
    elevation: 5,
  },
  sidebarWeb: {
    width: 320,
  },
  sidebarHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 24,
  },
  sidebarLogo: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sidebarLogoText: {
    color: palette.surface,
    fontSize: 22,
    fontWeight: '700',
  },
  sidebarHeaderText: {
    flex: 1,
  },
  sidebarTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: palette.text,
  },
  sidebarSubtitle: {
    marginTop: 2,
    fontSize: 13,
    color: palette.textSoft,
  },
  sidebarMenu: {
    gap: 8,
  },
  sidebarItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    minHeight: 48,
    paddingHorizontal: 12,
    borderRadius: 12,
    backgroundColor: '#F7F7F7',
  },
  sidebarItemText: {
    fontSize: 15,
    fontWeight: '600',
    color: palette.text,
  },
  logoutText: {
    color: '#D64545',
  },
});