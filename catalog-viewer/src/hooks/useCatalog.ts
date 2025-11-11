import { useState, useEffect } from 'react';
import { Catalog, Table } from '../types/catalog';

const CATALOG_URL = '/catalog.json';

export function useCatalog() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function loadCatalog() {
      try {
        setLoading(true);
        const response = await fetch(CATALOG_URL);
        if (!response.ok) {
          throw new Error(`Failed to load catalog: ${response.statusText}`);
        }
        const data: Catalog = await response.json();
        setCatalog(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    }

    loadCatalog();
  }, []);

  return { catalog, loading, error };
}

export function useTable(tableName: string | null) {
  const { catalog } = useCatalog();
  const [table, setTable] = useState<Table | null>(null);

  useEffect(() => {
    if (!catalog || !tableName) {
      setTable(null);
      return;
    }

    const found = catalog.tables.find(t => t.name === tableName);
    setTable(found || null);
  }, [catalog, tableName]);

  return table;
}

export function useTablesByLayer(layer: string | null) {
  const { catalog } = useCatalog();
  const [tables, setTables] = useState<Table[]>([]);

  useEffect(() => {
    if (!catalog || !layer) {
      setTables([]);
      return;
    }

    const filtered = catalog.tables.filter(t => t.schema === layer);
    setTables(filtered);
  }, [catalog, layer]);

  return tables;
}

export function useSearchTables(query: string) {
  const { catalog } = useCatalog();
  const [results, setResults] = useState<Table[]>([]);

  useEffect(() => {
    if (!catalog) {
      setResults([]);
      return;
    }

    if (!query.trim()) {
      setResults(catalog.tables);
      return;
    }

    const lowerQuery = query.toLowerCase();
    const filtered = catalog.tables.filter(table => {
      const nameMatch = table.name?.toLowerCase().includes(lowerQuery);
      const descMatch = table.description?.toLowerCase().includes(lowerQuery);
      const schemaMatch = table.schema?.toLowerCase().includes(lowerQuery);
      return nameMatch || descMatch || schemaMatch;
    });

    setResults(filtered);
  }, [catalog, query]);

  return results;
}

