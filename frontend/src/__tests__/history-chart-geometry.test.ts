import { getTooltipPosition } from '../services/historyChartGeometry';

const area = { width: 320, height: 250 };
const tooltip = { width: 180, height: 92 };

function expectInside(position: { left: number; top: number }) {
  expect(position.left).toBeGreaterThanOrEqual(8);
  expect(position.top).toBeGreaterThanOrEqual(8);
  expect(position.left + tooltip.width).toBeLessThanOrEqual(area.width - 8);
  expect(position.top + tooltip.height).toBeLessThanOrEqual(area.height - 8);
}

it.each([
  ['top-left', { x: 84, y: 16 }, 'below'],
  ['top-right', { x: 284, y: 16 }, 'below'],
  ['bottom-left', { x: 84, y: 186 }, 'above'],
  ['bottom-right', { x: 284, y: 186 }, 'above'],
])('keeps a tooltip inside the chart at the %s corner', (_corner, point, verticalPlacement) => {
  const position = getTooltipPosition(point, area, tooltip);

  expectInside(position);
  if (verticalPlacement === 'below') {
    expect(position.top).toBeGreaterThan(point.y);
  } else {
    expect(position.top + tooltip.height).toBeLessThan(point.y);
  }
});

it('places a center tooltip above the point and adjusts for points close together', () => {
  const center = getTooltipPosition({ x: 160, y: 120 }, area, tooltip);
  const close = getTooltipPosition({ x: 161, y: 121 }, area, tooltip);

  expectInside(center);
  expectInside(close);
  expect(center.top + tooltip.height).toBeLessThan(120);
  expect(close.top + tooltip.height).toBeLessThan(121);
});

it('clamps a tooltip to a narrow viewport when its point is on either edge', () => {
  const narrow = { width: 250, height: 220 };
  const smallTooltip = { width: 180, height: 92 };
  const left = getTooltipPosition({ x: 40, y: 100 }, narrow, smallTooltip);
  const right = getTooltipPosition({ x: 210, y: 100 }, narrow, smallTooltip);

  expect(left.left).toBeGreaterThanOrEqual(8);
  expect(left.left + smallTooltip.width).toBeLessThanOrEqual(narrow.width - 8);
  expect(right.left).toBeGreaterThanOrEqual(8);
  expect(right.left + smallTooltip.width).toBeLessThanOrEqual(narrow.width - 8);
});
