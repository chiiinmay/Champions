import React, { useState } from 'react'
import { simulateRisk } from '../api'
import RiskBadge from '../components/RiskBadge'
import { LoadingSpinner, ErrorMessage } from '../components/StatusNotice'

const PRESET_1 = [
  { sender_account: 'V_SIM_1', receiver_account: 'M_SIM_1', amount: 30000.0, timestamp: '2026-11-20 10:00:00', sender_bank: 'Bank Alpha', receiver_bank: 'Bank Beta' },
  { sender_account: 'V_SIM_2', receiver_account: 'M_SIM_1', amount: 25000.0, timestamp: '2026-11-20 10:08:00', sender_bank: 'Bank Alpha', receiver_bank: 'Bank Beta' },
  { sender_account: 'M_SIM_1', receiver_account: 'L2_SIM_A', amount: 17000.0, timestamp: '2026-11-20 10:15:00', sender_bank: 'Bank Beta', receiver_bank: 'Bank Gamma' },
  { sender_account: 'M_SIM_1', receiver_account: 'L2_SIM_B', amount: 17000.0, timestamp: '2026-11-20 10:18:00', sender_bank: 'Bank Beta', receiver_bank: 'Bank Alpha' },
  { sender_account: 'M_SIM_1', receiver_account: 'L2_SIM_C', amount: 17000.0, timestamp: '2026-11-20 10:21:00', sender_bank: 'Bank Beta', receiver_bank: 'Bank Gamma' },
  { sender_account: 'L2_SIM_A', receiver_account: 'CO_SIM_1', amount: 16500.0, timestamp: '2026-11-20 10:50:00', sender_bank: 'Bank Gamma', receiver_bank: 'Bank Alpha' },
  { sender_account: 'L2_SIM_B', receiver_account: 'CO_SIM_1', amount: 16500.0, timestamp: '2026-11-20 10:55:00', sender_bank: 'Bank Alpha', receiver_bank: 'Bank Alpha' },
  { sender_account: 'L2_SIM_C', receiver_account: 'CO_SIM_1', amount: 16500.0, timestamp: '2026-11-20 10:58:00', sender_bank: 'Bank Gamma', receiver_bank: 'Bank Alpha' },
]

const PRESET_2 = [
  { sender_account: 'NEW_VICTIM_X', receiver_account: 'B900', amount: 50000.0, timestamp: '2026-11-20 11:00:00', sender_bank: 'Bank Alpha', receiver_bank: 'Bank Beta' },
]

const PRESET_3 = [
  { sender_account: 'SLOW_P_1', receiver_account: 'SLOW_Q_1', amount: 500.0, timestamp: '2026-11-20 09:00:00', sender_bank: 'Bank Alpha', receiver_bank: 'Bank Beta' },
  { sender_account: 'SLOW_P_2', receiver_account: 'SLOW_Q_2', amount: 450.0, timestamp: '2026-11-21 14:00:00', sender_bank: 'Bank Beta', receiver_bank: 'Bank Gamma' },
]

export default function EarlyWarning() {
  const [transactions, setTransactions] = useState(PRESET_1)
  const [activePreset, setActivePreset] = useState(1)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const applyPreset = (presetNumber, txList) => {
    setActivePreset(presetNumber)
    setTransactions(JSON.parse(JSON.stringify(txList)))
    setResult(null)
  }

  const handleRowChange = (index, field, value) => {
    const updated = [...transactions]
    updated[index] = { ...updated[index], [field]: value }
    setTransactions(updated)
  }

  const addRow = () => {
    setTransactions([
      ...transactions,
      {
        sender_account: '',
        receiver_account: '',
        amount: 1000.0,
        timestamp: '2026-11-20 12:00:00',
        sender_bank: 'Bank Alpha',
        receiver_bank: 'Bank Beta',
      },
    ])
  }

  const removeRow = (index) => {
    if (transactions.length <= 1) return
    setTransactions(transactions.filter((_, i) => i !== index))
  }

  const handleRunSimulation = async () => {
    setLoading(true)
    setError(null)
    try {
      const formatted = transactions.map((t) => ({
        ...t,
        amount: parseFloat(t.amount) || 0,
      }))
      const res = await simulateRisk(formatted)
      setResult(res)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Early Warning Simulation</h1>
        <p style={styles.subtitle}>
          Evaluate new hypothetical scenarios against known case topologies to generate explainable review priorities.
        </p>
      </div>

      {/* Preset Scenario Buttons */}
      <div style={styles.presetBar}>
        <span style={styles.presetLabel}>Load Scenario Preset:</span>
        <div style={styles.presetButtonGroup}>
          <button
            type="button"
            onClick={() => applyPreset(1, PRESET_1)}
            style={{
              ...styles.presetBtn,
              backgroundColor: activePreset === 1 ? '#2563eb' : '#ffffff',
              color: activePreset === 1 ? '#ffffff' : '#374151',
              borderColor: activePreset === 1 ? '#1d4ed8' : '#d1d5db',
            }}
          >
            Preset 1: Rapid 3-Account Fan-Out (New Accounts)
          </button>
          <button
            type="button"
            onClick={() => applyPreset(2, PRESET_2)}
            style={{
              ...styles.presetBtn,
              backgroundColor: activePreset === 2 ? '#2563eb' : '#ffffff',
              color: activePreset === 2 ? '#ffffff' : '#374151',
              borderColor: activePreset === 2 ? '#1d4ed8' : '#d1d5db',
            }}
          >
            Preset 2: Transfer to B900 (Known Mule)
          </button>
          <button
            type="button"
            onClick={() => applyPreset(3, PRESET_3)}
            style={{
              ...styles.presetBtn,
              backgroundColor: activePreset === 3 ? '#2563eb' : '#ffffff',
              color: activePreset === 3 ? '#ffffff' : '#374151',
              borderColor: activePreset === 3 ? '#1d4ed8' : '#d1d5db',
            }}
          >
            Preset 3: Slow Small Payments (Routine)
          </button>
        </div>
      </div>

      <div style={styles.layout}>
        {/* Left: Editable Transactions Grid */}
        <div style={styles.editorCard}>
          <div style={styles.editorHeader}>
            <div>
              <h3 style={styles.cardTitle}>Scenario Transactions ({transactions.length})</h3>
              <span style={styles.cardHint}>Add, modify, or remove simulated transfers</span>
            </div>
            <button type="button" onClick={addRow} style={styles.addRowBtn}>
              + Add Transfer
            </button>
          </div>

          <div style={{ overflowX: 'auto', padding: '16px' }}>
            <table style={styles.editorTable}>
              <thead>
                <tr>
                  <th style={styles.th}>Sender</th>
                  <th style={styles.th}>Sender Bank</th>
                  <th style={styles.th}>Receiver</th>
                  <th style={styles.th}>Receiver Bank</th>
                  <th style={styles.th}>Amount (INR)</th>
                  <th style={styles.th}>Timestamp</th>
                  <th style={styles.th}></th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx, idx) => (
                  <tr key={idx}>
                    <td style={styles.tdInput}>
                      <input
                        type="text"
                        value={tx.sender_account}
                        onChange={(e) => handleRowChange(idx, 'sender_account', e.target.value)}
                        style={styles.input}
                        placeholder="ACC_FROM"
                      />
                    </td>
                    <td style={styles.tdInput}>
                      <select
                        value={tx.sender_bank}
                        onChange={(e) => handleRowChange(idx, 'sender_bank', e.target.value)}
                        style={styles.select}
                      >
                        <option value="Bank Alpha">Bank Alpha</option>
                        <option value="Bank Beta">Bank Beta</option>
                        <option value="Bank Gamma">Bank Gamma</option>
                      </select>
                    </td>
                    <td style={styles.tdInput}>
                      <input
                        type="text"
                        value={tx.receiver_account}
                        onChange={(e) => handleRowChange(idx, 'receiver_account', e.target.value)}
                        style={styles.input}
                        placeholder="ACC_TO"
                      />
                    </td>
                    <td style={styles.tdInput}>
                      <select
                        value={tx.receiver_bank}
                        onChange={(e) => handleRowChange(idx, 'receiver_bank', e.target.value)}
                        style={styles.select}
                      >
                        <option value="Bank Alpha">Bank Alpha</option>
                        <option value="Bank Beta">Bank Beta</option>
                        <option value="Bank Gamma">Bank Gamma</option>
                      </select>
                    </td>
                    <td style={styles.tdInput}>
                      <input
                        type="number"
                        value={tx.amount}
                        onChange={(e) => handleRowChange(idx, 'amount', e.target.value)}
                        style={{ ...styles.input, textAlign: 'right' }}
                      />
                    </td>
                    <td style={styles.tdInput}>
                      <input
                        type="text"
                        value={tx.timestamp}
                        onChange={(e) => handleRowChange(idx, 'timestamp', e.target.value)}
                        style={styles.input}
                      />
                    </td>
                    <td style={styles.tdInput}>
                      <button
                        type="button"
                        onClick={() => removeRow(idx)}
                        disabled={transactions.length <= 1}
                        style={{
                          ...styles.delBtn,
                          opacity: transactions.length <= 1 ? 0.3 : 1,
                        }}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={styles.editorFooter}>
            <button
              type="button"
              onClick={handleRunSimulation}
              disabled={loading}
              style={styles.runBtn}
            >
              {loading ? 'Evaluating Scenario...' : 'Run Priority Assessment'}
            </button>
          </div>
        </div>

        {/* Right: Results Assessment Card */}
        <div style={styles.resultCard}>
          {loading && <LoadingSpinner message="Calculating behavioral risk assessment..." />}
          {error && <ErrorMessage error={error} onRetry={handleRunSimulation} />}

          {!loading && !error && !result && (
            <div style={styles.resultPlaceholder}>
              <div style={{ fontSize: '36px', marginBottom: '12px' }}>📊</div>
              <strong>Ready to Assess Scenario</strong>
              <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
                Select a preset or edit transactions, then click "Run Priority Assessment".
              </p>
            </div>
          )}

          {!loading && !error && result && (
            <div>
              <div style={styles.resultHeader}>
                <div>
                  <h3 style={styles.cardTitle}>Assessment Result</h3>
                  <span style={styles.cardHint}>Generated priority for human review</span>
                </div>
                <RiskBadge level={result.risk_level} />
              </div>

              {/* Score Display */}
              <div style={styles.scoreBox}>
                <div style={styles.scoreRow}>
                  <span>Priority Review Score:</span>
                  <span style={styles.scoreNumber}>{(result.risk_score * 100).toFixed(1)}%</span>
                </div>
                <div style={styles.progressBarBg}>
                  <div
                    style={{
                      ...styles.progressBarFill,
                      width: `${Math.min(100, result.risk_score * 100)}%`,
                      backgroundColor:
                        result.risk_score >= 0.65
                          ? '#ef4444'
                          : result.risk_score >= 0.35
                          ? '#f59e0b'
                          : '#10b981',
                    }}
                  />
                </div>
              </div>

              {/* Component breakdown */}
              <div style={styles.componentsSection}>
                <h4 style={styles.subHeading}>Component Weights Breakdown</h4>

                <div style={styles.compItem}>
                  <div style={styles.compLabel}>
                    <span>Direct Account Connection (40% weight)</span>
                    <strong>{((result.components?.connection || 0) * 100).toFixed(0)}%</strong>
                  </div>
                  <div style={styles.miniBarTrack}>
                    <div
                      style={{
                        ...styles.miniBarFill,
                        width: `${(result.components?.connection || 0) * 100}%`,
                        backgroundColor: '#3b82f6',
                      }}
                    />
                  </div>
                </div>

                <div style={styles.compItem}>
                  <div style={styles.compLabel}>
                    <span>Pattern Similarity to Known Fraud (35% weight)</span>
                    <strong>{((result.components?.pattern_similarity || 0) * 100).toFixed(0)}%</strong>
                  </div>
                  <div style={styles.miniBarTrack}>
                    <div
                      style={{
                        ...styles.miniBarFill,
                        width: `${(result.components?.pattern_similarity || 0) * 100}%`,
                        backgroundColor: '#8b5cf6',
                      }}
                    />
                  </div>
                </div>

                <div style={styles.compItem}>
                  <div style={styles.compLabel}>
                    <span>Isolation Forest Anomaly Level (25% weight)</span>
                    <strong>{((result.components?.anomaly || 0) * 100).toFixed(0)}%</strong>
                  </div>
                  <div style={styles.miniBarTrack}>
                    <div
                      style={{
                        ...styles.miniBarFill,
                        width: `${(result.components?.anomaly || 0) * 100}%`,
                        backgroundColor: '#f59e0b',
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Closest known cases */}
              <div style={styles.section}>
                <h4 style={styles.subHeading}>Closest Known Reported Cases</h4>
                <div style={styles.closestList}>
                  {(result.closest_known_cases || []).map((c, idx) => (
                    <div key={idx} style={styles.closestItem}>
                      <span style={{ fontWeight: '600' }}>{c.case_id}</span>
                      <span style={styles.simPill}>
                        Similarity: {(c.similarity * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Matched Features */}
              {result.matched_features?.length > 0 && (
                <div style={styles.section}>
                  <h4 style={styles.subHeading}>Matched Behavioral Features</h4>
                  <div style={styles.tagGroup}>
                    {result.matched_features.map((feat, idx) => (
                      <span key={idx} style={styles.tag}>
                        {feat}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Reasons */}
              <div style={styles.section}>
                <h4 style={styles.subHeading}>Assessment Reasons</h4>
                <ul style={styles.reasonsList}>
                  {(result.reasons || []).map((reason, idx) => (
                    <li key={idx} style={styles.reasonItem}>
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>

              <div style={styles.disclaimerBox}>
                <span style={{ fontSize: '11px', color: '#6b7280' }}>
                  {result.disclaimer ||
                    'Investigative lead only; not proof of criminal activity.'}
                </span>
              </div>
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
  presetBar: {
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
  presetLabel: { fontSize: '13px', fontWeight: '600', color: '#374151' },
  presetButtonGroup: { display: 'flex', gap: '10px', flexWrap: 'wrap' },
  presetBtn: {
    padding: '6px 14px',
    borderRadius: '6px',
    border: '1px solid',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  layout: {
    display: 'grid',
    gridTemplateColumns: 'minmax(0, 1fr) 420px',
    gap: '20px',
  },
  editorCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  editorHeader: {
    padding: '16px 20px',
    borderBottom: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fafafa',
  },
  cardTitle: { fontSize: '15px', fontWeight: '600', color: '#111827', margin: '0 0 2px 0' },
  cardHint: { fontSize: '12px', color: '#6b7280' },
  addRowBtn: {
    padding: '6px 12px',
    backgroundColor: '#f3f4f6',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '600',
    color: '#374151',
    cursor: 'pointer',
  },
  editorTable: { width: '100%', borderCollapse: 'collapse', fontSize: '12px' },
  th: {
    padding: '8px 10px',
    textAlign: 'left',
    color: '#4b5563',
    fontWeight: '600',
    borderBottom: '1px solid #e5e7eb',
  },
  tdInput: { padding: '6px 8px' },
  input: {
    width: '100%',
    padding: '6px 8px',
    borderRadius: '4px',
    border: '1px solid #d1d5db',
    fontSize: '12px',
    boxSizing: 'border-box',
  },
  select: {
    width: '100%',
    padding: '6px 8px',
    borderRadius: '4px',
    border: '1px solid #d1d5db',
    fontSize: '12px',
    backgroundColor: '#ffffff',
    boxSizing: 'border-box',
  },
  delBtn: {
    background: 'none',
    border: 'none',
    color: '#ef4444',
    cursor: 'pointer',
    fontSize: '14px',
    padding: '4px',
  },
  editorFooter: {
    padding: '16px 20px',
    borderTop: '1px solid #e5e7eb',
    textAlign: 'right',
    backgroundColor: '#fafafa',
  },
  runBtn: {
    padding: '10px 20px',
    backgroundColor: '#2563eb',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontWeight: '600',
    fontSize: '14px',
    cursor: 'pointer',
  },
  resultCard: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    padding: '20px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  resultPlaceholder: {
    textAlign: 'center',
    padding: '80px 20px',
    color: '#4b5563',
  },
  resultHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid #e5e7eb',
    paddingBottom: '14px',
    marginBottom: '16px',
  },
  scoreBox: {
    backgroundColor: '#f9fafb',
    padding: '14px',
    borderRadius: '6px',
    border: '1px solid #e5e7eb',
    marginBottom: '18px',
  },
  scoreRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
    fontWeight: '600',
    color: '#374151',
    marginBottom: '8px',
  },
  scoreNumber: { fontSize: '18px', fontWeight: '700', color: '#111827' },
  progressBarBg: {
    width: '100%',
    height: '8px',
    backgroundColor: '#e5e7eb',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressBarFill: { height: '100%', borderRadius: '4px' },
  componentsSection: { marginBottom: '16px' },
  subHeading: { fontSize: '13px', fontWeight: '600', color: '#374151', margin: '0 0 8px 0' },
  compItem: { marginBottom: '10px' },
  compLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '11px',
    color: '#4b5563',
    marginBottom: '4px',
  },
  miniBarTrack: {
    width: '100%',
    height: '6px',
    backgroundColor: '#f3f4f6',
    borderRadius: '3px',
    overflow: 'hidden',
  },
  miniBarFill: { height: '100%', borderRadius: '3px' },
  section: { marginBottom: '16px' },
  closestList: { display: 'flex', flexDirection: 'column', gap: '6px' },
  closestItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '12px',
    padding: '6px 10px',
    backgroundColor: '#f9fafb',
    borderRadius: '4px',
    border: '1px solid #e5e7eb',
  },
  simPill: {
    backgroundColor: '#e0e7ff',
    color: '#3730a3',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: '600',
  },
  tagGroup: { display: 'flex', flexWrap: 'wrap', gap: '6px' },
  tag: {
    backgroundColor: '#f3f4f6',
    color: '#374151',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    padding: '2px 8px',
    fontSize: '11px',
  },
  reasonsList: { margin: 0, paddingLeft: '18px', fontSize: '12px', color: '#4b5563', lineHeight: '1.5' },
  reasonItem: { marginBottom: '4px' },
  disclaimerBox: {
    marginTop: '18px',
    paddingTop: '12px',
    borderTop: '1px solid #f3f4f6',
  },
}
