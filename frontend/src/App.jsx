import { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export default function App() {
  const [apiStatus, setApiStatus] = useState('Checking API…')

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((response) => {
        if (!response.ok) throw new Error('API unavailable')
        return response.json()
      })
      .then((data) => setApiStatus(data.status === 'ok' ? 'Connected' : 'Unexpected response'))
      .catch(() => setApiStatus('Not connected'))
  }, [])

  return (
    <main className="page">
      <section className="panel">
        <div className="brand-mark">C</div>
        <p className="eyebrow">TAX DOCUMENT ASSISTANT</p>
        <h1>Claritax</h1>
        <p className="intro">A workspace for preparing and reviewing tax documents.</p>
        <div className="status">
          <span className={apiStatus === 'Connected' ? 'dot connected' : 'dot'} />
          Backend status: <strong>{apiStatus}</strong>
        </div>
        <p className="note">Project setup scaffold — document workflows will be added in upcoming tasks.</p>
      </section>
    </main>
  )
}
