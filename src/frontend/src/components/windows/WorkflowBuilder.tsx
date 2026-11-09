/**
 * Workflow builder component for DAG-based task orchestration
 */
'use client';

import { useState } from 'react';

export interface WorkflowNode {
  id: string;
  name: string;
  type: 'start' | 'task' | 'condition' | 'end';
  x: number;
  y: number;
  inputs?: string[];
  outputs?: string[];
}

export interface WorkflowEdge {
  from: string;
  to: string;
  label?: string;
}

interface WorkflowBuilderProps {
  onClose?: () => void;
  onSave?: (workflow: { nodes: WorkflowNode[]; edges: WorkflowEdge[] }) => void;
}

export function WorkflowBuilder({ onClose, onSave }: WorkflowBuilderProps) {
  const [nodes, setNodes] = useState<WorkflowNode[]>([
    { id: 'start', name: 'Start', type: 'start', x: 50, y: 50 },
    { id: 'end', name: 'End', type: 'end', x: 450, y: 250 },
  ]);
  const [edges, setEdges] = useState<WorkflowEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [draggingNode, setDraggingNode] = useState<WorkflowNode | null>(null);
  const [newNodeType, setNewNodeType] = useState<'task' | 'condition'>('task');
  const [nodeNameInput, setNodeNameInput] = useState('');

  const addNode = () => {
    if (!nodeNameInput.trim()) return;

    const newNode: WorkflowNode = {
      id: `node-${Date.now()}`,
      name: nodeNameInput,
      type: newNodeType,
      x: 200 + Math.random() * 100,
      y: 150 + Math.random() * 100,
    };

    setNodes([...nodes, newNode]);
    setNodeNameInput('');
  };

  const updateNode = (id: string, updates: Partial<WorkflowNode>) => {
    setNodes(nodes.map((n) => (n.id === id ? { ...n, ...updates } : n)));
    if (selectedNode?.id === id) {
      setSelectedNode({ ...selectedNode, ...updates });
    }
  };

  const deleteNode = (id: string) => {
    if (id === 'start' || id === 'end') return; // Can't delete start/end

    setNodes(nodes.filter((n) => n.id !== id));
    setEdges(edges.filter((e) => e.from !== id && e.to !== id));
    setSelectedNode(null);
  };

  const addEdge = (fromId: string, toId: string) => {
    if (fromId === toId) return;

    const exists = edges.some((e) => e.from === fromId && e.to === toId);
    if (!exists) {
      setEdges([...edges, { from: fromId, to: toId }]);
    }
  };

  const handleNodeMouseDown = (node: WorkflowNode) => {
    setDraggingNode(node);
    setSelectedNode(node);
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!draggingNode) return;

    const svg = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - svg.left;
    const y = e.clientY - svg.top;

    updateNode(draggingNode.id, { x, y });
  };

  const handleCanvasMouseUp = () => {
    setDraggingNode(null);
  };

  const nodeColor = (type: string) => {
    switch (type) {
      case 'start':
        return 'fill-green-600';
      case 'end':
        return 'fill-red-600';
      case 'task':
        return 'fill-blue-600';
      case 'condition':
        return 'fill-yellow-600';
      default:
        return 'fill-gray-600';
    }
  };

  const handleSave = () => {
    if (onSave) {
      onSave({ nodes, edges });
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-100 border border-gray-700 rounded overflow-hidden">
      {/* Header */}
      <div className="p-3 border-b border-gray-700 bg-gray-900 flex justify-between items-center">
        <h3 className="font-semibold">Workflow Builder</h3>
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="text-xs px-3 py-1 rounded bg-sky-600 hover:bg-sky-700 text-white transition"
          >
            Save
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-200 text-lg leading-none"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-48 border-r border-gray-700 bg-gray-900 p-3 overflow-y-auto space-y-3">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Add Node</label>
            <div className="space-y-2">
              <input
                type="text"
                value={nodeNameInput}
                onChange={(e) => setNodeNameInput(e.target.value)}
                placeholder="Node name..."
                className="w-full bg-gray-800 text-gray-100 border border-gray-700 rounded px-2 py-1 text-xs"
                onKeyPress={(e) => e.key === 'Enter' && addNode()}
              />

              <div>
                <label className="text-xs text-gray-400">Type:</label>
                <select
                  value={newNodeType}
                  onChange={(e) => setNewNodeType(e.target.value as 'task' | 'condition')}
                  className="w-full bg-gray-800 text-gray-100 border border-gray-700 rounded px-2 py-1 text-xs"
                >
                  <option value="task">Task</option>
                  <option value="condition">Condition</option>
                </select>
              </div>

              <button
                onClick={addNode}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs"
              >
                Add Node
              </button>
            </div>
          </div>

          <div className="border-t border-gray-700 pt-3">
            <h4 className="text-xs font-semibold text-gray-400 mb-2">Nodes ({nodes.length})</h4>
            <div className="space-y-1">
              {nodes.map((node) => (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`w-full text-left px-2 py-1 rounded text-xs truncate transition-colors ${
                    selectedNode?.id === node.id
                      ? 'bg-sky-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  {node.name}
                </button>
              ))}
            </div>
          </div>

          {selectedNode && selectedNode.id !== 'start' && selectedNode.id !== 'end' && (
            <button
              onClick={() => deleteNode(selectedNode.id)}
              className="w-full bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs"
            >
              Delete Selected
            </button>
          )}
        </div>

        {/* Canvas */}
        <div className="flex-1 overflow-auto bg-gray-950 relative">
          <svg
            className="w-full h-full cursor-grab active:cursor-grabbing"
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
            onMouseLeave={handleCanvasMouseUp}
          >
            {/* Edges */}
            <g>
              {edges.map((edge) => {
                const fromNode = nodes.find((n) => n.id === edge.from);
                const toNode = nodes.find((n) => n.id === edge.to);
                if (!fromNode || !toNode) return null;

                return (
                  <line
                    key={`${edge.from}-${edge.to}`}
                    x1={fromNode.x}
                    y1={fromNode.y}
                    x2={toNode.x}
                    y2={toNode.y}
                    stroke="#555"
                    strokeWidth="2"
                    markerEnd="url(#arrowhead)"
                  />
                );
              })}

              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="10"
                  refX="9"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" fill="#555" />
                </marker>
              </defs>
            </g>

            {/* Nodes */}
            <g>
              {nodes.map((node) => (
                <g key={node.id}>
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r="30"
                    className={`${nodeColor(node.type)} cursor-pointer opacity-80 hover:opacity-100 transition`}
                    onMouseDown={() => handleNodeMouseDown(node)}
                  />
                  <text
                    x={node.x}
                    y={node.y + 5}
                    textAnchor="middle"
                    className="text-xs fill-white pointer-events-none select-none"
                  >
                    {node.name.substring(0, 8)}
                  </text>

                  {/* Connection points */}
                  {selectedNode?.id === node.id && (
                    <>
                      {/* Right connection for linking */}
                      <circle
                        cx={node.x + 30}
                        cy={node.y}
                        r="5"
                        fill="#4f9cff"
                        className="cursor-pointer hover:r-6"
                        title="Drag to connect"
                      />
                    </>
                  )}
                </g>
              ))}
            </g>
          </svg>
        </div>
      </div>

      {/* Info Bar */}
      <div className="px-3 py-2 border-t border-gray-700 bg-gray-900 text-xs text-gray-500 flex justify-between">
        <span>Nodes: {nodes.length}</span>
        <span>Edges: {edges.length}</span>
        {selectedNode && <span>Selected: {selectedNode.name}</span>}
      </div>
    </div>
  );
}
