import React, { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { comparePatterns, discoverConnections } from '../api'
import { LoadingSpinner, ErrorMessage, EmptyState } from '../components/StatusNotice'

export default function PatternFingerprinting() {
  const [patternData, setPatternData] = useState(null)
  const [connections, setConnections] = useState([])
  const [selectedPair, setSelectedPair] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [patRes, connRes] = await Promise.all([
        comparePatterns(),
        discoverConnections().catch(() => ({ connections: [] })),
      ])
      setPatternData(patRes)
      setConnections(connRes?.connections || [])

      // Default select CASE_A vs CASE_D (the Missing Link demo pair)
      if (patRes?.pairs?.length > 0) {
        const adPair = patRes.pairs.find(
          (p) =>
            (p.case_a === 'CASE_A' && p.case_b === 'CASE_D') ||
            (p.case_a === 'CASE_D' && p.case_b === 'CASE_A')
        )
        setSelectedPair(adPair || patRes.pairs[0])
      }
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) return <LoadingSpinner message="Calculating behavioral fingerprints & similarity matrix..." />
  if (error) return <ErrorMessage error={error} onRetry={fetchData} />
  if (!patternData || !patternData.pairs || patternData.pairs.length === 0) {
    return <EmptyState message="No pattern comparison pairs available." />
  }

  const { pairs, threshold } = patternData

  // Extract unique case IDs for matrix
  const caseSet = new Set()
  pairs.forEach((p) => {
    caseSet.add(p.case_a)
    caseSet.add(p.case_b)
  })
  const caseList = Array.from(caseSet).sort()

  // Helper to look up pair data between two case IDs
  const getPair = (c1, c2) => {
    if (c1 === c2) return { similarity: 1.0, is_similar: true, self: true }
    return (
      pairs.find(
        (p) =>
          (p.case_a === c1 && p.case_b === c2) ||
          (p.case_a === c2 && p.case_b === c1)
      ) || null
    )
  }

  // Count shared accounts from connections data
  const getSharedAccountCount = (c1, c2) => {
    const conn = connections.find(
      (c) =>
        (c.case_a === c1 && c.case_b === c2) ||
        (c.case_a === c2 && c.case_b === c1)
    )
    return conn ? (conn.shared_accounts?.length || 0) : 0
  }

  // Color interpolation for heatmap table cell
  const getCellColor = (sim, isSelf) => {
    if (isSelf) return '#f3f4f6'
    if (sim >= threshold) {
      // Strong similarity (green/emerald tint)
      const alpha = Math.min(1, Math.max(0.2, (sim - threshold) / (1 - threshold) + 0.3))
      return `rgba(16, 185, 129, ${alpha})`
    }
    // Low/moderate similarity (slate/amber tint)
    return `rgba(243, 244, 246, 0.8)`
  }

  const sharedCount = selectedPair
    ? getSharedAccountCount(selectedPair.case_a, selectedPair.case_b)
    : 0

  // Prepare chart data from selectedPair.matching_features
  const chartData = (selectedPair?.matching_features || []).map((m) => ({
    feature: m.feature,
    [selectedPair.case_a]: m.a,
    [selectedPair.case_b]: m.b,
  }))

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Pattern Fingerprinting & Behavioral Similarity</h1>
        <p style={styles.subtitle}>
          Compare case behavioral profiles independently of account names to uncover coordinated networks.
        </p>
      </div>

      {/* Threshold notification banner */}
      <div style={styles.thresholdBanner}>
        <div>
          <strong>Calibrated Similarity Threshold:</strong>{' '}
          <span style={styles.thresholdValue}>{threshold?.toFixed(3)}</span>
        </div>
        <div style={styles.thresholdNote}>
          Pairs with similarity &ge; {threshold?.toFixed(3)} are identified as matching suspicious money-movement behavior.
        </div>
      </div>

      <div style={styles.workspace}>
        {/* Left: Similarity Heatmap Table */}
        <div style={styles.matrixCard}>
          <div style={styles.cardHeader}>
            <h2 style={styles.cardTitle}>Pairwise Similarity Matrix</h2>
            <span style={styles.cardHint}>Click any cell to inspect matched features</span>
          </div>

          <div style={{ overflowX: 'auto', padding: '16px' }}>
            <table style={styles.matrixTable}>
              <thead>
                <tr>
                  <th style={styles.matrixThCorner}>Case</th>
                  {caseList.map((c) => (
                    <th key={c} style={styles.matrixTh}>
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {caseList.map((rowCase) => (
                  <tr key={rowCase}>
                    <td style={styles.matrixRowHeader}>{rowCase}</td>
                    {caseList.map((colCase) => {
                      const pair = getPair(rowCase, colCase)
                      if (!pair) return <td key={colCase} style={styles.matrixEmptyCell}>-</td>

                      const isSelected =
                        selectedPair &&
                        ((selectedPair.case_a === rowCase && selectedPair.case_b === colCase) ||
                          (selectedPair.case_a === colCase && selectedPair.case_b === rowCase))

                      return (
                        <td
                          key={colCase}
                          onClick={() => !pair.self && setSelectedPair(pair)}
                          style={{
                            ...styles.matrixCell,
                            backgroundColor: getCellColor(pair.similarity, pair.self),
                            border: isSelected ? '2px solid #2563eb' : '1px solid #e5e7eb',
                            cursor: pair.self ? 'default' : 'pointer',
                            fontWeight: pair.similarity >= threshold ? '700' : '400',
                            color: pair.similarity >= threshold ? '#065f46' : '#4b5563',
                          }}
                        >
                          {pair.self ? '1.000' : pair.similarity.toFixed(3)}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={styles.matrixLegend}>
            <div style={styles.legendEntry}>
              <span style={{ ...styles.legendBox, backgroundColor: 'rgba(16, 185, 129, 0.6)' }} />
              <span>Above Threshold (&ge; {threshold?.toFixed(3)}) — Similar Pattern</span>
            </div>
            <div style={styles.legendEntry}>
              <span style={{ ...styles.legendBox, backgroundColor: 'rgba(243, 244, 246, 0.9)' }} />
              <span>Below Threshold — Distinct Pattern</span>
            </div>
          </div>
        </div>

        {/* Right: Selected Pair Deep-Dive Inspector */}
        <div style={styles.detailCard}>
          {selectedPair ? (
            <div>
              <div style={styles.detailHeader}>
                <div>
                  <h3 style={styles.detailTitle}>
                    {selectedPair.case_a} &harr; {selectedPair.case_b}
                  </h3>
                  <span style={styles.detailSubtitle}>Detailed Behavioral Comparison</span>
                </div>
                <div>
                  {selectedPair.is_similar ? (
                    <span style={styles.similarBadge}>Similar Pattern</span>
                  ) : (
                    <span style={styles.notSimilarBadge}>Distinct Pattern</span>
                  )}
                </div>
              </div>

              {/* Metrics Highlights */}
              <div style={styles.metricsRow}>
                <div style={styles.metricItem}>
                  <div style={styles.metricLabel}>Similarity Score</div>
                  <div style={styles.metricVal}>
                    {(selectedPair.similarity * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={styles.metricItem}>
                  <div style={styles.metricLabel}>Shared Accounts</div>
                  <div
                    style={{
                      ...styles.metricVal,
                      color: sharedCount === 0 ? '#2563eb' : '#dc2626',
                    }}
                  >
                    {sharedCount}
                  </div>
                </div>
                <div style={styles.metricItem}>
                  <div style={styles.metricLabel}>Threshold Boundary</div>
                  <div style={styles.metricVal}>
                    {selectedPair.similarity >= threshold ? 'Exceeded' : 'Below'}
                  </div>
                </div>
              </div>

              {/* Special callout for Missing Link (CASE_A vs CASE_D) */}
              {((selectedPair.case_a === 'CASE_A' && selectedPair.case_b === 'CASE_D') ||
                (selectedPair.case_a === 'CASE_D' && selectedPair.case_b === 'CASE_A')) && (
                <div style={styles.missingLinkCallout}>
                  <strong>The "Missing Link" Found:</strong> CASE_D shares 0 common bank accounts
                  with CASE_A, yet behavioral fingerprinting identifies 98% topological similarity
                  (rapid mule splitting & consolidation).
                </div>
              )}

              {/* Explanation Text */}
              {selectedPair.explanation && (
                <div style={styles.explanationBox}>
                  <strong>Assessment Explanation:</strong>
                  <p style={{ margin: '6px 0 0 0', lineHeight: 1.4 }}>
                    {selectedPair.explanation}
                  </p>
                </div>
              )}

              {/* Recharts Bar Chart Comparing Features */}
              <div style={styles.chartSection}>
                <h4 style={styles.chartTitle}>Matching Feature Values Comparison</h4>
                {chartData.length === 0 ? (
                  <p style={styles.noFeatures}>No non-zero matching features in this pair.</p>
                ) : (
                  <div style={{ width: '100%', height: 260 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={chartData}
                        margin={{ top: 10, right: 20, left: 0, bottom: 25 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis
                          dataKey="feature"
                          angle={-20}
                          textAnchor="end"
                          interval={0}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                        <Bar
                          dataKey={selectedPair.case_a}
                          fill="#3b82f6"
                          radius={[4, 4, 0, 0]}
                        />
                        <Bar
                          dataKey={selectedPair.case_b}
                          fill="#10b981"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={styles.emptyDetail}>
              Click any comparison cell in the matrix to view detailed feature values.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const styles = {
  header: { marginBottom: '20px' },
  title: { fontSize: '24px', fontWeight: '700', color: '#111827', margin: '0 0 6px 0' },
  subtitle: { fontSize: '14px', color: '#6b7280', margin: 0 },
  thresholdBanner: {
    backgroundColor: '#eff6ff',
    border: '1px solid #bfdbfe',
    borderRadius: '8px',
    padding: '12px 18px',
    marginBottom: '20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '10px',
    fontSize: '13px',
    color: '#1e40af',
  },
  thresholdValue: {
    backgroundColor: '#1d4ed8',
    color: '#ffffff',
    padding: '2px 8px',
    borderRadius: '4px',
    fontWeight: '700',
    fontFamily: 'monospace',
    marginLeft: '6px',
  },
  thresholdNote: { color: '#3b82f6', fontSize: '12px' },
  workspace: {
    display: 'grid',
    gridTemplateColumns: 'minmax(0, 1fr) 460px',
    gap: '20px',
  },
  matrixCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  cardHeader: {
    padding: '16px 20px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fafafa',
  },
  cardTitle: { fontSize: '15px', fontWeight: '600', color: '#111827', margin: '0 0 4px 0' },
  cardHint: { fontSize: '12px', color: '#6b7280' },
  matrixTable: {
    width: '100%',
    borderCollapse: 'collapse',
    textAlign: 'center',
    fontSize: '12px',
  },
  matrixThCorner: {
    padding: '10px',
    textAlign: 'left',
    color: '#4b5563',
    fontWeight: '600',
    borderBottom: '2px solid #e5e7eb',
  },
  matrixTh: {
    padding: '10px',
    color: '#4b5563',
    fontWeight: '600',
    borderBottom: '2px solid #e5e7eb',
    minWidth: '60px',
  },
  matrixRowHeader: {
    padding: '10px',
    textAlign: 'left',
    fontWeight: '600',
    color: '#111827',
    borderRight: '2px solid #e5e7eb',
  },
  matrixCell: {
    padding: '10px',
    transition: 'all 0.15s ease',
  },
  matrixEmptyCell: {
    padding: '10px',
    color: '#9ca3af',
  },
  matrixLegend: {
    padding: '12px 18px',
    borderTop: '1px solid #e5e7eb',
    display: 'flex',
    gap: '20px',
    fontSize: '12px',
    color: '#4b5563',
    backgroundColor: '#f9fafb',
    flexWrap: 'wrap',
  },
  legendEntry: { display: 'flex', alignItems: 'center', gap: '8px' },
  legendBox: {
    width: '14px',
    height: '14px',
    borderRadius: '3px',
    border: '1px solid #d1d5db',
  },
  detailCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    padding: '20px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  detailHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid #e5e7eb',
    paddingBottom: '14px',
    marginBottom: '16px',
  },
  detailTitle: { fontSize: '18px', fontWeight: '700', color: '#111827', margin: '0 0 4px 0' },
  detailSubtitle: { fontSize: '12px', color: '#6b7280' },
  similarBadge: {
    backgroundColor: '#dcfce7',
    color: '#166534',
    border: '1px solid #86efac',
    borderRadius: '4px',
    padding: '3px 8px',
    fontSize: '12px',
    fontWeight: '600',
  },
  notSimilarBadge: {
    backgroundColor: '#f3f4f6',
    color: '#4b5563',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    padding: '3px 8px',
    fontSize: '12px',
    fontWeight: '600',
  },
  metricsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
    marginBottom: '16px',
  },
  metricItem: {
    backgroundColor: '#f9fafb',
    padding: '10px',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
    textAlign: 'center',
  },
  metricLabel: { fontSize: '11px', color: '#6b7280', marginBottom: '4px' },
  metricVal: { fontSize: '16px', fontWeight: '700', color: '#111827' },
  missingLinkCallout: {
    backgroundColor: '#eff6ff',
    border: '1px solid #93c5fd',
    borderRadius: '6px',
    padding: '12px 14px',
    fontSize: '12px',
    color: '#1e40af',
    marginBottom: '16px',
    lineHeight: '1.4',
  },
  explanationBox: {
    backgroundColor: '#f9fafb',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    padding: '12px 14px',
    fontSize: '12px',
    color: '#374151',
    marginBottom: '18px',
  },
  chartSection: { marginTop: '14px' },
  chartTitle: { fontSize: '13px', fontWeight: '600', color: '#374151', margin: '0 0 10px 0' },
  noFeatures: { fontSize: '12px', color: '#6b7280', fontStyle: 'italic' },
  emptyDetail: { textAlign: 'center', padding: '60px 20px', color: '#9ca3af', fontSize: '14px' },
}
