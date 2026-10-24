import React from 'react';
import { act, fireEvent, render, waitFor } from '@testing-library/react-native';

import { MedicineImage } from '../components/MedicineImage';
import { Medicamento } from '../types/api';

it('tries API-resolved image references in order, then shows the fallback', async () => {
  const medicine = {
    id: 9,
    nome: 'Nimesulida 100mg Cimed 12 Comprimidos',
    codigo_barras: '7896523212685',
    principio_ativo: '',
    laboratorio: '',
    exige_receita: false,
    categorias: [],
    imagem_status: 'pendente',
    imagem_urls: [1, 2].map((id) => `https://images.example.test/nimesulida-${id}.jpg`),
    ofertas: [],
  } as Medicamento;

  const screen = await render(<MedicineImage medicine={medicine} />);
  const label = `Embalagem de ${medicine.nome}`;
  expect(screen.getByLabelText(label).props.source.uri).toContain('-1.jpg');
  await fireEvent(screen.getByLabelText(label), 'error');
  expect(screen.getByLabelText(label).props.source.uri).toContain('-2.jpg');
  await fireEvent(screen.getByLabelText(label), 'error');
  expect(screen.queryByLabelText(label)).toBeNull();
  expect(screen.getByText('Imagem indisponível')).toBeTruthy();
});

it('resets the fallback cursor when the persisted image reference changes', async () => {
  const medicine = {
    id: 10,
    nome: 'Produto teste',
    codigo_barras: '7891234567895',
    principio_ativo: '',
    laboratorio: '',
    exige_receita: false,
    categorias: [],
    imagem_status: 'pendente',
    imagem_urls: [1, 2].map((id) => `https://images.example.test/fallback-${id}.jpg`),
    ofertas: [],
  } as Medicamento;
  const view = await render(<MedicineImage medicine={medicine} />);
  const label = `Embalagem de ${medicine.nome}`;
  await fireEvent(view.getByLabelText(label), 'error');
  expect(view.getByLabelText(label).props.source.uri).toContain('fallback-2.jpg');

  await act(async () => {
    view.rerender(
      <MedicineImage
        medicine={{
          ...medicine,
          imagem_urls: ['https://cdn.example.test/updated.jpg'],
          imagem_status: 'verificada',
        }}
      />,
    );
  });
  await waitFor(() => {
    expect(view.getByLabelText(label).props.source.uri).toBe('https://cdn.example.test/updated.jpg');
  });
});
