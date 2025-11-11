import { useState, useMemo } from 'react';
import { Table } from '../types/catalog';
import SearchBar from './SearchBar';

interface TableBrowserProps {
  tables: Table[];
  onTableSelect: (table: Table) => void;
  selectedTable?: string | null;
}

export default function TableBrowser({ tables, onTableSelect, selectedTable }: TableBrowserProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [layerFilter, setLayerFilter] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'row_count' | 'schema'>('name');

  const filteredTables = useMemo(() => {
    let filtered = [...tables];

    // Apply layer filter
    if (layerFilter) {
      filtered = filtered.filter(t => t.schema === layerFilter);
    }

    // Apply search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(table => {
        const nameMatch = table.name?.toLowerCase().includes(query);
        const descMatch = table.description?.toLowerCase().includes(query);
        const schemaMatch = table.schema?.toLowerCase().includes(query);
        return nameMatch || descMatch || schemaMatch;
      });
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'row_count':
          const aCount = a.row_count || 0;
          const bCount = b.row_count || 0;
          return bCount - aCount;
        case 'schema':
          return (a.schema || '').localeCompare(b.schema || '');
        case 'name':
        default:
          return (a.name || '').localeCompare(b.name || '');
      }
    });

    return filtered;
  }, [tables, searchQuery, layerFilter, sortBy]);

  const layers = useMemo(() => {
    const unique = new Set(tables.map(t => t.schema).filter(Boolean));
    return Array.from(unique) as string[];
  }, [tables]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <SearchBar onSearch={setSearchQuery} placeholder="Search tables by name, schema, or description..." />
      
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <div>
          <label style={{ marginRight: '0.5rem', color: '#ccc' }}>Layer:</label>
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
            {layers.map(layer => (
              <option key={layer} value={layer}>{layer}</option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ marginRight: '0.5rem', color: '#ccc' }}>Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'name' | 'row_count' | 'schema')}
            style={{
              padding: '0.25rem 0.5rem',
              backgroundColor: '#1a1a1a',
              color: '#fff',
              border: '1px solid #444',
              borderRadius: '4px',
            }}
          >
            <option value="name">Name</option>
            <option value="row_count">Row Count</option>
            <option value="schema">Schema</option>
          </select>
        </div>

        <div style={{ color: '#ccc', marginLeft: 'auto', alignSelf: 'center' }}>
          {filteredTables.length} table{filteredTables.length !== 1 ? 's' : ''}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {filteredTables.map(table => (
          <div
            key={table.name}
            onClick={() => onTableSelect(table)}
            style={{
              padding: '1rem',
              marginBottom: '0.5rem',
              backgroundColor: selectedTable === table.name ? '#2a2a2a' : '#1a1a1a',
              border: selectedTable === table.name ? '2px solid #3b82f6' : '1px solid #444',
              borderRadius: '4px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              if (selectedTable !== table.name) {
                e.currentTarget.style.backgroundColor = '#222';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedTable !== table.name) {
                e.currentTarget.style.backgroundColor = '#1a1a1a';
              }
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div style={{ flex: 1 }}>
                <h3 style={{ margin: '0 0 0.5rem 0', color: '#fff' }}>{table.name}</h3>
                {table.description && (
                  <p style={{ margin: '0 0 0.5rem 0', color: '#aaa', fontSize: '0.9rem' }}>
                    {table.description}
                  </p>
                )}
                <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem', color: '#888' }}>
                  {table.schema && (
                    <span style={{
                      padding: '0.25rem 0.5rem',
                      backgroundColor: '#2a2a2a',
                      borderRadius: '4px',
                    }}>
                      {table.schema}
                    </span>
                  )}
                  {table.kind && (
                    <span style={{
                      padding: '0.25rem 0.5rem',
                      backgroundColor: '#2a2a2a',
                      borderRadius: '4px',
                    }}>
                      {table.kind}
                    </span>
                  )}
                  {table.row_count !== null && table.row_count !== undefined && (
                    <span>
                      {table.row_count.toLocaleString()} rows
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

