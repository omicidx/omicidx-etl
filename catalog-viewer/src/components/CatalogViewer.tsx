import { useState } from 'react';
import { useCatalog, useDependencyGraph } from '../hooks';
import { Table } from '../types/catalog';
import DependencyGraph from './DependencyGraph';
import TableBrowser from './TableBrowser';
import TableDetail from './TableDetail';

type ViewMode = 'browser' | 'graph';

export default function CatalogViewer() {
  const { catalog, loading, error } = useCatalog();
  const [viewMode, setViewMode] = useState<ViewMode>('browser');
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [layerFilter, setLayerFilter] = useState<string | null>(null);

  const graphData = useDependencyGraph(catalog, layerFilter);

  const selectedTableData = catalog?.tables.find(t => t.name === selectedTable) || null;

  const handleTableSelect = (table: Table) => {
    setSelectedTable(table.name);
  };

  const handleNodeClick = (node: { id: string }) => {
    setSelectedTable(node.id);
    setViewMode('browser');
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#fff' }}>
        Loading catalog...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#f00' }}>
        Error loading catalog: {error.message}
      </div>
    );
  }

  if (!catalog) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
        No catalog data available
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#1a1a1a' }}>
      <header style={{ padding: '1rem', borderBottom: '1px solid #444', backgroundColor: '#2a2a2a' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0, color: '#fff' }}>OmicIDX Data Catalog</h1>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div>
              <label style={{ marginRight: '0.5rem', color: '#ccc' }}>Filter by layer:</label>
              <select
                value={layerFilter || ''}
                onChange={(e) => setLayerFilter(e.target.value || null)}
                style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: '#1a1a1a',
                  color: '#fff',
                  border: '1px solid #444',
                  borderRadius: '4px',
                }}
              >
                <option value="">All</option>
                <option value="raw">Raw</option>
                <option value="bronze">Bronze</option>
                <option value="geometadb">GEOmetadb</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => setViewMode('browser')}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: viewMode === 'browser' ? '#3b82f6' : '#2a2a2a',
                  color: '#fff',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Browser
              </button>
              <button
                onClick={() => setViewMode('graph')}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: viewMode === 'graph' ? '#3b82f6' : '#2a2a2a',
                  color: '#fff',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Graph
              </button>
            </div>
          </div>
        </div>
        <div style={{ marginTop: '0.5rem', color: '#888', fontSize: '0.9rem' }}>
          {catalog.tables.length} tables • Generated: {new Date(catalog.generated_at).toLocaleString()}
        </div>
      </header>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {viewMode === 'browser' ? (
          <>
            <div style={{ width: '400px', borderRight: '1px solid #444', display: 'flex', flexDirection: 'column' }}>
              <div style={{ padding: '1rem', borderBottom: '1px solid #444' }}>
                <h2 style={{ margin: 0, color: '#fff', fontSize: '1.2rem' }}>Tables</h2>
              </div>
              <div style={{ flex: 1, overflow: 'hidden', padding: '1rem' }}>
                <TableBrowser
                  tables={catalog.tables}
                  onTableSelect={handleTableSelect}
                  selectedTable={selectedTable}
                />
              </div>
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <TableDetail table={selectedTableData} />
            </div>
          </>
        ) : (
          <div style={{ flex: 1, padding: '1rem', overflow: 'hidden' }}>
            <DependencyGraph
              graphData={graphData}
              onNodeClick={handleNodeClick}
              selectedNode={selectedTable}
            />
          </div>
        )}
      </div>
    </div>
  );
}

