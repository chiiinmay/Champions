
import React from 'react'

export default function DisclaimerBanner() {
  return (
    <div style={styles.banner}>
      <div style={styles.content}>
        <span style={styles.badge}>SYNTHETIC DATA</span>
        <span style={styles.text}>
          <strong>Investigative leads for human review, not proof of criminal activity.</strong> SHADOWNET does not block payments or determine guilt.
        </span>
      </div>
    </div>
  )
}

const styles = {
  banner: {
    backgroundColor: '#fffbeb',
    borderBottom: '1px solid #fde68a',
    padding: '8px 20px',
    color: '#92400e',
    fontSize: '13px',
    lineHeight: '1.4',
  },
  content: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    flexWrap: 'wrap',
  },
  badge: {
    backgroundColor: '#374151',
    color: '#ffffff',
    fontWeight: '700',
    fontSize: '10px',
    letterSpacing: '0.05em',
    padding: '2px 8px',
    borderRadius: '4px',
    display: 'inline-flex',
  },
  text: {
    flex: 1,
  },
}
