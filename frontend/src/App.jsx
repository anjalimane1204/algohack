import { useEffect, useState } from 'react'
import './App.css'

const emptyForm = {
  name: '',
  dob: '',
  address: '',
  phone: '',
  pass_type: 'Student Pass',
}

const documentFields = [
  { key: 'id_proof', label: 'ID Proof' },
  { key: 'address_proof', label: 'Address Proof' },
  { key: 'photograph', label: 'Photograph' },
  { key: 'other_document', label: 'Other required document' },
]

const demoCases = {
  complete: {
    form: {
      name: 'Aisha Sharma',
      dob: '05/11/2001',
      address: '25 Lake View, Bengaluru',
      phone: '9876543210',
      pass_type: 'Student Pass',
    },
    files: ['id_proof', 'address_proof', 'photograph'],
  },
  missing: {
    form: {
      name: 'Aisha Sharma',
      dob: '05/11/2001',
      address: '25 Lake View, Bengaluru',
      phone: '9876543210',
      pass_type: 'Student Pass',
    },
    files: ['id_proof', 'photograph'],
  },
  mismatch: {
    form: {
      name: 'Aisha Sharma',
      dob: '05/11/2001',
      address: '25 Lake View, Bengaluru',
      phone: '9876543210',
      pass_type: 'Student Pass',
    },
    files: ['id_proof', 'address_proof', 'photograph'],
  },
  manual: {
    form: {
      name: 'Rohit Nair',
      dob: '12/08/1998',
      address: '12 Main Road, Kochi',
      phone: '9000012345',
      pass_type: 'Senior Citizen Pass',
    },
    files: ['id_proof'],
  },
}

function App() {
  const [form, setForm] = useState(emptyForm)
  const [files, setFiles] = useState({})
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/applications')
      const payload = await response.json()
      setHistory(payload.results || [])
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const loadDemoCase = (caseKey) => {
    const demo = demoCases[caseKey]
    setForm(demo.form)
    setFiles({})
    setResult(null)
    setError('')
    const current = document.querySelectorAll('input[type="file"]')
    current.forEach((input) => {
      input.value = ''
    })
  }

  const handleFileChange = (event) => {
    const { name, files: selectedFiles } = event.target
    const file = selectedFiles && selectedFiles[0] ? selectedFiles[0] : null
    setFiles((prev) => ({ ...prev, [name]: file }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    const formData = new FormData()
    Object.entries(form).forEach(([key, value]) => {
      formData.append(key, value)
    })

    documentFields.forEach(({ key }) => {
      if (files[key]) {
        formData.append(key, files[key])
      }
    })

    try {
      const response = await fetch('http://localhost:8000/api/applications/verify', {
        method: 'POST',
        body: formData,
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || 'Verification failed')
      }

      setResult(payload)
      await fetchHistory()
    } catch (err) {
      setError(err.message || 'Unable to submit application')
    } finally {
      setLoading(false)
    }
  }

  const statusClass = (status) => {
    if (!status) return 'status-badge neutral'
    if (status === 'COMPLETE') return 'status-badge success'
    if (status === 'MANUAL_REVIEW') return 'status-badge warning'
    return 'status-badge danger'
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">ALG-AUTO-02</p>
          <h1>Smart Application Verification & Processing</h1>
        </div>
      </header>

      <section className="demo-panel">
        <h2>Quick demo cases</h2>
        <div className="demo-buttons">
          <button type="button" onClick={() => loadDemoCase('complete')}>Complete case</button>
          <button type="button" onClick={() => loadDemoCase('missing')}>Missing document</button>
          <button type="button" onClick={() => loadDemoCase('mismatch')}>Name mismatch</button>
          <button type="button" onClick={() => loadDemoCase('manual')}>Manual review</button>
        </div>
      </section>

      <main className="layout">
        <form className="card form-card" onSubmit={handleSubmit}>
          <h2>Application Form</h2>

          <div className="field-grid">
            <label>
              Name
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Enter full name"
              />
            </label>

            <label>
              Date of Birth
              <input
                type="text"
                value={form.dob}
                onChange={(e) => setForm({ ...form, dob: e.target.value })}
                placeholder="DD/MM/YYYY"
              />
            </label>

            <label className="full-width">
              Address
              <input
                type="text"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                placeholder="Enter address"
              />
            </label>

            <label>
              Phone Number
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="Enter phone number"
              />
            </label>

            <label>
              Pass/Application Type
              <select
                value={form.pass_type}
                onChange={(e) => setForm({ ...form, pass_type: e.target.value })}
              >
                <option>Student Pass</option>
                <option>Senior Citizen Pass</option>
                <option>General Pass</option>
                <option>Monthly Commuter Pass</option>
              </select>
            </label>
          </div>

          <div className="document-upload-section">
            <h3>Document Upload</h3>
            <div className="upload-grid">
              {documentFields.map(({ key, label }) => (
                <label key={key} className="upload-box">
                  <span>{label}</span>
                  <input
                    type="file"
                    name={key}
                    onChange={handleFileChange}
                    accept=".png,.jpg,.jpeg,.pdf"
                  />
                  {files[key] && <small>{files[key].name}</small>}
                </label>
              ))}
            </div>
          </div>

          {error && <div className="error-box">{error}</div>}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify Application'}
          </button>
        </form>

        <aside className="card result-card">
          {result ? (
            <>
              <div className="result-header">
                <h2>Verification Result</h2>
                <span className={statusClass(result.status)}>{result.status}</span>
              </div>

              <div className="report-block">
                <h3>Application ID</h3>
                <p>{result.id}</p>
              </div>

              <div className="report-block">
                <h3>Documents received</h3>
                <ul>
                  {result.documents_received.length ? (
                    result.documents_received.map((item) => <li key={item}>✓ {item}</li>)
                  ) : (
                    <li>No documents received</li>
                  )}
                </ul>
              </div>

              <div className="report-block">
                <h3>Missing documents</h3>
                <ul>
                  {result.missing_documents.length ? (
                    result.missing_documents.map((item) => <li key={item}>✗ {item}</li>)
                  ) : (
                    <li>None</li>
                  )}
                </ul>
              </div>

              <div className="report-block">
                <h3>Extracted information</h3>
                <pre>{JSON.stringify(result.extracted_data, null, 2)}</pre>
              </div>

              <div className="report-block">
                <h3>Validation results</h3>
                <ul>
                  {result.validation_results.length ? (
                    result.validation_results.map((item, index) => <li key={index}>{item}</li>)
                  ) : (
                    <li>No validation errors</li>
                  )}
                </ul>
              </div>

              <div className="report-block">
                <h3>Detected inconsistencies</h3>
                <ul>
                  {result.inconsistencies.length ? (
                    result.inconsistencies.map((item, index) => <li key={index}>{item}</li>)
                  ) : (
                    <li>No inconsistencies detected</li>
                  )}
                </ul>
              </div>

              <div className="report-block action-box">
                <h3>Required corrective action</h3>
                <p>{result.required_action}</p>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <h2>Verification dashboard</h2>
              <p>Submit an application to view the verification report.</p>
            </div>
          )}
        </aside>
      </main>

      <section className="card history-card">
        <h2>Application History</h2>
        <table>
          <thead>
            <tr>
              <th>Application ID</th>
              <th>Applicant</th>
              <th>Status</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {history.length ? (
              history.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.name || 'Unknown'}</td>
                  <td><span className={statusClass(item.status)}>{item.status}</span></td>
                  <td>{item.created_at}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4">No applications stored yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}

export default App
