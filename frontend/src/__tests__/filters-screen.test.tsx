import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';

import FiltersScreen from '../app/(app)/filters';
import { api } from '../services/api';

const mockCatalog = {
  selectedFilters: [],
  filterOptions: [
    { id: 'categoria:similar', type: 'categoria', label: 'Similar', value: 'similar' },
    { id: 'categoria:biologico', type: 'categoria', label: 'Biológico', value: 'biologico' },
    { id: 'receita:com_receita', type: 'receita', label: 'Com receita', value: 'com_receita' },
    { id: 'controle_especial:sim', type: 'controle_especial', label: 'Controle especial', value: 'sim' },
    { id: 'referencia:sim', type: 'referencia', label: 'Medicamento de referência (ANVISA)', value: 'sim' },
    { id: 'classificacao:desconhecida', type: 'classificacao', label: 'Categoria não confirmada', value: 'desconhecida' },
    { id: 'laboratorio:cimed', type: 'laboratorio', label: 'Cimed', value: 'CIMED' },
  ],
  applyFilters: jest.fn(),
  clearFilters: jest.fn(),
  selectedPharmacyId: null,
  setSelectedPharmacyId: jest.fn(),
};

jest.mock('../context/AppContext', () => ({ useCatalogContext: () => mockCatalog }));
jest.mock('../components/Screen', () => ({ Screen: ({ children }: { children: React.ReactNode }) => <>{children}</> }));
jest.mock('expo-router', () => ({ useRouter: () => ({ canGoBack: () => true, back: jest.fn(), replace: jest.fn() }) }));

beforeEach(() => {
  jest.clearAllMocks();
  (api.get as jest.Mock).mockResolvedValue({ data: [] });
});

it('omits active ingredient filtering and only lists supported medicine categories', async () => {
  const ui = await render(<FiltersScreen />);

  expect(ui.queryByText(/Princípios ativos/i)).toBeNull();
  expect(ui.queryByText('Paracetamol')).toBeNull();
  expect(ui.getByText('Tipo de medicamento')).toBeTruthy();
  expect(ui.queryByText('Biológico')).toBeNull();
  expect(ui.getByText('Laboratórios')).toBeTruthy();
  expect(ui.queryByText('Medicamento de referência (ANVISA)')).toBeNull();
  expect(ui.queryByText('Categoria não confirmada')).toBeNull();
});

it('shows one combined sale section and preserves the API semantics for the two selections', async () => {
  const ui = await render(<FiltersScreen />);

  expect(ui.getByText('Com receita')).toBeTruthy();
  expect(ui.getByText('Controle especial')).toBeTruthy();
  expect(ui.getAllByText('Controle especial')).toHaveLength(1);
  expect(ui.queryByText('Venda livre')).toBeNull();

  await fireEvent.press(ui.getByRole('button', { name: 'Com receita' }));
  await fireEvent.press(ui.getByRole('button', { name: 'Controle especial' }));
  await fireEvent.press(ui.getByRole('button', { name: 'Aplicar filtros' }));

  expect(mockCatalog.applyFilters).toHaveBeenCalledWith(expect.arrayContaining([
    expect.objectContaining({ type: 'receita', value: 'com_receita' }),
    expect.objectContaining({ type: 'controle_especial', value: 'sim' }),
  ]));
});
