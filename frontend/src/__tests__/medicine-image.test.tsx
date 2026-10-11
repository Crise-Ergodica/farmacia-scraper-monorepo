import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';

import { MedicineImage } from '../components/MedicineImage';
import { Medicamento } from '../types/api';

it('tries another exact-product offer image, then shows the fallback', async () => {
  const productUrl = 'https://www.farmaciaindiana.com.br/nimesulida-100mg-cimed-12-comprimidos/p';
  const medicine = {
    id: 9,
    nome: 'Nimesulida 100mg Cimed 12 Comprimidos',
    codigo_barras: '7896523212685',
    principio_ativo: '',
    laboratorio: '',
    exige_receita: false,
    categorias: [],
    imagem_status: 'pendente',
    ofertas: [1, 2].map((id) => ({
      id, farmacia_id: 1, catalogo_id: 9, preco: 5,
      quantidade_estoque: 1, disponivel: true, url_origem: productUrl,
      imagem_url: `https://farmaciaindiana.vteximg.com.br/arquivos/nimesulida-100mg-cimed-12-comprimidos-${id}.jpg`,
    })),
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
