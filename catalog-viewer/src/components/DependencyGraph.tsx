import { useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { GraphData, GraphNode } from '../types/catalog';
import { getLayerColor } from '../hooks';

interface DependencyGraphProps {
  graphData: GraphData;
  onNodeClick?: (node: GraphNode) => void;
  selectedNode?: string | null;
}

export default function DependencyGraph({ graphData, onNodeClick, selectedNode }: DependencyGraphProps) {
  const fgRef = useRef<any>();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    function handleResize() {
      setDimensions({
        width: window.innerWidth - 400, // Account for sidebar
        height: window.innerHeight - 100,
      });
    }

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div style={{ width: '100%', height: '100%', border: '1px solid #444', borderRadius: '4px' }}>
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        nodeLabel={(node: GraphNode) => `
          <div style="background: #1a1a1a; padding: 8px; border-radius: 4px; border: 1px solid #444;">
            <strong>${node.name}</strong><br/>
            <small>${node.schema}</small><br/>
            ${node.row_count ? `<small>${node.row_count.toLocaleString()} rows</small>` : ''}
          </div>
        `}
        nodeColor={(node: GraphNode) => getLayerColor(node.schema as string)}
        nodeVal={(node: GraphNode) => {
          // Size nodes based on row count
          if (node.row_count) {
            return Math.sqrt(node.row_count) / 100;
          }
          return 5;
        }}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
        linkColor={() => 'rgba(255, 255, 255, 0.3)'}
        onNodeClick={(node: GraphNode) => {
          if (onNodeClick) {
            onNodeClick(node);
          }
        }}
        nodeCanvasObject={(node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const label = node.name;
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = node.id === selectedNode ? '#fff' : '#ccc';
          ctx.fillText(label, node.x || 0, (node.y || 0) + 8);
        }}
        cooldownTicks={100}
        onEngineStop={() => {
          if (fgRef.current) {
            fgRef.current.zoomToFit(400, 20);
          }
        }}
      />
    </div>
  );
}

