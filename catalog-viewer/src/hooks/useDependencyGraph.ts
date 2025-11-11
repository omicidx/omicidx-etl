import { useMemo } from 'react';
import { Catalog, GraphNode, GraphLink, GraphData } from '../types/catalog';

export function useDependencyGraph(catalog: Catalog | null, layerFilter?: string | null): GraphData {
  return useMemo(() => {
    if (!catalog) {
      return { nodes: [], links: [] };
    }

    const nodes: GraphNode[] = [];
    const links: GraphLink[] = [];
    const nodeMap = new Map<string, GraphNode>();

    // Create nodes
    for (const table of catalog.tables) {
      // Apply layer filter if specified
      if (layerFilter && table.schema !== layerFilter) {
        continue;
      }

      const node: GraphNode = {
        id: table.name,
        name: table.table_name || table.name.split('.').pop() || table.name,
        schema: table.schema || 'unknown',
        kind: table.kind,
        row_count: table.row_count,
        dependencies: table.dependencies,
        dependents: table.dependents,
      };

      nodes.push(node);
      nodeMap.set(table.name, node);
    }

    // Create links
    for (const table of catalog.tables) {
      if (layerFilter && table.schema !== layerFilter) {
        continue;
      }

      const sourceId = table.name;
      if (!nodeMap.has(sourceId)) {
        continue;
      }

      // Add links for dependencies
      if (table.dependencies) {
        for (const dep of table.dependencies) {
          // Only include links to nodes that exist in our filtered set
          if (nodeMap.has(dep)) {
            links.push({
              source: dep,
              target: sourceId,
            });
          }
        }
      }
    }

    return { nodes, links };
  }, [catalog, layerFilter]);
}

export function getLayerColor(schema: string): string {
  switch (schema) {
    case 'raw':
      return '#3b82f6'; // blue
    case 'bronze':
      return '#10b981'; // green
    case 'geometadb':
      return '#f59e0b'; // amber
    default:
      return '#6b7280'; // gray
  }
}

