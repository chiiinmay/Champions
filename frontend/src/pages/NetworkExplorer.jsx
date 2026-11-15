import React, { useEffect, useState, useRef } from 'react'
import cytoscape from 'cytoscape'
import { getGraph, discoverConnections, getCases } from '../api'
import { LoadingSpinner, ErrorMessage, EmptyState } from '../components/StatusNotice'

const BANK_COLORS = {
  'Bank Alpha': '#2563eb', // blue
  'Bank Beta': '#059669', // green
  'Bank Gamma': '#d97706', // amber
}

export default function NetworkExplorer() {
  const [availableCases, setAvailableCases] = useState(['CASE_A', 'CASE_B', 'CASE_C', 'CASE_D', 'CASE_E', 'CASE_F'])
  const [selectedCases, setSelectedCases] = useState(['CASE_A', 'CASE_B', 'CASE_C'])
  const [graphData, setGraphData] = useState(null)
  const [connectionData, setConnectionData] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const cyRef = useRef(null)
  const cyInstance = useRef(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [connRes, casesRes] = await Promise.all([
        discoverConnections(),
        getCases().catch(() => []),
      ])
      setConnectionData(connRes)
      if (casesRes && casesRes.length > 0) {
        setAvailableCases(casesRes.map((c) => c.case_id))
      }
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  const loadGraph = async () => {
    if (selectedCases.length === 0) {
      setGraphData({ nodes: [], edges: [] })
      return
    }
    try {
      const gData = await getGraph(selectedCases)
      setGraphData(gData)
    } catch (err) {
      setError(err)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    loadGraph()
  }, [selectedCases])

  // Initialize and update Cytoscape
  useEffect(() => {
    if (!cyRef.current || !graphData) return

    if (cyInstance.current) {
      cyInstance.current.destroy()
    }

    const elements = [
      ...graphData.nodes.map((n) => ({
        group: 'nodes',
        data: n.data,
      })),
      ...graphData.edges.map((e) => ({
        group: 'edges',
        data: e.data,
      })),
    ]

    const cy = cytoscape({
      container: cyRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'font-size': '11px',
            'font-weight': '600',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'background-color': (ele) => BANK_COLORS[ele.data('bank')] || '#6b7280',
            color: '#1f2937',
            width: 30,
            height: 30,
          },
        },
        {
          selector: 'node[?shared]',
          style: {
            shape: 'diamond',
            width: 42,
            height: 42,
            'border-width': 3,
            'border-color': '#dc2626',
            'border-opacity': 1,
            'background-color': (ele) => BANK_COLORS[ele.data('bank')] || '#ef4444',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#9ca3af',
            'line-color': '#cbd5e1',
            label: 'data(label)',
            'font-size': '9px',
            'text-rotation': 'autorotate',
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.8,
            'text-background-padding': '2px',
            color: '#475569',
          },
        },
        {
          selector: ':selected',
          style: {
            'border-width': 3,
            'border-color': '#2563eb',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 30,
        nodeRepulsion: 8000,
        idealEdgeLength: 80,
      },
    })

    cy.on('tap', 'node', (evt) => {
      const nodeData = evt.target.data()
      // Find which cases touch this account
      const connectedEdges = evt.target.connectedEdges()
      const casesTouching = new Set()
      connectedEdges.forEach((e) => {
        if (e.data('case_id')) casesTouching.add(e.data('case_id'))
      })

      setSelectedNode({
        account: nodeData.id,
        bank: nodeData.bank,
        shared: nodeData.shared,
        cases: Array.from(casesTouching),
      })
    })

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null)
      }
    })

    cyInstance.current = cy

    return () => {
      if (cyInstance.current) {
        cyInstance.current.destroy()
        cyInstance.current = null
      }
    }
  }, [graphData])

  const toggleCase = (cid) => {
    if (selectedCases.includes(cid)) {
      setSelectedCases(selectedCases.filter((c) => c !== cid))
    } else {
      setSelectedCases([...selectedCases, cid])
    }
  }

  if (loading) return <LoadingSpinner message="Loading network topology..." />
  if (error) return <ErrorMessage error={error} onRetry={fetchData} />

  // Filter connections relevant to currently selected cases
  const visibleConnections = (connectionData?.connections || []).filter(
    (c) => selectedCases.includes(c.case_a) && selectedCases.includes(c.case_b)
  )

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Network Explorer</h1>
        <p style={styles.subtitle}>
          Multi-bank transaction graph highlighting shared intermediaries, beneficiaries, and transaction flow.
        </p>
      </div>

      {/* Case Filter Selector */}
      <div style={styles.filterCard}>
        <div style={styles.filterLabel}>
          <strong>Selected Reported Cases:</strong>
          <span style={{ fontSize: '12px', color: '#6b7280', marginLeft: '8px' }}>
            (Toggle to compare multi-bank case topologies)
          </span>
        </div>
        <div style={styles.badgeGroup}>
          {availableCases.map((cid) => {
            const isSelected = selectedCases.includes(cid)
            return (
              <button
                key={cid}
                type="button"
                onClick={() => toggleCase(cid)}
                style={{
                  ...styles.caseBtn,
                  backgroundColor: isSelected ? '#2563eb' : '#f3f4f6',
                  color: isSelected ? '#ffffff' : '#374151',
                  borderColor: isSelected ? '#1d4ed8' : '#d1d5db',
                }}
              >
                {cid} {isSelected ? '✓' : '+'}
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div style={styles.workspace}>
        {/* Left: Cytoscape Graph Canvas */}
        <div style={styles.graphContainer}>
          <div style={styles.graphToolbar}>
            <span style={styles.graphTitle}>
              Graph Topology ({graphData?.nodes?.length || 0} nodes,{' '}
              {graphData?.edges?.length || 0} edges)
            </span>

            {/* Legend */}
            <div style={styles.legend}>
              <div style={styles.legendItem}>
                <span style={{ ...styles.legendDot, backgroundColor: '#2563eb' }} />
                <span>Bank Alpha</span>
              </div>
              <div style={styles.legendItem}>
                <span style={{ ...styles.legendDot, backgroundColor: '#059669' }} />
                <span>Bank Beta</span>
              </div>
              <div style={styles.legendItem}>
                <span style={{ ...styles.legendDot, backgroundColor: '#d97706' }} />
                <span>Bank Gamma</span>
              </div>
              <div style={styles.legendItem}>
                <span style={styles.legendDiamond} />
                <span>Shared Account</span>
              </div>
            </div>
          </div>

          <div ref={cyRef} style={styles.cyCanvas} />

          {/* Node Detail Popup */}
          {selectedNode && (
            <div style={styles.nodeInspector}>
              <div style={styles.nodeInspectorHeader}>
                <strong>Account Inspection: {selectedNode.account}</strong>
                <button
                  type="button"
                  onClick={() => setSelectedNode(null)}
                  style={styles.closeBtn}
                >
                  ✕
                </button>
              </div>
              <div style={styles.nodeInspectorBody}>
                <div>
                  <strong>Institution:</strong> {selectedNode.bank || 'Unknown'}
                </div>
                <div>
                  <strong>Role Type:</strong>{' '}
                  {selectedNode.shared ? (
                    <span style={{ color: '#dc2626', fontWeight: '700' }}>
                      Shared Cross-Case Account
                    </span>
                  ) : (
                    'Case-Local Account'
                  )}
                </div>
                <div>
                  <strong>Associated Cases:</strong>{' '}
                  {selectedNode.cases.length > 0
                    ? selectedNode.cases.join(', ')
                    : 'Currently displayed active transfers'}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Side Panel with Connection Explanations & Hub Warning */}
        <div style={styles.sidePanel}>
          <div style={styles.panelCard}>
            <h3 style={styles.panelTitle}>
              Cross-Case Shared Connections ({visibleConnections.length})
            </h3>
            {visibleConnections.length === 0 ? (
              <p style={styles.panelEmpty}>
                No direct accounts shared between the currently selected cases.
              </p>
            ) : (
              <div style={styles.connectionsList}>
                {visibleConnections.map((conn, idx) => (
                  <div key={idx} style={styles.connItem}>
                    <div style={styles.connHeader}>
                      <span style={styles.connPair}>
                        {conn.case_a} &harr; {conn.case_b}
                      </span>
                    </div>
                    <p style={styles.connExplanation}>{conn.explanation}</p>
                    <div style={styles.evidenceSection}>
                      <span style={styles.evidenceTitle}>
                        Supporting Transactions ({conn.supporting_transactions?.length || 0}):
                      </span>
                      <div style={styles.txTagGroup}>
                        {(conn.supporting_transactions || []).map((txId) => (
                          <span key={txId} style={styles.txTag}>
                            {txId}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Hub Accounts Filtered Card */}
          <div style={styles.hubCard}>
            <h3 style={styles.hubTitle}>Filtered High-Degree Hub Accounts</h3>
            <p style={styles.hubDescription}>
              Accounts exceeding degree threshold 25 (e.g. utility bill payment hubs) are
              filtered to prevent false cross-case linkage.
            </p>
            <div style={styles.hubList}>
              {(connectionData?.ignored_hub_accounts || []).map((hub, idx) => (
                <div key={idx} style={styles.hubItem}>
                  <strong>Account {hub.account}</strong>: Total degree {hub.total_degree} (High-volume infrastructure account)
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  header: { marginBottom: '20px' },
  title: { fontSize: '24px', fontWeight: '700', color: '#111827', margin: '0 0 6px 0' },
  subtitle: { fontSize: '14px', color: '#6b7280', margin: 0 },
  filterCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    padding: '14px 18px',
    border: '1px solid #e5e7eb',
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    flexWrap: 'wrap',
  },
  filterLabel: { fontSize: '13px', color: '#374151' },
  badgeGroup: { display: 'flex', gap: '8px', flexWrap: 'wrap' },
  caseBtn: {
    padding: '6px 14px',
    borderRadius: '6px',
    border: '1px solid',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  workspace: {
    display: 'grid',
    gridTemplateColumns: 'minmax(0, 1fr) 380px',
    gap: '20px',
  },
  graphContainer: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    position: 'relative',
    overflow: 'hidden',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  graphToolbar: {
    padding: '12px 18px',
    borderBottom: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
    flexWrap: 'wrap',
    gap: '12px',
  },
  graphTitle: { fontSize: '13px', fontWeight: '600', color: '#374151' },
  legend: { display: 'flex', gap: '14px', alignItems: 'center', fontSize: '12px', color: '#4b5563' },
  legendItem: { display: 'flex', alignItems: 'center', gap: '6px' },
  legendDot: { width: '10px', height: '10px', borderRadius: '50%' },
  legendDiamond: {
    width: '10px',
    height: '10px',
    backgroundColor: '#ef4444',
    transform: 'rotate(45deg)',
    display: 'inline-flex',
    border: '1px solid #b91c1c',
  },
  cyCanvas: {
    width: '100%',
    height: '560px',
    backgroundColor: '#fafafa',
  },
  nodeInspector: {
    position: 'absolute',
    bottom: '16px',
    left: '16px',
    backgroundColor: '#ffffff',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    padding: '14px 16px',
    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
    zIndex: 10,
    width: '280px',
    fontSize: '12px',
  },
  nodeInspectorHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
    borderBottom: '1px solid #f3f4f6',
    paddingBottom: '6px',
    color: '#111827',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: '#9ca3af',
    fontSize: '14px',
  },
  nodeInspectorBody: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    color: '#4b5563',
  },
  sidePanel: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  panelCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    padding: '18px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  panelTitle: {
    fontSize: '15px',
    fontWeight: '600',
    color: '#111827',
    margin: '0 0 12px 0',
  },
  panelEmpty: {
    fontSize: '13px',
    color: '#6b7280',
    fontStyle: 'italic',
    margin: 0,
  },
  connectionsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
    maxHeight: '360px',
    overflowY: 'auto',
  },
  connItem: {
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
  },
  connHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '6px',
  },
  connPair: {
    fontWeight: '700',
    color: '#1e40af',
    fontSize: '13px',
  },
  connExplanation: {
    fontSize: '12px',
    color: '#374151',
    margin: '0 0 8px 0',
    lineHeight: '1.4',
  },
  evidenceSection: {
    fontSize: '11px',
    color: '#6b7280',
  },
  evidenceTitle: {
    fontWeight: '600',
    display: 'flex',
    marginBottom: '4px',
  },
  txTagGroup: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
  },
  txTag: {
    backgroundColor: '#e0e7ff',
    color: '#3730a3',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '10px',
    fontWeight: '600',
  },
  hubCard: {
    backgroundColor: '#fffbeb',
    borderRadius: '8px',
    border: '1px solid #fde68a',
    padding: '16px',
  },
  hubTitle: {
    fontSize: '13px',
    fontWeight: '700',
    color: '#92400e',
    margin: '0 0 6px 0',
  },
  hubDescription: {
    fontSize: '12px',
    color: '#78350f',
    margin: '0 0 10px 0',
    lineHeight: '1.4',
  },
  hubList: {
    fontSize: '12px',
    color: '#92400e',
  },
  hubItem: {
    backgroundColor: '#ffffff',
    padding: '6px 10px',
    borderRadius: '4px',
    border: '1px solid #fef3c7',
  },
}
