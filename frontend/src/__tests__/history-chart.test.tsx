import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';

import { HistoryChart } from '../components/HistoryChart';

jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));

const series = [{
  key: '1',
  label: 'Farmácia Central',
  color: '#1688F6',
  history: [
    { timestamp: '2026-06-10T12:00:00Z', label: '10/06/2026', value: 0.59 },
    { timestamp: '2026-06-11T12:00:00Z', label: '11/06/2026', value: 0.63 },
  ],
}];

it('lets touch and keyboard users select a chart point and reads its exact currency value', async () => {
  const { getByTestId, getByRole, getAllByTestId, getByText, getAllByText } = await render(<HistoryChart series={series} />);

  await fireEvent(getByTestId('history-chart'), 'layout', {
    nativeEvent: { layout: { x: 0, y: 0, width: 320, height: 250 } },
  });

  const secondPoint = getAllByTestId('history-point')[1];
  expect(secondPoint.props.accessibilityRole).toBe('button');
  expect(secondPoint.props.accessibilityLabel).toContain('R$ 0,63');
  await fireEvent.press(secondPoint);

  expect(getAllByText('R$ 0,63').length).toBeGreaterThan(1);
  expect(getByText('11/06/2026')).toBeTruthy();
  expect(getByRole('button', { name: /11\/06\/2026/ })).toBeTruthy();
});

it('shows monetary precision on narrow chart axes instead of rounding small prices to zero', async () => {
  const { getByTestId, getAllByText } = await render(<HistoryChart series={series} />);

  await fireEvent(getByTestId('history-chart'), 'layout', {
    nativeEvent: { layout: { x: 0, y: 0, width: 320, height: 250 } },
  });

  expect(getAllByText(/R\$ 0,5[0-9]/).length).toBeGreaterThan(0);
});
