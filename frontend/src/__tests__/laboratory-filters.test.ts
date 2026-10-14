import { api } from '../services/api';
import { fetchCatalogPage, fetchFilterOptions, formatLaboratoryLabel, getLaboratoryDisplayName, normalizeText } from '../services/catalog';

beforeEach(() => jest.clearAllMocks());

it('formats the visible company name while retaining the exact source value', async () => {
  const cimedValue = '02814497000107 - CIMED INDUSTRIA S.A';
  const sourceLimitedValue = '11082598000393 - BESINS HEALTHCARE BRASIL COMERCIAL E DISTRIBUIDORA DE MEDICAMEN';
  (api.get as jest.Mock).mockResolvedValue({
    data: {
      laboratorios: [
        cimedValue,
        sourceLimitedValue,
        '00923140000131 - EMS SIGMA PHARMA LTDA',
        '57507378000365 - EMS S/A',
        '00000000000001 - LABORATORIO ALFA LTDA',
        '00000000000002 - LABORATORIO ALFA LTDA',
        '3M - MEDICAL PRODUCTS 2',
      ],
    },
  });

  const options = await fetchFilterOptions();
  const cimed = options.find((option) => option.value === cimedValue)!;
  const sourceLimited = options.find((option) => option.value === sourceLimitedValue)!;
  const emsOptions = options.filter((option) => option.label.startsWith('EMS'));
  const ambiguousOptions = options.filter((option) => option.value.includes('LABORATORIO ALFA'));

  expect(cimed.label).toBe('Cimed Indústria S.A.');
  expect(cimed.value).toBe(cimedValue);
  expect(sourceLimited.label).toBe('Besins Healthcare Brasil Comercial e Distribuidora de Medicamen…');
  expect(sourceLimited.value).toBe(sourceLimitedValue);
  expect(emsOptions.map((option) => option.label)).toEqual(['EMS S.A.', 'EMS Sigma Pharma Ltda.']);
  expect(new Set(emsOptions.map((option) => option.id)).size).toBe(2);
  expect(ambiguousOptions.map((option) => option.label)).toEqual([
    'Laboratório Alfa Ltda. · unidade 1',
    'Laboratório Alfa Ltda. · unidade 2',
  ]);
  expect(new Set(ambiguousOptions.map((option) => option.value)).size).toBe(2);
  expect(formatLaboratoryLabel('3M - MEDICAL PRODUCTS 2')).toBe('3M - Medical Products 2');

  (api.get as jest.Mock).mockResolvedValue({ data: { total: 0, limit: 20, offset: 0, items: [] } });
  await fetchCatalogPage({ filters: [cimed] });
  const requestUrl = (api.get as jest.Mock).mock.calls[1][0] as string;
  expect(new URL(`http://local.test${requestUrl}`).searchParams.get('filtros')).toBe(
    `laboratorio:${cimedValue}`
  );
});

it('normalizes partial search text without considering case or accents', () => {
  expect(normalizeText('Cimed Indústria S.A.').includes(normalizeText('cime'))).toBe(true);
  expect(normalizeText('Aché Laboratórios Farmacêuticos').includes(normalizeText('farmaceuticos'))).toBe(true);
});

it('provides one friendly display label and omits missing laboratory placeholders', () => {
  expect(getLaboratoryDisplayName('05161069000110 - BRAINFARMA INDUSTRIA QUIMICA E FARMACEUTICA S.A.'))
    .toBe('Brainfarma Indústria Química e Farmacêutica S.A.');
  expect(getLaboratoryDisplayName('Não informado')).toBeUndefined();
  expect(getLaboratoryDisplayName('')).toBeUndefined();
});
