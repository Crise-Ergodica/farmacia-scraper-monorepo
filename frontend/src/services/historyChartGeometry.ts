export type ChartPointPosition = { x: number; y: number };
export type ChartAreaSize = { width: number; height: number };
export type TooltipPosition = { left: number; top: number };

const EDGE_GAP = 8;
const POINT_GAP = 12;

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), Math.max(minimum, maximum));
}

export function getTooltipPosition(
  point: ChartPointPosition,
  area: ChartAreaSize,
  tooltip: ChartAreaSize,
): TooltipPosition {
  const leftSpace = point.x - EDGE_GAP;
  const rightSpace = area.width - point.x - EDGE_GAP;
  let left = point.x - tooltip.width / 2;

  if (rightSpace < tooltip.width / 2 && leftSpace >= tooltip.width + POINT_GAP) {
    left = point.x - tooltip.width - POINT_GAP;
  } else if (leftSpace < tooltip.width / 2 && rightSpace >= tooltip.width + POINT_GAP) {
    left = point.x + POINT_GAP;
  }

  const topSpace = point.y - EDGE_GAP;
  const bottomSpace = area.height - point.y - EDGE_GAP;
  let top = point.y - tooltip.height - POINT_GAP;

  if (topSpace < tooltip.height + POINT_GAP && bottomSpace >= tooltip.height + POINT_GAP) {
    top = point.y + POINT_GAP;
  } else if (topSpace < tooltip.height + POINT_GAP) {
    top = point.y - tooltip.height / 2;
  }

  return {
    left: clamp(left, EDGE_GAP, area.width - tooltip.width - EDGE_GAP),
    top: clamp(top, EDGE_GAP, area.height - tooltip.height - EDGE_GAP),
  };
}
