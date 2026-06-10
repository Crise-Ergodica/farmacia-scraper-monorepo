import 'react-native-gesture-handler';

import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import { GlobalButtonHover } from '../components/GlobalButtonHover';
import { AppProvider } from '../context/AppContext';
import { palette } from '../theme';

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <AppProvider>
        <GlobalButtonHover />

        <StatusBar style="dark" backgroundColor={palette.background} />

        <Stack screenOptions={{ headerShown: false }} />
      </AppProvider>
    </GestureHandlerRootView>
  );
}