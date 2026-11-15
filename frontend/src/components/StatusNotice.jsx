import React from 'react'

export function LoadingSpinner({ message = 'Loading intelligence data...' }) {
  return (
    <div style={styles.card}>
      <div style={styles.spinner} />
      <p style={styles.loadingText}>{message}</p>
    </div>
  )
}

export function ErrorMessage({ error, onRetry }) {
  const isNetworkError =
    !error?.response ||
    error?.code === 'ERR_NETWORK' ||
    error?.message?.includes('Network Error') ||
    error?.message?.includes('Failed to fetch')

  const displayMessage = isNetworkError
    ? 'Backend not reachable. Start it with uvicorn backend.main:app --port 8000'
    : error?.response?.data?.detail || error?.message || 'An unexpected error occurred.'

  return (
    <div style={styles.errorBox}>
      <div style={styles.errorHeader}>
        <span style={{ fontSize: '18px' }}>⚠️</span>
        <strong>Error</strong>
      </div>
      <p style={styles.errorBody}>{displayMessage}</p>
      {onRetry && (
        <button onClick={onRetry} style={styles.retryBtn}>
          Try Again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ message = 'No reported case records found.' }) {
  return (
    <div style={styles.card}>
      <span style={{ fontSize: '28px', color: '#9ca3af' }}>📂</span>
      <p style={styles.emptyText}>{message}</p>
    </div>
  )
}

const styles = {
  card: {
    padding: '40px 20px',
    textAlign: 'center',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    margin: '20px 0',
  },
  spinner: {
    width: '32px',
    height: '32px',
    border: '3px solid #e5e7eb',
    borderTop: '3px solid #3b82f6',
    borderRadius: '50%',
    margin: '0 auto 12px auto',
    animation: 'spin 1s linear infinite',
  },
  loadingText: {
    color: '#6b7280',
    fontSize: '14px',
    margin: 0,
  },
  emptyText: {
    color: '#6b7280',
    fontSize: '14px',
    marginTop: '10px',
  },
  errorBox: {
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    padding: '16px 20px',
    color: '#991b1b',
    margin: '20px 0',
  },
  errorHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '15px',
    marginBottom: '6px',
  },
  errorBody: {
    fontSize: '14px',
    margin: 0,
    lineHeight: '1.5',
  },
  retryBtn: {
    marginTop: '12px',
    padding: '6px 14px',
    backgroundColor: '#dc2626',
    color: '#ffffff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
  },
}
