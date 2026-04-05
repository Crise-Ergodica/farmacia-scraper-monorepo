import { Drawer } from 'expo-router/drawer';
import { Platform } from 'react-native';

import { AppDrawerContent } from '../../components/AppDrawerContent';
import { palette } from '../../theme';

export default function AppLayout() {
  return (
    <Drawer
      drawerContent={(props) => <AppDrawerContent {...props} />}
      screenOptions={{
        headerShown: false,
        drawerType: Platform.OS === 'web' ? 'front' : 'front',
        overlayColor: 'rgba(0, 0, 0, 0.15)',
        drawerStyle: {
          backgroundColor: palette.background,
          width: 280,
        },
        sceneStyle: {
          backgroundColor: palette.background,
        },
      }}
    >
      <Drawer.Screen name="home" options={{ title: 'Home', drawerItemStyle: { display: 'none' } }} />
      <Drawer.Screen name="favorites" options={{ title: 'Favoritos' }} />
      <Drawer.Screen name="included-pharmacies" options={{ title: 'Farmácias inclusas' }} />
      <Drawer.Screen name="settings" options={{ title: 'Settings' }} />
      <Drawer.Screen name="about" options={{ title: 'Saiba mais' }} />
      <Drawer.Screen name="profile" options={{ title: 'Perfil', drawerItemStyle: { display: 'none' } }} />
      <Drawer.Screen name="search" options={{ title: 'Busca', drawerItemStyle: { display: 'none' } }} />
      <Drawer.Screen name="filters" options={{ title: 'Filtros', drawerItemStyle: { display: 'none' } }} />
      <Drawer.Screen name="medicine/[id]" options={{ title: 'Detalhe', drawerItemStyle: { display: 'none' } }} />
      <Drawer.Screen name="history/[id]" options={{ title: 'Histórico', drawerItemStyle: { display: 'none' } }} />
    </Drawer>
  );
}
