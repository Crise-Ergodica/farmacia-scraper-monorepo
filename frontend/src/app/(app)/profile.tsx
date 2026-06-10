import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import React, { useEffect, useState } from 'react';

import {
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from 'react-native';

import { Screen } from '../../components/Screen';
import { useAppContext } from '../../context/AppContext';
import { palette, radius, spacing } from '../../theme';

export default function ProfileScreen() {
  const {
    sessionMode,
    currentUserName,
    currentUserEmail,
    favoriteIds,
    recentIds,
    logout,
    updateProfile,
  } = useAppContext();

  const { width } = useWindowDimensions();

  const isWeb = Platform.OS === 'web';
  const isDesktop = isWeb && width >= 980;

  const isAuthenticated = sessionMode === 'authenticated';

  const displayName = isAuthenticated
    ? currentUserName || 'Usuário autenticado'
    : 'Convidado';

  const displayEmail = isAuthenticated
    ? currentUserEmail || 'Email não informado'
    : 'Entre ou crie uma conta para salvar seus dados';

  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');

  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editName, setEditName] = useState(displayName);
  const [editEmail, setEditEmail] = useState(
    isAuthenticated ? currentUserEmail || '' : ''
  );
  const [editMessage, setEditMessage] = useState('');

  useEffect(() => {
    setEditName(isAuthenticated ? currentUserName || '' : '');
    setEditEmail(isAuthenticated ? currentUserEmail || '' : '');
  }, [isAuthenticated, currentUserName, currentUserEmail]);

  const handleLogout = () => {
    logout();
    router.replace('/login');
  };

  const openEditModal = () => {
    setEditName(currentUserName || '');
    setEditEmail(currentUserEmail || '');
    setEditMessage('');
    setEditModalVisible(true);
  };

  const closeEditModal = () => {
    setEditModalVisible(false);
    setEditMessage('');
  };

  const handleSaveProfile = () => {
    if (!editName.trim()) {
      setEditMessage('Informe o nome.');
      return;
    }

    if (!editEmail.trim()) {
      setEditMessage('Informe o email.');
      return;
    }

    if (!editEmail.includes('@')) {
      setEditMessage('Informe um email válido.');
      return;
    }

    updateProfile(editName, editEmail);
    setEditModalVisible(false);
    setEditMessage('');
  };

  return (
    <>
      <Screen>
        <View style={[styles.page, isDesktop && styles.pageDesktop]}>
          <View style={[styles.profileCard, isDesktop && styles.profileCardDesktop]}>
            <View style={styles.profileHeader}>
              <View style={styles.avatarBox}>
                <Text style={styles.avatarText}>{initials || 'P'}</Text>
              </View>

              <View style={styles.profileTitleBox}>
                <View
                  style={[
                    styles.statusBadge,
                    isAuthenticated ? styles.authBadge : styles.guestBadge,
                  ]}
                >
                  <View
                    style={[
                      styles.statusDot,
                      isAuthenticated ? styles.authDot : styles.guestDot,
                    ]}
                  />

                  <Text
                    style={[
                      styles.statusText,
                      isAuthenticated ? styles.authText : styles.guestText,
                    ]}
                  >
                    {isAuthenticated ? 'Conta ativa' : 'Modo convidado'}
                  </Text>
                </View>

                <Text style={[styles.userName, isDesktop && styles.userNameDesktop]}>
                  {displayName}
                </Text>

                <Text style={styles.userEmail}>{displayEmail}</Text>
              </View>
            </View>

            <View style={styles.profileDivider} />

            <View style={styles.infoGrid}>
              <View style={[styles.infoCard, isDesktop && styles.infoCardDesktop]}>
                <View style={styles.infoIconBox}>
                  <Ionicons name="heart-outline" size={21} color={palette.primary} />
                </View>

                <Text style={styles.infoValue}>{favoriteIds.length}</Text>

                <Text style={styles.infoLabel}>Favoritos</Text>
              </View>

              <View style={[styles.infoCard, isDesktop && styles.infoCardDesktop]}>
                <View style={styles.infoIconBox}>
                  <Ionicons name="time-outline" size={21} color={palette.primary} />
                </View>

                <Text style={styles.infoValue}>{recentIds.length}</Text>

                <Text style={styles.infoLabel}>Visualizados</Text>
              </View>

              <View style={[styles.infoCard, isDesktop && styles.infoCardDesktop]}>
                <View style={styles.infoIconBox}>
                  <Ionicons
                    name={
                      isAuthenticated
                        ? 'checkmark-circle-outline'
                        : 'person-outline'
                    }
                    size={21}
                    color={isAuthenticated ? palette.success : palette.primary}
                  />
                </View>

                <Text style={styles.infoValue}>
                  {isAuthenticated ? 'Ativo' : 'Livre'}
                </Text>

                <Text style={styles.infoLabel}>Acesso</Text>
              </View>
            </View>
          </View>

          <View style={[styles.sideColumn, isDesktop && styles.sideColumnDesktop]}>
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeader}>
                <View style={styles.sectionIcon}>
                  <Ionicons
                    name="person-circle-outline"
                    size={22}
                    color={palette.primary}
                  />
                </View>

                <View style={styles.sectionTitleBox}>
                  <Text style={styles.sectionTitle}>Dados da conta</Text>
                </View>
              </View>

              <View style={styles.detailList}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Nome</Text>

                  <Text numberOfLines={1} style={styles.detailValue}>
                    {displayName}
                  </Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Email</Text>

                  <Text numberOfLines={1} style={styles.detailValue}>
                    {isAuthenticated ? displayEmail : 'Não conectado'}
                  </Text>
                </View>

                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Sessão</Text>

                  <Text numberOfLines={1} style={styles.detailValue}>
                    {isAuthenticated ? 'Usuário autenticado' : 'Convidado'}
                  </Text>
                </View>
              </View>
            </View>

            <View style={styles.sectionCard}>
              <View style={styles.sectionHeader}>
                <View style={styles.sectionIcon}>
                  <Ionicons
                    name="sparkles-outline"
                    size={22}
                    color={palette.primary}
                  />
                </View>

                <View style={styles.sectionTitleBox}>
                  <Text style={styles.sectionTitle}>Experiência</Text>

                  <Text style={styles.sectionSubtitle}>
                    Recursos disponíveis para sua conta
                  </Text>
                </View>
              </View>

              {isAuthenticated ? (
                <View style={styles.benefitsList}>
                  <View style={styles.benefitRow}>
                    <Ionicons
                      name="checkmark-circle"
                      size={20}
                      color={palette.success}
                    />

                    <Text style={styles.benefitText}>
                      Você pode salvar medicamentos favoritos.
                    </Text>
                  </View>

                  <View style={styles.benefitRow}>
                    <Ionicons
                      name="checkmark-circle"
                      size={20}
                      color={palette.success}
                    />

                    <Text style={styles.benefitText}>
                      Você pode receber noticações de menor preço de remédios.
                    </Text>
                  </View>
                </View>
              ) : (
                <View style={styles.guestBox}>
                  <Text style={styles.guestTitle}>
                    Você está navegando como convidado.
                  </Text>

                  <Text style={styles.guestDescription}>
                    Entre ou crie uma conta para salvar favoritos e visualizar seus dados no perfil.
                  </Text>

                  <View style={styles.guestActions}>
                    <Pressable
                      style={styles.primaryButton}
                      onPress={() => router.push('/login' as never)}
                    >
                      <Text style={styles.primaryButtonText}>Entrar</Text>
                    </Pressable>

                    <Pressable
                      style={styles.secondaryButton}
                      onPress={() => router.push('/signup' as never)}
                    >
                      <Text style={styles.secondaryButtonText}>Criar conta</Text>
                    </Pressable>
                  </View>
                </View>
              )}
            </View>

            {isAuthenticated ? (
              <View style={styles.actionsCard}>
                <Pressable style={styles.editButton} onPress={openEditModal}>
                  <Ionicons name="create-outline" size={19} color={palette.primary} />

                  <Text style={styles.editButtonText}>Editar dados</Text>
                </Pressable>

                <Pressable style={styles.logoutButton} onPress={handleLogout}>
                  <Ionicons name="exit-outline" size={19} color={palette.danger} />

                  <Text style={styles.logoutButtonText}>Sair da conta</Text>
                </Pressable>
              </View>
            ) : null}
          </View>
        </View>
      </Screen>

      <Modal
        transparent
        animationType="fade"
        visible={editModalVisible}
        onRequestClose={closeEditModal}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.editModal, isDesktop && styles.editModalDesktop]}>
            <View style={styles.modalHeader}>
              <View>
                <Text style={styles.modalTitle}>Editar dados</Text>

                <Text style={styles.modalSubtitle}>
                  Atualize o nome e email exibidos no perfil.
                </Text>
              </View>

              <Pressable style={styles.modalCloseButton} onPress={closeEditModal}>
                <Ionicons name="close" size={22} color={palette.text} />
              </Pressable>
            </View>

            <View style={styles.modalForm}>
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Nome</Text>

                <TextInput
                  value={editName}
                  onChangeText={setEditName}
                  placeholder="Digite seu nome"
                  placeholderTextColor={palette.muted}
                  style={[styles.input, isWeb && styles.inputWeb]}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Email</Text>

                <TextInput
                  value={editEmail}
                  onChangeText={setEditEmail}
                  placeholder="Digite seu email"
                  placeholderTextColor={palette.muted}
                  autoCapitalize="none"
                  keyboardType="email-address"
                  style={[styles.input, isWeb && styles.inputWeb]}
                />
              </View>
            </View>

            {editMessage ? (
              <View style={styles.editMessageBox}>
                <Ionicons
                  name="alert-circle-outline"
                  size={19}
                  color={palette.danger}
                />

                <Text style={styles.editMessageText}>{editMessage}</Text>
              </View>
            ) : null}

            <View style={styles.modalActions}>
              <Pressable style={styles.cancelButton} onPress={closeEditModal}>
                <Text style={styles.cancelButtonText}>Cancelar</Text>
              </Pressable>

              <Pressable style={styles.saveButton} onPress={handleSaveProfile}>
                <Text style={styles.saveButtonText}>Salvar</Text>
              </Pressable>
            </View>
          </View>

          <Pressable style={styles.modalBackdrop} onPress={closeEditModal} />
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  page: {
    width: '100%',
    gap: spacing.lg,
  },

  pageDesktop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },

  profileCard: {
    width: '100%',
    backgroundColor: palette.surface,
    borderRadius: 28,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.lg,
    shadowColor: '#0F172A',
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: {
      width: 0,
      height: 10,
    },
    elevation: 4,
  },

  profileCardDesktop: {
    flex: 1.1,
    minHeight: 420,
    padding: spacing.xl,
  },

  profileHeader: {
    gap: spacing.lg,
  },

  avatarBox: {
    width: 92,
    height: 92,
    borderRadius: 30,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#0F172A',
    shadowOpacity: 0.14,
    shadowRadius: 18,
    shadowOffset: {
      width: 0,
      height: 10,
    },
    elevation: 5,
  },

  avatarText: {
    color: palette.surface,
    fontSize: 34,
    fontWeight: '900',
  },

  profileTitleBox: {
    gap: spacing.xs,
  },

  statusBadge: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 8,
  },

  authBadge: {
    backgroundColor: '#EAF8EF',
  },

  guestBadge: {
    backgroundColor: palette.primarySoft,
  },

  statusDot: {
    width: 8,
    height: 8,
    borderRadius: radius.pill,
  },

  authDot: {
    backgroundColor: palette.success,
  },

  guestDot: {
    backgroundColor: palette.primary,
  },

  statusText: {
    fontSize: 12,
    fontWeight: '900',
  },

  authText: {
    color: palette.success,
  },

  guestText: {
    color: palette.primary,
  },

  userName: {
    color: palette.text,
    fontSize: 32,
    lineHeight: 38,
    fontWeight: '900',
  },

  userNameDesktop: {
    fontSize: 44,
    lineHeight: 50,
  },

  userEmail: {
    color: palette.textSoft,
    fontSize: 15,
    lineHeight: 22,
  },

  profileDivider: {
    height: 1,
    backgroundColor: palette.border,
    marginVertical: spacing.xl,
  },

  infoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },

  infoCard: {
    width: '100%',
    backgroundColor: '#F8FBFF',
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E2EDFA',
    padding: spacing.lg,
  },

  infoCardDesktop: {
    flex: 1,
    minWidth: 0,
  },

  infoIconBox: {
    width: 42,
    height: 42,
    borderRadius: radius.pill,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },

  infoValue: {
    color: palette.text,
    fontSize: 25,
    fontWeight: '900',
  },

  infoLabel: {
    color: palette.textSoft,
    fontSize: 13,
    fontWeight: '700',
    marginTop: 3,
  },

  sideColumn: {
    width: '100%',
    gap: spacing.lg,
  },

  sideColumnDesktop: {
    flex: 0.9,
  },

  sectionCard: {
    backgroundColor: palette.surface,
    borderRadius: 28,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.lg,
    shadowColor: '#0F172A',
    shadowOpacity: 0.06,
    shadowRadius: 14,
    shadowOffset: {
      width: 0,
      height: 8,
    },
    elevation: 3,
  },

  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginBottom: spacing.lg,
  },

  sectionIcon: {
    width: 46,
    height: 46,
    borderRadius: radius.lg,
    backgroundColor: palette.primarySoft,
    justifyContent: 'center',
    alignItems: 'center',
  },

  sectionTitleBox: {
    flex: 1,
  },

  sectionTitle: {
    color: palette.text,
    fontSize: 19,
    fontWeight: '900',
  },

  sectionSubtitle: {
    color: palette.textSoft,
    fontSize: 13,
    marginTop: 2,
  },

  detailList: {
    gap: spacing.sm,
  },

  detailRow: {
    backgroundColor: palette.surfaceAlt,
    borderRadius: radius.lg,
    padding: spacing.md,
  },

  detailLabel: {
    color: palette.textSoft,
    fontSize: 12,
    fontWeight: '800',
    marginBottom: 4,
  },

  detailValue: {
    color: palette.text,
    fontSize: 16,
    fontWeight: '800',
  },

  benefitsList: {
    gap: spacing.md,
  },

  benefitRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },

  benefitText: {
    flex: 1,
    color: palette.text,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '600',
  },

  guestBox: {
    backgroundColor: '#F8FBFF',
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: '#E2EDFA',
    padding: spacing.lg,
  },

  guestTitle: {
    color: palette.text,
    fontSize: 18,
    fontWeight: '900',
  },

  guestDescription: {
    color: palette.textSoft,
    fontSize: 14,
    lineHeight: 20,
    marginTop: spacing.xs,
  },

  guestActions: {
    marginTop: spacing.lg,
    gap: spacing.sm,
  },

  actionsCard: {
    backgroundColor: palette.surface,
    borderRadius: 28,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.lg,
    gap: spacing.md,
  },

  primaryButton: {
    minHeight: 48,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  primaryButtonText: {
    color: palette.surface,
    fontSize: 15,
    fontWeight: '900',
  },

  secondaryButton: {
    minHeight: 48,
    borderRadius: radius.pill,
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  secondaryButtonText: {
    color: palette.primary,
    fontSize: 15,
    fontWeight: '900',
  },

  editButton: {
    minHeight: 50,
    borderRadius: radius.pill,
    backgroundColor: palette.primarySoft,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.sm,
  },

  editButtonText: {
    color: palette.primary,
    fontSize: 15,
    fontWeight: '900',
  },

  logoutButton: {
    minHeight: 50,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: '#F0B7B7',
    backgroundColor: '#FFF1F1',
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.sm,
  },

  logoutButtonText: {
    color: palette.danger,
    fontSize: 15,
    fontWeight: '900',
  },

  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.35)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },

  modalBackdrop: {
    ...StyleSheet.absoluteFillObject,
  },

  editModal: {
    width: '100%',
    maxWidth: 480,
    backgroundColor: palette.surface,
    borderRadius: 28,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.lg,
    zIndex: 2,
    shadowColor: '#0F172A',
    shadowOpacity: 0.18,
    shadowRadius: 28,
    shadowOffset: {
      width: 0,
      height: 18,
    },
    elevation: 8,
  },

  editModalDesktop: {
    padding: spacing.xl,
  },

  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.md,
    alignItems: 'flex-start',
    marginBottom: spacing.lg,
  },

  modalTitle: {
    color: palette.text,
    fontSize: 25,
    fontWeight: '900',
  },

  modalSubtitle: {
    color: palette.textSoft,
    fontSize: 14,
    lineHeight: 20,
    marginTop: 4,
  },

  modalCloseButton: {
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: palette.surfaceAlt,
    justifyContent: 'center',
    alignItems: 'center',
  },

  modalForm: {
    gap: spacing.md,
  },

  inputGroup: {
    gap: spacing.xs,
  },

  inputLabel: {
    color: palette.text,
    fontSize: 13,
    fontWeight: '900',
  },

  input: {
    minHeight: 52,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: palette.border,
    backgroundColor: palette.surface,
    paddingHorizontal: spacing.md,
    color: palette.text,
    fontSize: 16,
  },

  inputWeb: {
    outlineWidth: 0,
    outlineColor: 'transparent',
    outlineStyle: 'none' as any,
  },

  editMessageBox: {
    marginTop: spacing.md,
    backgroundColor: '#FFF1F1',
    borderWidth: 1,
    borderColor: '#F0B7B7',
    borderRadius: radius.lg,
    padding: spacing.md,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },

  editMessageText: {
    flex: 1,
    color: palette.text,
    fontSize: 14,
    lineHeight: 20,
  },

  modalActions: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.xl,
  },

  cancelButton: {
    flex: 1,
    minHeight: 50,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: palette.border,
    backgroundColor: palette.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },

  cancelButtonText: {
    color: palette.text,
    fontSize: 15,
    fontWeight: '900',
  },

  saveButton: {
    flex: 1,
    minHeight: 50,
    borderRadius: radius.pill,
    backgroundColor: palette.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },

  saveButtonText: {
    color: palette.surface,
    fontSize: 15,
    fontWeight: '900',
  },
});