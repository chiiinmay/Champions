import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getMoneyTrail, getCases } from '../api'
import { LoadingSpinner, ErrorMessage, EmptyState } from '../components/StatusNotice'

export default function MoneyTrail() {
  const { caseId: routeCaseId } = useParams()
  const navigate = useNavigate()

  const [availableCases, setAvailableCases] = useState(['CASE_A', 'CASE_B', 'CASE_C', 'CASE_D', 'CASE_E', 'CASE_F'])
  const [selectedCase, setSelectedCase] = useState(routeCaseId || 'CASE_A')
  const [trailData, setTrailData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getCases()
      .then((cases) => {
        if (cases && cases.length > 0) {
          setAvailableCases(cases.map((c) => c.case_id))
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (routeCaseId && routeCaseId !== selectedCase) {
      setSelectedCase(routeCaseId)
    }
  }, [routeCaseId])

  const loadTrail = async (cid) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getMoneyTrail(cid)
      setTrailData(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTrail(selectedCase)
  }, [selectedCase])

  const handleSelectCase = (cid) => {
    setSelectedCase(cid)
    navigate(`/money-trail/${cid}`)
  }

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Money Trail & Fund Flow Reconstruction</h1>
        <p style={styles.subtitle}>
          Chronological transfer ledger, multi-hop time-respecting paths, splitting, and consolidation analysis.
        </p>
      </div>

      {/* Case Selector Bar */}
      <div style={styles.selectorBar}>
        <span style={styles.selectorLabel}>Select Reported Case:</span>
        <div style={styles.caseButtons}>
          {availableCases.map((cid) => (
            <button
              key={cid}
              type="button"
              onClick={() => handleSelectCase(cid)}
              style={{
                ...styles.caseBtn,
                backgroundColor: selectedCase === cid ? '#2563eb' : '#f3f4f6',
                color: selectedCase === cid ? '#ffffff' : '#374151',
                borderColor: selectedCase === cid ? '#1d4ed8' : '#d1d5db',
              }}
            >
              {cid}
            </button>
          ))}
        </div>
      </div>

      {loading && <LoadingSpinner message={`Reconstructing money trail for ${selectedCase}...`} />}
      {error && <ErrorMessage error={error} onRetry={() => loadTrail(selectedCase)} />}

      {!loading && !error && trailData && (
        <div style={styles.contentLayout}>
          {/* Top Cards: Splitting & Consolidation Alerts */}
          <div style={styles.summaryRow}>
            {/* Splitting Detected */}
            <div style={styles.patternCard}>
              <div style={styles.patternHeader}>
                <span style={styles.patternIcon}>⚡</span>
                <h3 style={styles.patternTitle}>
                  Mule Splitting Detected ({trailData.splits?.length || 0})
                </h3>
              </div>
              {trailData.splits?.length > 0 ? (
                trailData.splits.map((s, idx) => (
                  <div key={idx} style={styles.splitItem}>
                    <div style={{ fontWeight: '600', color: '#111827' }}>
                      Account {s.account} &rarr; Fans out to {s.targets?.length} accounts
                    </div>
                    <div style={styles.detailText}>
                      Total Split Amount: ₹{s.total?.toLocaleString('en-IN')}
                    </div>
                    <div style={styles.targetList}>
                      Targets: {s.targets?.join(', ')}
                    </div>
                  </div>
                ))
              ) : (
                <p style={styles.muted}>No rapid mule fund splitting detected in this case.</p>
              )}
            </div>

            {/* Consolidation Detected */}
            <div style={styles.patternCard}>
              <div style={styles.patternHeader}>
                <span style={styles.patternIcon}>🎯</span>
                <h3 style={styles.patternTitle}>
                  Cash-Out Consolidation ({trailData.consolidations?.length || 0})
                </h3>
              </div>
              {trailData.consolidations?.length > 0 ? (
                trailData.consolidations.map((c, idx) => (
                  <div key={idx} style={styles.splitItem}>
                    <div style={{ fontWeight: '600', color: '#111827' }}>
                      Account {c.account} &larr; Receives from {c.sources?.length} sources
                    </div>
                    <div style={styles.detailText}>
                      Total Consolidated: ₹{c.total?.toLocaleString('en-IN')}
                    </div>
                    <div style={styles.targetList}>
                      Sources: {c.sources?.join(', ')}
                    </div>
                  </div>
                ))
              ) : (
                <p style={styles.muted}>No rapid terminal consolidation detected in this case.</p>
              )}
            </div>
          </div>

          {/* Time-Respecting Paths Section */}
          <div style={styles.sectionCard}>
            <div style={styles.sectionHeader}>
              <h3 style={styles.sectionTitle}>
                Time-Respecting Money Paths ({trailData.paths?.length || 0})
              </h3>
              <span style={styles.sectionHint}>
                Causal transfer chains where each hop strictly occurs after the preceding transfer.
              </span>
            </div>
            {trailData.paths?.length === 0 ? (
              <p style={{ padding: '20px', color: '#6b7280', margin: 0 }}>
                No multi-hop paths found.
              </p>
            ) : (
              <div style={styles.pathsList}>
                {trailData.paths.map((p, idx) => (
                  <div key={idx} style={styles.pathItem}>
                    <div style={styles.pathMeta}>
                      <span style={styles.pathIdx}>Path #{idx + 1}</span>
                      <span>
                        Entering: <strong>₹{p.amount_entering?.toLocaleString('en-IN')}</strong>
                      </span>
                      <span>&rarr;</span>
                      <span>
                        Leaving: <strong>₹{p.amount_leaving?.toLocaleString('en-IN')}</strong>
                      </span>
                      <span style={styles.pathDuration}>
                        Duration: {p.duration_min} mins
                      </span>
                    </div>
                    <div style={styles.pathChain}>
                      {p.accounts.map((acct, aIdx) => (
                        <React.Fragment key={aIdx}>
                          <span style={styles.pathNode}>{acct}</span>
                          {aIdx < p.accounts.length - 1 && (
                            <span style={styles.pathArrow}>&rarr;</span>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Chronological Transaction Table */}
          <div style={styles.sectionCard}>
            <div style={styles.sectionHeader}>
              <h3 style={styles.sectionTitle}>
                Chronological Transaction Ledger ({trailData.trail?.length || 0})
              </h3>
              <span style={styles.sectionHint}>Time-ordered sequence of fund transfers</span>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.thRow}>
                    <th style={styles.th}>Transaction ID</th>
                    <th style={styles.th}>Timestamp</th>
                    <th style={styles.th}>Origin Account</th>
                    <th style={styles.th}>Sender Bank</th>
                    <th style={styles.th}>Destination Account</th>
                    <th style={styles.th}>Receiver Bank</th>
                    <th style={{ ...styles.th, textAlign: 'right' }}>Amount (INR)</th>
                  </tr>
                </thead>
                <tbody>
                  {(trailData.trail || []).map((tx) => (
                    <tr key={tx.transaction_id} style={styles.tr}>
                      <td style={styles.tdId}>{tx.transaction_id}</td>
                      <td style={styles.td}>{tx.time?.replace('T', ' ')}</td>
                      <td style={styles.tdBold}>{tx.from}</td>
                      <td style={styles.tdMuted}>{tx.from_bank}</td>
                      <td style={styles.tdBold}>{tx.to}</td>
                      <td style={styles.tdMuted}>{tx.to_bank}</td>
                      <td style={styles.tdAmount}>
                        ₹{Number(tx.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const styles = {
  header: { marginBottom: '20px' },
  title: { fontSize: '24px', fontWeight: '700', color: '#111827', margin: '0 0 6px 0' },
  subtitle: { fontSize: '14px', color: '#6b7280', margin: 0 },
  selectorBar: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    padding: '12px 18px',
    border: '1px solid #e5e7eb',
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    flexWrap: 'wrap',
  },
  selectorLabel: { fontSize: '13px', fontWeight: '600', color: '#374151' },
  caseButtons: { display: 'flex', gap: '8px', flexWrap: 'wrap' },
  caseBtn: {
    padding: '6px 14px',
    borderRadius: '6px',
    border: '1px solid',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  contentLayout: { display: 'flex', flexDirection: 'column', gap: '20px' },
  summaryRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: '16px',
  },
  patternCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    padding: '18px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  patternHeader: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' },
  patternIcon: { fontSize: '18px' },
  patternTitle: { fontSize: '15px', fontWeight: '600', color: '#111827', margin: 0 },
  splitItem: {
    backgroundColor: '#f9fafb',
    padding: '10px 12px',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
    fontSize: '12px',
    marginBottom: '8px',
  },
  detailText: { color: '#4b5563', marginTop: '2px' },
  targetList: { color: '#6b7280', fontSize: '11px', marginTop: '4px' },
  muted: { color: '#9ca3af', fontSize: '13px', fontStyle: 'italic', margin: 0 },
  sectionCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
    overflow: 'hidden',
  },
  sectionHeader: {
    padding: '16px 20px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fafafa',
  },
  sectionTitle: { fontSize: '15px', fontWeight: '600', color: '#111827', margin: '0 0 4px 0' },
  sectionHint: { fontSize: '12px', color: '#6b7280' },
  pathsList: { padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '10px' },
  pathItem: {
    backgroundColor: '#f9fafb',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    padding: '12px 16px',
    fontSize: '12px',
  },
  pathMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '8px',
    color: '#374151',
    flexWrap: 'wrap',
  },
  pathIdx: {
    backgroundColor: '#3b82f6',
    color: '#ffffff',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '10px',
    fontWeight: '700',
  },
  pathDuration: {
    backgroundColor: '#e5e7eb',
    color: '#4b5563',
    padding: '2px 8px',
    borderRadius: '10px',
    fontSize: '11px',
    marginLeft: 'auto',
  },
  pathChain: { display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' },
  pathNode: {
    backgroundColor: '#ffffff',
    border: '1px solid #d1d5db',
    padding: '3px 8px',
    borderRadius: '4px',
    fontWeight: '600',
    color: '#1f2937',
  },
  pathArrow: { color: '#9ca3af', fontWeight: '700' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' },
  thRow: { backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' },
  th: {
    padding: '12px 16px',
    fontWeight: '600',
    color: '#4b5563',
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  tr: { borderBottom: '1px solid #f3f4f6' },
  td: { padding: '12px 16px', color: '#374151' },
  tdId: { padding: '12px 16px', fontWeight: '600', color: '#2563eb', fontFamily: 'monospace' },
  tdBold: { padding: '12px 16px', fontWeight: '600', color: '#111827' },
  tdMuted: { padding: '12px 16px', color: '#6b7280', fontSize: '12px' },
  tdAmount: {
    padding: '12px 16px',
    fontWeight: '700',
    color: '#111827',
    textAlign: 'right',
    fontFamily: 'monospace',
  },
}
