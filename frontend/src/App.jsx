import React from 'react'
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import DisclaimerBanner from './components/DisclaimerBanner'
import Overview from './pages/Overview'
import NetworkExplorer from './pages/NetworkExplorer'
import PatternFingerprinting from './pages/PatternFingerprinting'
import MoneyTrail from './pages/MoneyTrail'
import EarlyWarning from './pages/EarlyWarning'
import Upload from './pages/Upload'

export default function App() {
  return (
    <BrowserRouter>
      <div style={styles.appContainer}>
        {/* Persistent Top Disclaimer Banner */}
        <DisclaimerBanner />

        <div style={styles.mainLayout}>
          {/* Navigation Sidebar */}
          <aside style={styles.sidebar}>
            <div style={styles.brand}>
              <div style={styles.brandLogo}>⚡</div>
              <div>
                <div style={styles.brandTitle}>SHADOWNET</div>
                <div style={styles.brandSubtitle}>Intelligence Prototype</div>
              </div>
            </div>

            <nav style={styles.nav}>
              <NavLink
                to="/"
                end
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                <span style={styles.navIcon}>📊</span>
                <span>Overview</span>
              </NavLink>

              <NavLink
                to="/network"
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                <span style={styles.navIcon}>🕸️</span>
                <span>Network Explorer</span>
              </NavLink>

              <NavLink
                to="/patterns"
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                <span style={styles.navIcon}>🧬</span>
                <span>Pattern Fingerprinting</span>
              </NavLink>

              <NavLink
                to="/money-trail"
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                <span style={styles.navIcon}>💸</span>
                <span>Money Trail</span>
              </NavLink>

              <NavLink
                to="/early-warning"
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                <span style={styles.navIcon}>🚨</span>
                <span>Early Warning</span>
              </NavLink>

              <NavLink
                to="/upload"
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                <span style={styles.navIcon}>📤</span>
                <span>Upload Dataset</span>
              </NavLink>
            </nav>

            <div style={styles.sidebarFooter}>
              <div style={styles.envTag}>ENV: LOCAL DEV</div>
              <div style={styles.statusDot}>
                <span style={styles.greenDot} /> API: port 8000
              </div>
            </div>
          </aside>

          {/* Main Content Area */}
          <main style={styles.mainContent}>
            <div style={styles.pageInner}>
              <Routes>
                <Route path="/" element={<Overview />} />
                <Route path="/network" element={<NetworkExplorer />} />
                <Route path="/patterns" element={<PatternFingerprinting />} />
                <Route path="/money-trail" element={<MoneyTrail />} />
                <Route path="/money-trail/:caseId" element={<MoneyTrail />} />
                <Route path="/early-warning" element={<EarlyWarning />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </div>

            {/* Global Bottom Footer */}
            <footer style={styles.footer}>
              This prototype simulates a shared intelligence view across banks. A real deployment would need data-sharing agreements and privacy controls.
            </footer>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}

const styles = {
  appContainer: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    backgroundColor: '#f3f4f6',
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    color: '#111827',
  },
  mainLayout: {
    display: 'flex',
    flex: 1,
    minHeight: 0,
  },
  sidebar: {
    width: '240px',
    backgroundColor: '#1e293b',
    color: '#f8fafc',
    display: 'flex',
    flexDirection: 'column',
    flexShrink: 0,
  },
  brand: {
    padding: '20px',
    borderBottom: '1px solid #334155',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  brandLogo: {
    fontSize: '22px',
    backgroundColor: '#3b82f6',
    color: '#ffffff',
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandTitle: {
    fontWeight: '800',
    fontSize: '16px',
    letterSpacing: '0.05em',
  },
  brandSubtitle: {
    fontSize: '10px',
    color: '#94a3b8',
    textTransform: 'uppercase',
  },
  nav: {
    padding: '16px 10px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    flex: 1,
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 14px',
    borderRadius: '6px',
    color: '#cbd5e1',
    textDecoration: 'none',
    fontSize: '13px',
    fontWeight: '500',
    transition: 'all 0.15s ease',
  },
  navLinkActive: {
    backgroundColor: '#2563eb',
    color: '#ffffff',
    fontWeight: '600',
  },
  navIcon: {
    fontSize: '16px',
  },
  sidebarFooter: {
    padding: '16px 20px',
    borderTop: '1px solid #334155',
    fontSize: '11px',
    color: '#94a3b8',
  },
  envTag: {
    fontWeight: '700',
    marginBottom: '4px',
    letterSpacing: '0.05em',
  },
  statusDot: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  greenDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#10b981',
  },
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflowY: 'auto',
    minWidth: 0,
  },
  pageInner: {
    flex: 1,
    padding: '24px 32px',
    maxWidth: '1440px',
    width: '100%',
    boxSizing: 'border-box',
    margin: '0 auto',
  },
  footer: {
    padding: '14px 32px',
    backgroundColor: '#ffffff',
    borderTop: '1px solid #e5e7eb',
    fontSize: '12px',
    color: '#6b7280',
    textAlign: 'center',
  },
}
