import React, { useState } from 'react'
import { uploadTransactions } from '../api'

const REQUIRED_COLUMNS = [
  { name: 'transaction_id', type: 'string', desc: 'Unique transfer identifier (e.g. TX00001)' },
  { name: 'case_id', type: 'string', desc: 'Case cluster identifier (e.g. CASE_A, NORM_01)' },
  { name: 'sender_bank', type: 'string', desc: 'Origin financial institution (e.g. Bank Alpha)' },
  { name: 'receiver_bank', type: 'string', desc: 'Destination financial institution (e.g. Bank Beta)' },
  { name: 'sender_account', type: 'string', desc: 'Debited originating account number' },
  { name: 'receiver_account', type: 'string', desc: 'Credited beneficiary account number' },
  { name: 'amount', type: 'float', desc: 'Positive transfer amount in INR' },
  { name: 'timestamp', type: 'datetime', desc: 'ISO format (YYYY-MM-DD HH:MM:SS)' },
  { name: 'transaction_type', type: 'string', desc: 'Transfer, Payment, etc.' },
  { name: 'is_synthetic_suspicious', type: 'Yes/No', desc: 'Simulation ground-truth flag (not used by models)' },
  { name: 'source', type: 'string', desc: 'synthetic, public_paysim, etc.' },
]

export default function Upload() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setErrorMsg(null)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setErrorMsg(null)
    setResult(null)

    try {
      const res = await uploadTransactions(file)
      setResult(res)
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        'Upload failed. Check file format.'
      setErrorMsg(detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Upload Transactions Dataset</h1>
        <p style={styles.subtitle}>
          Load multi-bank CSV transaction records into SHADOWNET's in-memory analytical state.
        </p>
      </div>

      {/* In-Memory Persistence Warning Notice */}
      <div style={styles.noticeBanner}>
        <strong>In-Memory Operational Boundary:</strong> Uploaded CSV files reload the server's
        active in-memory analytical cache only. The bundled on-disk dataset (
        <code>dataset/transactions.csv</code>) is never modified or overwritten.
      </div>

      <div style={styles.layout}>
        {/* Upload Form Card */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Upload CSV File</h2>
          <p style={styles.cardDesc}>
            Select a comma-separated values (.csv) file matching the schema requirements.
          </p>

          <form onSubmit={handleUpload}>
            <div style={styles.dropZone}>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                style={styles.fileInput}
                id="file-upload"
              />
              <label htmlFor="file-upload" style={styles.fileLabel}>
                <span style={{ fontSize: '32px' }}>📁</span>
                <span style={{ fontWeight: '600', color: '#2563eb', marginTop: '6px' }}>
                  {file ? file.name : 'Choose CSV file to upload'}
                </span>
                <span style={{ fontSize: '11px', color: '#6b7280' }}>
                  {file ? `${(file.size / 1024).toFixed(1)} KB` : 'or click to browse'}
                </span>
              </label>
            </div>

            <div style={{ marginTop: '16px', textAlign: 'right' }}>
              <button
                type="submit"
                disabled={!file || loading}
                style={{
                  ...styles.submitBtn,
                  opacity: !file || loading ? 0.6 : 1,
                  cursor: !file || loading ? 'not-allowed' : 'pointer',
                }}
              >
                {loading ? 'Processing & Validating...' : 'Upload & Reload State'}
              </button>
            </div>
          </form>

          {/* Success Summary */}
          {result && (
            <div style={styles.successBox}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>✅</span>
                <strong style={{ color: '#065f46' }}>Dataset Successfully Loaded</strong>
              </div>
              <ul style={styles.successList}>
                <li>
                  Total Transactions Parsed: <strong>{result.transactions}</strong>
                </li>
                <li>
                  Reported Cases Identified: <strong>{result.cases}</strong>
                </li>
                <li>
                  Status: <strong>{result.status}</strong>
                </li>
              </ul>
            </div>
          )}

          {/* Error Message */}
          {errorMsg && (
            <div style={styles.errorBox}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>⚠️</span>
                <strong style={{ color: '#991b1b' }}>Upload Validation Error (HTTP 400)</strong>
              </div>
              <p style={styles.errorText}>{errorMsg}</p>
            </div>
          )}
        </div>

        {/* Schema Contract Card */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Required Schema Contract</h2>
          <p style={styles.cardDesc}>
            All 11 columns below must be present with valid headers for the parser to accept the file.
          </p>

          <div style={{ overflowX: 'auto' }}>
            <table style={styles.schemaTable}>
              <thead>
                <tr>
                  <th style={styles.th}>Column</th>
                  <th style={styles.th}>Type</th>
                  <th style={styles.th}>Description</th>
                </tr>
              </thead>
              <tbody>
                {REQUIRED_COLUMNS.map((col) => (
                  <tr key={col.name} style={styles.tr}>
                    <td style={styles.tdCol}>{col.name}</td>
                    <td style={styles.tdType}>{col.type}</td>
                    <td style={styles.tdDesc}>{col.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
  noticeBanner: {
    backgroundColor: '#eff6ff',
    border: '1px solid #bfdbfe',
    borderRadius: '8px',
    padding: '12px 18px',
    fontSize: '13px',
    color: '#1e40af',
    marginBottom: '20px',
    lineHeight: '1.4',
  },
  layout: {
    display: 'grid',
    gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1.2fr)',
    gap: '20px',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    padding: '20px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  cardTitle: { fontSize: '16px', fontWeight: '600', color: '#111827', margin: '0 0 6px 0' },
  cardDesc: { fontSize: '13px', color: '#6b7280', margin: '0 0 16px 0' },
  dropZone: {
    border: '2px dashed #cbd5e1',
    borderRadius: '8px',
    padding: '30px 20px',
    textAlign: 'center',
    backgroundColor: '#f8fafc',
    position: 'relative',
    cursor: 'pointer',
  },
  fileInput: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    opacity: 0,
    cursor: 'pointer',
  },
  fileLabel: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    cursor: 'pointer',
  },
  submitBtn: {
    padding: '10px 20px',
    backgroundColor: '#2563eb',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontWeight: '600',
    fontSize: '13px',
  },
  successBox: {
    marginTop: '20px',
    padding: '16px',
    backgroundColor: '#ecfdf5',
    border: '1px solid #a7f3d0',
    borderRadius: '6px',
    fontSize: '13px',
  },
  successList: {
    margin: '8px 0 0 0',
    paddingLeft: '20px',
    color: '#065f46',
    lineHeight: '1.6',
  },
  errorBox: {
    marginTop: '20px',
    padding: '16px',
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '6px',
    fontSize: '13px',
  },
  errorText: {
    margin: '6px 0 0 0',
    color: '#991b1b',
    lineHeight: '1.4',
  },
  schemaTable: { width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' },
  th: {
    padding: '8px 10px',
    borderBottom: '1px solid #e5e7eb',
    color: '#4b5563',
    fontWeight: '600',
  },
  tr: { borderBottom: '1px solid #f3f4f6' },
  tdCol: { padding: '8px 10px', fontFamily: 'monospace', fontWeight: '600', color: '#1f2937' },
  tdType: { padding: '8px 10px', color: '#3b82f6', fontWeight: '500' },
  tdDesc: { padding: '8px 10px', color: '#4b5563' },
}
