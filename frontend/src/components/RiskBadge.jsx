import React from 'react'

export default function RiskBadge({ level }) {
  const norm = (level || '').toLowerCase()

  let bg = '#f3f4f6'
  let color = '#374151'
  let border = '#d1d5db'
  let icon = 'ℹ️'

  if (norm.includes('high')) {
    bg = '#fee2e2'
    color = '#991b1b'
    border = '#f87171'
    icon = '⚠️'
  } else if (norm.includes('medium')) {
    bg = '#fef3c7'
    color = '#92400e'
    border = '#fcd34d'
    icon = '⚡'
  } else if (norm.includes('low')) {
    bg = '#dcfce7'
    color = '#166534'
    border = '#86efac'
    icon = '✓'
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        backgroundColor: bg,
        color: color,
        border: `1px solid ${border}`,
        borderRadius: '6px',
        padding: '3px 10px',
        fontSize: '12px',
        fontWeight: '600',
        whiteSpace: 'nowrap',
      }}
    >
      <span>{icon}</span>
      <span>{level || 'Unknown'}</span>
    </span>
  )
}
