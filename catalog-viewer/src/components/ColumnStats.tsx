import { Column } from '../types/catalog';

interface ColumnStatsProps {
  column: Column;
}

export default function ColumnStats({ column }: ColumnStatsProps) {
  const stats = column.statistics || {
    null_count: column.null_count,
    null_percentage: column.null_percentage,
    distinct_count: column.distinct_count,
    min: column.min,
    max: column.max,
    mean: column.mean,
    std: column.std,
    q25: column.q25,
    q50: column.q50,
    q75: column.q75,
  };

  const hasStats = Object.values(stats).some(v => v !== null && v !== undefined);

  if (!hasStats) {
    return <span style={{ color: '#888', fontSize: '0.9rem' }}>No statistics available</span>;
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem', fontSize: '0.85rem' }}>
      {stats.null_count !== null && stats.null_count !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Nulls:</strong>{' '}
          <span style={{ color: '#fff' }}>
            {stats.null_count.toLocaleString()}
            {stats.null_percentage !== null && stats.null_percentage !== undefined && (
              <span style={{ color: '#888' }}> ({stats.null_percentage.toFixed(1)}%)</span>
            )}
          </span>
        </div>
      )}
      
      {stats.distinct_count !== null && stats.distinct_count !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Distinct:</strong>{' '}
          <span style={{ color: '#fff' }}>{stats.distinct_count.toLocaleString()}</span>
        </div>
      )}
      
      {stats.min !== null && stats.min !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Min:</strong>{' '}
          <span style={{ color: '#fff' }}>{typeof stats.min === 'number' ? stats.min.toLocaleString() : stats.min}</span>
        </div>
      )}
      
      {stats.max !== null && stats.max !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Max:</strong>{' '}
          <span style={{ color: '#fff' }}>{typeof stats.max === 'number' ? stats.max.toLocaleString() : stats.max}</span>
        </div>
      )}
      
      {stats.mean !== null && stats.mean !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Mean:</strong>{' '}
          <span style={{ color: '#fff' }}>{stats.mean.toFixed(2)}</span>
        </div>
      )}
      
      {stats.std !== null && stats.std !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Std Dev:</strong>{' '}
          <span style={{ color: '#fff' }}>{stats.std.toFixed(2)}</span>
        </div>
      )}
      
      {stats.q25 !== null && stats.q25 !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Q25:</strong>{' '}
          <span style={{ color: '#fff' }}>{stats.q25.toLocaleString()}</span>
        </div>
      )}
      
      {stats.q50 !== null && stats.q50 !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Median:</strong>{' '}
          <span style={{ color: '#fff' }}>{stats.q50.toLocaleString()}</span>
        </div>
      )}
      
      {stats.q75 !== null && stats.q75 !== undefined && (
        <div>
          <strong style={{ color: '#aaa' }}>Q75:</strong>{' '}
          <span style={{ color: '#fff' }}>{stats.q75.toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}

