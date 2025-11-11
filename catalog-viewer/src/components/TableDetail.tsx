import { Table } from '../types/catalog';
import ColumnStats from './ColumnStats';

interface TableDetailProps {
  table: Table | null;
}

export default function TableDetail({ table }: TableDetailProps) {
  if (!table) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
        Select a table to view details
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem', height: '100%', overflowY: 'auto' }}>
      <h2 style={{ marginTop: 0, color: '#fff' }}>{table.name}</h2>
      
      {table.description && (
        <p style={{ color: '#aaa', marginBottom: '1.5rem' }}>{table.description}</p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {table.schema && (
          <div>
            <strong style={{ color: '#aaa', display: 'block', marginBottom: '0.25rem' }}>Schema:</strong>
            <span style={{ color: '#fff' }}>{table.schema}</span>
          </div>
        )}
        
        {table.kind && (
          <div>
            <strong style={{ color: '#aaa', display: 'block', marginBottom: '0.25rem' }}>Kind:</strong>
            <span style={{ color: '#fff' }}>{table.kind}</span>
          </div>
        )}
        
        {table.grain && (
          <div>
            <strong style={{ color: '#aaa', display: 'block', marginBottom: '0.25rem' }}>Grain:</strong>
            <span style={{ color: '#fff' }}>
              {Array.isArray(table.grain) ? table.grain.join(', ') : table.grain}
            </span>
          </div>
        )}
        
        {table.cron && (
          <div>
            <strong style={{ color: '#aaa', display: 'block', marginBottom: '0.25rem' }}>Schedule:</strong>
            <span style={{ color: '#fff' }}>{table.cron}</span>
          </div>
        )}
        
        {table.row_count !== null && table.row_count !== undefined && (
          <div>
            <strong style={{ color: '#aaa', display: 'block', marginBottom: '0.25rem' }}>Row Count:</strong>
            <span style={{ color: '#fff' }}>{table.row_count.toLocaleString()}</span>
          </div>
        )}
      </div>

      {table.dependencies && table.dependencies.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ color: '#fff', marginBottom: '0.5rem' }}>Dependencies</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {table.dependencies.map(dep => (
              <span
                key={dep}
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: '#2a2a2a',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '0.9rem',
                }}
              >
                {dep}
              </span>
            ))}
          </div>
        </div>
      )}

      {table.dependents && table.dependents.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ color: '#fff', marginBottom: '0.5rem' }}>Dependents</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {table.dependents.map(dep => (
              <span
                key={dep}
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: '#2a2a2a',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '0.9rem',
                }}
              >
                {dep}
              </span>
            ))}
          </div>
        </div>
      )}

      {table.columns && table.columns.length > 0 && (
        <div>
          <h3 style={{ color: '#fff', marginBottom: '1rem' }}>Columns ({table.columns.length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {table.columns.map(column => (
              <div
                key={column.name}
                style={{
                  padding: '1rem',
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #444',
                  borderRadius: '4px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                  <div>
                    <strong style={{ color: '#fff', fontSize: '1.1rem' }}>{column.name}</strong>
                    <span style={{ color: '#888', marginLeft: '0.5rem' }}>{column.type}</span>
                    {column.nullable !== undefined && (
                      <span style={{ color: '#888', marginLeft: '0.5rem' }}>
                        {column.nullable ? '(nullable)' : '(not null)'}
                      </span>
                    )}
                  </div>
                </div>
                
                {column.description && (
                  <p style={{ color: '#aaa', margin: '0.5rem 0', fontSize: '0.9rem' }}>
                    {column.description}
                  </p>
                )}
                
                <ColumnStats column={column} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

