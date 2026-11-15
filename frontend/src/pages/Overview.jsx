import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOverview, getCases } from '../api'
import RiskBadge from '../components/RiskBadge'
import { LoadingSpinner, ErrorMessage, EmptyState } from '../components/StatusNotice'

export default function Overview() {
  const [overview, setOverview] = useState(null)
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [ovData, casesData] = await Promise.all([getOverview(), getCases()])
      setOverview(ovData)
      setCases(casesData)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) return <LoadingSpinner message="Loading investigation overview..." />
  if (error) return <ErrorMessage error={error} onRetry={fetchData} />
  if (!overview || cases.length === 0) return <EmptyState message="No case data currently available." />

  const cards = [
    { label: 'Reported Cases', value: overview.cases, icon: '📁' },
    { label: 'Tracked Accounts', value: overview.accounts, icon: '👥' },
    { label: 'Transactions', value: overview.transactions, icon: '💳' },
    { label: 'Shared Relationships', value: overview.relationships, icon: '🔗' },
    { label: 'Similar Behavioral Pairs', value: overview.similar_pairs, icon: '🧬' },
  ]

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Investigation Overview</h1>
        <p style={styles.subtitle}>
          Cross-case intelligence synthesis and priority queue for human investigation.
        </p>
      </div>

      <div style={styles.grid}>
        {cards.map((c, idx) => (
          <div key={idx} style={styles.card}>
            <div style={styles.cardIcon}>{c.icon}</div>
            <div style={styles.cardContent}>
              <div style={styles.cardValue}>{c.value}</div>
              <div style={styles.cardLabel}>{c.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={styles.tableCard}>
        <div style={styles.tableHeader}>
          <h2 style={styles.tableTitle}>Reported Cases (Ranked by Review Priority)</h2>
          <span style={styles.tableHint}>
            Priority scores reflect direct account links, behavioral patterns, and anomaly level.
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={styles.table}>
            <thead>
              <tr style={styles.thRow}>
                <th style={styles.th}>Rank</th>
                <th style={styles.th}>Case ID</th>
                <th style={styles.th}>Review Priority</th>
                <th style={styles.th}>Priority Score</th>
                <th style={styles.th}>Direct Link</th>
                <th style={styles.th}>Pattern Similarity</th>
                <th style={styles.th}>Anomaly Level</th>
                <th style={styles.th}>Investigation Action</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((item, idx) => (
                <tr key={item.case_id} style={styles.tr}>
                  <td style={styles.tdMuted}>#{idx + 1}</td>
                  <td style={styles.tdBold}>{item.case_id}</td>
                  <td style={styles.td}>
                    <RiskBadge level={item.risk_level} />
                  </td>
                  <td style={styles.tdScore}>
                    {(item.risk_score * 100).toFixed(1)}%
                    <div style={styles.miniBarContainer}>
                      <div
                        style={{
                          ...styles.miniBar,
                          width: `${Math.min(100, item.risk_score * 100)}%`,
                          backgroundColor:
                            item.risk_score >= 0.65
                              ? '#ef4444'
                              : item.risk_score >= 0.35
                              ? '#f59e0b'
                              : '#10b981',
                        }}
                      />
                    </div>
                  </td>
                  <td style={styles.td}>
                    {((item.components?.connection || 0) * 100).toFixed(0)}%
                  </td>
                  <td style={styles.td}>
                    {((item.components?.pattern_similarity || 0) * 100).toFixed(0)}%
                  </td>
                  <td style={styles.td}>
                    {((item.components?.anomaly || 0) * 100).toFixed(0)}%
                  </td>
                  <td style={styles.td}>
                    <Link
                      to={`/money-trail/${item.case_id}`}
                      style={styles.actionLink}
                    >
                      View Money Trail &rarr;
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

const styles = {
  header: {
    marginBottom: '24px',
  },
  title: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#111827',
    margin: '0 0 6px 0',
  },
  subtitle: {
    fontSize: '14px',
    color: '#6b7280',
    margin: 0,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
    gap: '16px',
    marginBottom: '28px',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    padding: '18px 20px',
    border: '1px solid #e5e7eb',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  cardIcon: {
    fontSize: '28px',
    backgroundColor: '#f3f4f6',
    borderRadius: '8px',
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardContent: {
    flex: 1,
  },
  cardValue: {
    fontSize: '22px',
    fontWeight: '700',
    color: '#111827',
    lineHeight: 1.1,
  },
  cardLabel: {
    fontSize: '12px',
    color: '#6b7280',
    marginTop: '4px',
    fontWeight: '500',
  },
  tableCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
    overflow: 'hidden',
  },
  tableHeader: {
    padding: '18px 20px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fafafa',
  },
  tableTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#111827',
    margin: '0 0 4px 0',
  },
  tableHint: {
    fontSize: '12px',
    color: '#6b7280',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    textAlign: 'left',
    fontSize: '13px',
  },
  thRow: {
    backgroundColor: '#f9fafb',
    borderBottom: '1px solid #e5e7eb',
  },
  th: {
    padding: '12px 16px',
    fontWeight: '600',
    color: '#4b5563',
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  tr: {
    borderBottom: '1px solid #f3f4f6',
    transition: 'background-color 0.15s ease',
  },
  td: {
    padding: '14px 16px',
    color: '#374151',
  },
  tdBold: {
    padding: '14px 16px',
    fontWeight: '600',
    color: '#111827',
  },
  tdMuted: {
    padding: '14px 16px',
    color: '#9ca3af',
    fontWeight: '500',
  },
  tdScore: {
    padding: '14px 16px',
    fontWeight: '600',
    color: '#111827',
  },
  miniBarContainer: {
    width: '100px',
    height: '6px',
    backgroundColor: '#e5e7eb',
    borderRadius: '3px',
    marginTop: '5px',
    overflow: 'hidden',
  },
  miniBar: {
    height: '100%',
    borderRadius: '3px',
  },
  actionLink: {
    color: '#2563eb',
    textDecoration: 'none',
    fontWeight: '600',
    fontSize: '12px',
  },
}
