import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet } from 'react-native';
import { PaperProvider, MD3LightTheme, Appbar, Card, Text, Button } from 'react-native-paper';

// Tipagem preliminar das rotas
type RootStackParamList = {
  Busca: undefined;
  Detalhes: { medicamentoId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

// Componente mock atualizado com Material Design 3
function BuscaScreenMock() {
  return (
    <View style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleLarge">Catálogo Preço-Bão</Text>
          <Text variant="bodyMedium" style={{ marginTop: 8 }}>
            A interface Material Design 3 foi configurada com sucesso. A busca de medicamentos aparecerá aqui.
          </Text>
        </Card.Content>
        <Card.Actions>
          <Button mode="contained" onPress={() => console.log('Buscando...')}>
            Testar Busca
          </Button>
        </Card.Actions>
      </Card>
    </View>
  );
}

export default function App() {
  return (
    // PaperProvider injeta o tema global do Material 3
    <PaperProvider theme={MD3LightTheme}>
      <NavigationContainer>
        <StatusBar style="auto" />
        <Stack.Navigator 
          initialRouteName="Busca"
          screenOptions={{
            // Desativamos o cabeçalho padrão do React Navigation para usar o Appbar do Paper no futuro, se desejado
            headerShown: true, 
          }}
        >
          <Stack.Screen 
            name="Busca" 
            component={BuscaScreenMock} 
            options={{ title: 'Medicamentos' }} 
          />
        </Stack.Navigator>
      </NavigationContainer>
    </PaperProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: MD3LightTheme.colors.background,
  },
  card: {
    marginTop: 16,
  }
});