import useSWR from 'swr';

export interface Printer {
  id: string;
  name: string;
  supported_methods: string[];
  is_active: boolean;
}

export interface Material {
  id: string;
  method: string;
  name: string;
  unit_cost_per_g_cents: number;
  colors: string[];
  is_active: boolean;
}

export interface CatalogData {
  version: number;
  methods: string[];
  printers: Printer[];
  materials: Material[];
}

export interface CatalogResponse {
  version: number;
  data: CatalogData;
  updated_by: string;
  updated_at: string | null;
}

const fetcher = (url: string) => fetch(url).then(res => res.json());

export function useCatalog() {
  const { data, error, isLoading, mutate } = useSWR<CatalogResponse>(
    '/api/v1/catalog',
    fetcher,
    {
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      refreshInterval: 300000, // 5 minutes
      errorRetryCount: 3,
    }
  );

  return {
    catalog: data?.data,
    version: data?.version,
    updatedBy: data?.updated_by,
    updatedAt: data?.updated_at,
    isLoading,
    error,
    mutate,
  };
}

export function useCatalogVersion() {
  const { data, error, isLoading, mutate } = useSWR<{ version: number }>(
    '/api/v1/catalog/version',
    fetcher,
    {
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      refreshInterval: 60000, // 1 minute
      errorRetryCount: 3,
    }
  );

  return {
    version: data?.version,
    isLoading,
    error,
    mutate,
  };
}

// Utility functions for filtering catalog data
export function filterMaterialsByMethod(materials: Material[], method: string): Material[] {
  return materials.filter(material => 
    material.method === method && material.is_active
  );
}

export function filterPrintersByMethod(printers: Printer[], method: string): Printer[] {
  return printers.filter(printer => 
    printer.supported_methods.includes(method) && printer.is_active
  );
}

export function colorsForMaterial(materials: Material[], materialId: string): string[] {
  const material = materials.find(m => m.id === materialId && m.is_active);
  return material?.colors || [];
}

export function getMaterialById(materials: Material[], materialId: string): Material | undefined {
  return materials.find(m => m.id === materialId && m.is_active);
}

export function getPrinterById(printers: Printer[], printerId: string): Printer | undefined {
  return printers.find(p => p.id === printerId && p.is_active);
}
