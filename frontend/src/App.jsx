import { Fragment, useEffect, useMemo, useState } from 'react'
import './App.css'

const APPLICATION_TYPES = {
  scholarship: {
    key: 'scholarship',
    icon: '🎓',
    title: 'Scholarship Application',
    description: 'Academic funding, income verification, and merit review.',
    fields: [
      { key: 'applicant_name', label: 'Applicant Name', type: 'text', required: true },
      { key: 'date_of_birth', label: 'Date of Birth', type: 'text', required: true },
      { key: 'email', label: 'Email', type: 'email', required: true },
      { key: 'phone', label: 'Phone', type: 'tel', required: true },
      { key: 'address', label: 'Address', type: 'text', required: true },
      { key: 'institution', label: 'Institution', type: 'text', required: true },
      { key: 'course', label: 'Course', type: 'text', required: true },
      { key: 'academic_year', label: 'Academic Year', type: 'text', required: true },
      { key: 'annual_income', label: 'Annual Income', type: 'text', required: true },
      { key: 'academic_score', label: 'Academic Score / CGPA', type: 'text', required: true },
    ],
    requiredDocuments: [
      { key: 'identity_proof', label: 'Identity Proof', required: true },
      { key: 'student_id', label: 'Student ID / Bonafide Certificate', required: true },
      { key: 'marksheet', label: 'Marksheet', required: true },
      { key: 'income_certificate', label: 'Income Certificate', required: true },
      { key: 'address_proof', label: 'Address / Domicile Proof', required: true },
      { key: 'bank_proof', label: 'Bank Proof', required: true },
    ],
    optionalDocuments: [{ key: 'category_certificate', label: 'Category Certificate', required: false }],
  },
  transport_pass: {
    key: 'transport_pass',
    icon: '🚌',
    title: 'Transport Pass Application',
    description: 'Route access, identity, and residence verification.',
    fields: [
      { key: 'applicant_name', label: 'Applicant Name', type: 'text', required: true },
      { key: 'date_of_birth', label: 'Date of Birth', type: 'text', required: true },
      { key: 'address', label: 'Address', type: 'text', required: true },
      { key: 'phone', label: 'Phone', type: 'tel', required: true },
      { key: 'email', label: 'Email', type: 'email', required: false },
      { key: 'pass_type', label: 'Pass Type', type: 'text', required: true },
      { key: 'route', label: 'Route / Zone', type: 'text', required: false },
    ],
    requiredDocuments: [
      { key: 'identity_proof', label: 'Identity Proof', required: true },
      { key: 'address_proof', label: 'Address Proof', required: true },
      { key: 'student_employment_proof', label: 'Student / Employment Proof', required: true },
      { key: 'photograph', label: 'Photograph', required: true },
    ],
    optionalDocuments: [{ key: 'supporting_eligibility_document', label: 'Supporting Eligibility Document', required: false }],
  },
  college_admission: {
    key: 'college_admission',
    icon: '🏫',
    title: 'College Admission Application',
    description: 'Admission review, academic records, and transfer verification.',
    fields: [
      { key: 'applicant_name', label: 'Applicant Name', type: 'text', required: true },
      { key: 'date_of_birth', label: 'Date of Birth', type: 'text', required: true },
      { key: 'email', label: 'Email', type: 'email', required: true },
      { key: 'phone', label: 'Phone', type: 'tel', required: true },
      { key: 'institution', label: 'Preferred Institution', type: 'text', required: true },
      { key: 'course', label: 'Preferred Course', type: 'text', required: true },
      { key: 'academic_year', label: 'Admission Year', type: 'text', required: true },
      { key: 'address', label: 'Address', type: 'text', required: false },
    ],
    requiredDocuments: [
      { key: 'identity_proof', label: 'Identity Proof', required: true },
      { key: 'marksheet', label: 'Marksheet', required: true },
      { key: 'transfer_certificate', label: 'Transfer / Leaving Certificate', required: true },
      { key: 'admission_certificate', label: 'Admission / Student Certificate', required: true },
      { key: 'photograph', label: 'Photograph', required: true },
    ],
    optionalDocuments: [{ key: 'category_domicile_certificate', label: 'Category / Domicile Certificate', required: false }],
  },
}

const demoCases = {
  scholarship_complete: {
    applicationType: 'scholarship',
    form: {
      applicant_name: 'Aisha Sharma',
      date_of_birth: '05/11/2001',
      email: 'aisha@example.com',
      phone: '9876543210',
      address: '25 Lake View, Bengaluru',
      institution: 'NIT Trichy',
      course: 'Computer Science',
      academic_year: '2026',
      scholarship_type: 'Merit Scholarship',
      scholarship_category: 'General',
      annual_income: '120000',
      academic_score: '92%',
    },
  },
  scholarship_missing: {
    applicationType: 'scholarship',
    form: {
      applicant_name: 'Aisha Sharma',
      date_of_birth: '05/11/2001',
      email: 'aisha@example.com',
      phone: '9876543210',
      address: '25 Lake View, Bengaluru',
      institution: 'NIT Trichy',
      course: 'Computer Science',
      academic_year: '2026',
      scholarship_type: 'Merit Scholarship',
      scholarship_category: 'General',
      annual_income: '120000',
      academic_score: '92%',
    },
  },
  scholarship_wrong_document: {
    applicationType: 'scholarship',
    form: {
      applicant_name: 'Aisha Sharma',
      date_of_birth: '05/11/2001',
      email: 'aisha@example.com',
      phone: '9876543210',
      address: '25 Lake View, Bengaluru',
      institution: 'NIT Trichy',
      course: 'Computer Science',
      academic_year: '2026',
      scholarship_type: 'Merit Scholarship',
      scholarship_category: 'General',
      annual_income: '120000',
      academic_score: '92%',
    },
  },
  scholarship_name_mismatch: {
    applicationType: 'scholarship',
    form: {
      applicant_name: 'Aisha Sharma',
      date_of_birth: '05/11/2001',
      email: 'aisha@example.com',
      phone: '9876543210',
      address: '25 Lake View, Bengaluru',
      institution: 'NIT Trichy',
      course: 'Computer Science',
      academic_year: '2026',
      scholarship_type: 'Merit Scholarship',
      scholarship_category: 'General',
      annual_income: '120000',
      academic_score: '92%',
    },
  },
  transport_complete: {
    applicationType: 'transport_pass',
    form: {
      applicant_name: 'Rohit Menon',
      date_of_birth: '12/08/1998',
      email: 'rohit@example.com',
      phone: '9000012345',
      address: '12 Main Road, Kochi',
      pass_type: 'Student Pass',
      route: 'Blue Line - North Campus',
    },
  },
  admission_complete: {
    applicationType: 'college_admission',
    form: {
      applicant_name: 'Meera Iyer',
      date_of_birth: '03/03/2000',
      email: 'meera@example.com',
      phone: '9000098765',
      institution: 'BITS Pilani',
      course: 'Electronics',
      academic_year: '2026',
      address: '45 Green Park, Hyderabad',
    },
  },
}

const emptyForm = {
  applicant_name: '',
  date_of_birth: '',
  email: '',
  phone: '',
  address: '',
  institution: '',
  course: '',
  academic_year: '',
  annual_income: '',
  academic_score: '',
  scholarship_type: 'Merit Scholarship',
  scholarship_category: 'General',
  pass_type: 'Student Pass',
  route: '',
}

function App() {
  const [applicationType, setApplicationType] = useState('scholarship')
  const [form, setForm] = useState(emptyForm)
  const [files, setFiles] = useState({})
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [historyIssueId, setHistoryIssueId] = useState('')
  const [historyIssue, setHistoryIssue] = useState(null)
  const [historyIssueLoading, setHistoryIssueLoading] = useState(false)
  const [historyIssueError, setHistoryIssueError] = useState('')
  const [reviewLoading, setReviewLoading] = useState(false)
  const [reviewError, setReviewError] = useState('')

  const config = APPLICATION_TYPES[applicationType]

  const documentCards = useMemo(
    () => [...config.requiredDocuments, ...config.optionalDocuments],
    [config],
  )

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/applications')
      const payload = await response.json()
      setHistory(payload.results || [])
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  useEffect(() => {
    setForm({ ...emptyForm })
    setFiles({})
    setResult(null)
    setError('')
    setUploadError('')
  }, [applicationType])

  const handleFieldChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const setSelectedFile = (key, file) => {
    if (!file) return
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!['png', 'jpg', 'jpeg', 'pdf'].includes(extension)) {
      setUploadError('Choose a PDF, PNG, JPG, or JPEG document.')
      return
    }
    setUploadError('')
    setFiles((prev) => ({ ...prev, [key]: file }))
    setResult(null)
  }

  const handleFileChange = (event) => {
    setSelectedFile(event.target.name, event.target.files?.[0])
  }

  const handleFileDrop = (event, key) => {
    event.preventDefault()
    setSelectedFile(key, event.dataTransfer.files?.[0])
  }

  const removeFile = (key) => {
    setFiles((prev) => {
      const next = { ...prev }
      delete next[key]
      return next
    })
    setResult(null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setUploadError('')

    const formData = new FormData()
    formData.append('application_type', applicationType)

    Object.entries(form).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        formData.append(key, value)
      }
    })

    documentCards.forEach(({ key }) => {
      if (files[key]) {
        formData.append(key, files[key])
      }
    })

    try {
      const response = await fetch('/api/applications/verify', {
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
      setError(err.message || 'Unable to verify application')
    } finally {
      setLoading(false)
    }
  }

  const fetchReport = async (applicationId) => {
    if (!applicationId) return
    if (historyIssueId === applicationId) {
      setHistoryIssueId('')
      setHistoryIssue(null)
      setHistoryIssueError('')
      return
    }

    setHistoryIssueId(applicationId)
    setHistoryIssue(null)
    setHistoryIssueError('')
    setHistoryIssueLoading(true)
    try {
      const response = await fetch(`/api/applications/${applicationId}`)
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || 'Application not found')
      }
      setHistoryIssue(payload)
      setResult(payload)
    } catch (err) {
      setHistoryIssueError(err.message || 'Unable to fetch issue details')
    } finally {
      setHistoryIssueLoading(false)
    }
  }

  const resolveManualReview = async (action) => {
    const applicationId = result?.application_id || result?.id
    if (!applicationId) return

    setReviewLoading(true)
    setReviewError('')
    try {
      const formData = new FormData()
      formData.append('action', action)
      const response = await fetch(`/api/applications/${applicationId}/review`, {
        method: 'POST',
        body: formData,
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || 'Unable to save reviewer decision')
      }

      setResult(payload)
      setHistoryIssue(payload)
      await fetchHistory()
    } catch (err) {
      setReviewError(err.message || 'Unable to save reviewer decision')
    } finally {
      setReviewLoading(false)
    }
  }

  const deleteApplication = async (applicationId) => {
    if (!applicationId) return

    const confirmed = window.confirm('Delete this application from history?')
    if (!confirmed) return

    try {
      const response = await fetch(`/api/applications/${applicationId}`, {
        method: 'DELETE',
      })
      const payload = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(payload.detail || 'Unable to delete application')
      }

      setHistory((prev) => prev.filter((item) => (item.id || item.application_id) !== applicationId))
      if (historyIssueId === applicationId) {
        setHistoryIssueId('')
        setHistoryIssue(null)
      }
      if (result && ((result.id || result.application_id) === applicationId)) {
        setResult(null)
      }
      await fetchHistory()
    } catch (err) {
      setError(err.message || 'Unable to delete application')
    }
  }

  const statusClass = (status) => {
    if (!status) return 'status-badge neutral'
    const normalized = String(status).toUpperCase()
    if (normalized === 'COMPLETE') return 'status-badge success'
    if (normalized === 'MANUAL REVIEW' || normalized === 'MANUAL_REVIEW') return 'status-badge warning'
    return 'status-badge danger'
  }

  const getFieldMeta = (field) => `${field.label}${field.required ? ' *' : ''}`

  const getIssueSummary = (payload) => {
    if (payload?.review_decision === 'verified') return ['Application marked as verified by a reviewer.']

    const missingDocuments = (payload?.missing_documents || []).map((item) => `${item.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())} is missing.`)
    const validationIssues = (payload?.validation_results || []).filter((item) => !/required documents available for review/i.test(item))
    const issues = [...new Set([...(payload?.issues || []), ...missingDocuments, ...validationIssues])]

    if (issues.length) return issues.slice(0, 5)

    const status = String(payload?.overall_status || payload?.status || '').toUpperCase()
    if (status === 'COMPLETE') return ['No issue detected. Application is complete and ready for review.']

    const actions = (payload?.recommended_actions || []).filter((item) => !/no correction required/i.test(item))
    if (actions.length) return actions.slice(0, 5)

    return [`No specific issue details were saved for this older record. Recorded status: ${status || 'UNKNOWN'}.`]
  }

  const getManualReviewReason = (payload) => {
    const issues = payload?.issues || []
    if (issues.some((issue) => /could not be read reliably|text could not be extracted/i.test(issue))) {
      return 'Document text could not be extracted.'
    }
    if (issues.some((issue) => /could not be confidently identified/i.test(issue))) {
      return 'The document type could not be identified with enough confidence.'
    }
    return issues[0] || 'The system could not confidently process this document automatically.'
  }

  const getUploadStatus = (key) => {
    if (!result) return files[key] ? 'Ready to verify' : 'Waiting'
    const documents = result.detected_documents || result.documents || []
    const item = documents.find((entry) => entry.key_name === key || entry.expected_type === key)
    if (!item) {
      if ((result.missing_documents || []).includes(key)) return 'Missing'
      return files[key] ? 'Ready to verify' : 'Not processed'
    }
    const status = String(item.status || '').toUpperCase().replace(/[ -]+/g, '_')
    if (status === 'VALID') return 'Validated'
    if (status === 'WRONG_DOCUMENT') return 'Wrong document'
    if (status === 'INCOMPLETE') return 'Incomplete'
    if (status === 'MANUAL_REVIEW') return 'Manual review'
    return status.replace(/_/g, ' ') || 'Not processed'
  }

  const getDetectedType = (key) => {
    if (!result) return 'Not processed'
    const documents = result.detected_documents || result.documents || []
    const item = documents.find((entry) => entry.key_name === key || entry.expected_type === key)
    if (!item) return 'Not processed'
    const detectedType = item.detected_document_type || item.detected_type || 'Unknown Document'
    const confidence = Number(item.confidence || 0)
    const confidencePercent = confidence <= 1 ? Math.round(confidence * 100) : Math.round(confidence)
    return `${detectedType.replace(/_/g, ' ')} · ${confidencePercent}%`
  }

  const formatDocumentLabel = (value) => String(value || 'Document')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())

  const getStatusDescription = (status) => {
    const normalized = String(status || '').toUpperCase()
    if (normalized === 'COMPLETE') return 'All required checks passed. This application is ready for review.'
    if (normalized === 'MANUAL_REVIEW') return 'A document needs a person to inspect it before a decision can be made.'
    return 'One or more details need correction before this application can proceed.'
  }

  const visibleHistory = history.filter((entry) => {
    const searchableText = `${entry.id || ''} ${entry.application_id || ''} ${entry.applicant_name || ''} ${entry.applicant || ''}`.toLowerCase()
    const normalizedStatus = String(entry.status || entry.overall_status || '').trim().replace(/[ -]+/g, '_').toUpperCase()
    const matchesSearch = !searchTerm || searchableText.includes(searchTerm.trim().toLowerCase())
    const matchesStatus = statusFilter === 'all' || normalizedStatus === statusFilter
    const matchesType = typeFilter === 'all' || (entry.application_type || entry.type || '').toLowerCase() === typeFilter
    return matchesSearch && matchesStatus && matchesType
  })

  const summaryCounts = {
    total: history.length,
    complete: history.filter((entry) => (entry.status || entry.overall_status || '').toUpperCase() === 'COMPLETE').length,
    needsCorrection: history.filter((entry) => (entry.status || entry.overall_status || '').toUpperCase() === 'NEEDS_CORRECTION').length,
    manualReview: history.filter((entry) => (entry.status || entry.overall_status || '').toUpperCase() === 'MANUAL_REVIEW').length,
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <span className="top-badge">Smart Application Processing &amp; Verification Platform</span>
          <h1>Smart Application Processing &amp; Verification Platform</h1>
        </div>
      </header>

      <section className="stats-grid">
        <div className="stat-card accent">
          <span className="stat-label">Applications</span>
          <strong>{summaryCounts.total}</strong>
          <small>Total records</small>
        </div>
        <div className="stat-card success">
          <span className="stat-label">Complete</span>
          <strong>{summaryCounts.complete}</strong>
          <small>Ready for review</small>
        </div>
        <div className="stat-card warning">
          <span className="stat-label">Needs Correction</span>
          <strong>{summaryCounts.needsCorrection}</strong>
          <small>Action required</small>
        </div>
        <div className="stat-card danger">
          <span className="stat-label">Manual Review</span>
          <strong>{summaryCounts.manualReview}</strong>
          <small>Low confidence</small>
        </div>
      </section>

      <section className="type-selector panel">
        <div className="panel-header">
          <h2>Application Type</h2>
        </div>
        <div className="application-cards">
          {Object.values(APPLICATION_TYPES).map((appType) => (
            <button
              type="button"
              key={appType.key}
              className={`type-card ${applicationType === appType.key ? 'selected' : ''}`}
              onClick={() => setApplicationType(appType.key)}
              aria-pressed={applicationType === appType.key}
            >
              <span className="type-icon">{appType.icon}</span>
              <span className="type-title">{appType.title}</span>
              <span className="type-description">{appType.description}</span>
            </button>
          ))}
        </div>
      </section>

      <main className="content-grid">
        <div className="main-panel panel">
          <form onSubmit={handleSubmit}>
            <div className="panel-header">
              <h2>{config.title}</h2>
            </div>
            <p className="helper-copy">Upload real supporting documents. A readable document can satisfy more than one proof requirement when it matches the applicant details.</p>

            <div className="field-grid">
              {config.fields.map((field) => (
                <label key={field.key} className={field.key === 'address' ? 'full-span' : ''}>
                  <span>{getFieldMeta(field)}</span>
                  {field.type === 'select' ? (
                    <select value={form[field.key] || ''} onChange={(e) => handleFieldChange(field.key, e.target.value)}>
                      <option value="">Select...</option>
                      <option value="Merit Scholarship">Merit Scholarship</option>
                      <option value="Need-based Scholarship">Need-based Scholarship</option>
                      <option value="Research Grant">Research Grant</option>
                      <option value="Student Pass">Student Pass</option>
                    </select>
                  ) : (
                    <input
                      type={field.type}
                      value={form[field.key] || ''}
                      onChange={(e) => handleFieldChange(field.key, e.target.value)}
                      placeholder={field.label}
                    />
                  )}
                </label>
              ))}
            </div>

            <div className="document-upload-panel">
              <div className="panel-header compact">
                <h3>Required Documents</h3>
              </div>
              <div className="upload-grid">
                {documentCards.map(({ key, label, required }) => (
                  <div key={key} className="upload-card">
                    <div className="upload-header">
                      <span>{label}</span>
                      <span className={required ? 'required-tag' : 'optional-tag'}>{required ? 'Required' : 'Optional'}</span>
                    </div>

                        <label
                          className={`drop-zone ${files[key] ? 'has-file' : ''}`}
                          onDragOver={(event) => event.preventDefault()}
                          onDrop={(event) => handleFileDrop(event, key)}
                        >
                      <input type="file" name={key} onChange={handleFileChange} accept=".png,.jpg,.jpeg,.pdf" />
                          <span>{files[key] ? 'Drop to replace or choose another file' : 'Drag &amp; drop or choose file'}</span>
                    </label>

                    <div className="upload-meta">
                          <div className="selected-file">
                            <span><strong>Selected:</strong> {files[key] ? files[key].name : 'No file'}</span>
                            {files[key] && <button type="button" className="remove-file" onClick={() => removeFile(key)} aria-label={`Remove ${label}`}>Remove</button>}
                          </div>
                      <div><strong>Detected:</strong> {getDetectedType(key)}</div>
                          <div><strong>Status:</strong> <span className={`status-chip ${['Validated', 'Ready to verify'].includes(getUploadStatus(key)) ? 'ok' : ['Wrong document', 'Missing'].includes(getUploadStatus(key)) ? 'warn' : getUploadStatus(key).includes('Manual') ? 'manual' : 'idle'}`}>{getUploadStatus(key)}</span></div>
                    </div>
                  </div>
                ))}
              </div>
                  {uploadError && <div className="error-box" role="alert">{uploadError}</div>}
            </div>

            {loading && (
                  <div className="progress-panel" role="status" aria-live="polite">
                    <div className="progress-heading"><span className="progress-spinner" aria-hidden="true" /> Verifying application</div>
                    <p>Documents are being uploaded, read, and checked for consistency. This may take a moment.</p>
                    <div className="progress-line indeterminate" role="progressbar" aria-label="Verification in progress">
                      <span />
                </div>
              </div>
            )}

            {error && <div className="error-box">{error}</div>}

            <button className="submit-btn" type="submit" disabled={loading}>
              {loading ? 'Verifying...' : `Verify ${config.title}`}
            </button>
          </form>
        </div>

        <aside className="result-panel panel">
          {result ? (
            <>
              <div className="panel-header">
                <h2>Verification Result</h2>
                <span className={statusClass(result.overall_status || result.status)}>{result.overall_status || result.status}</span>
              </div>
              <p className="status-explainer">{getStatusDescription(result.overall_status || result.status)}</p>

              <div className="result-summary">
                <div>
                  <span>Application ID</span>
                  <strong>{result.application_id || result.id}</strong>
                </div>
                <div>
                  <span>Applicant</span>
                  <strong>{result.applicant?.name || result.applicant_name || 'Unknown'}</strong>
                </div>
                <div>
                  <span>Type</span>
                  <strong>{result.application_type || applicationType}</strong>
                </div>
              </div>

              {String(result.overall_status || result.status).toUpperCase() === 'MANUAL_REVIEW' && !result.review_decision && (
                <section className="manual-review-card" aria-labelledby="manual-review-title">
                  <div className="manual-review-heading">
                    <span aria-hidden="true">🔎</span>
                    <h3 id="manual-review-title">MANUAL REVIEW REQUIRED</h3>
                  </div>
                  <p>The system could not confidently process this document automatically.</p>
                  <dl>
                    <div>
                      <dt>Reason</dt>
                      <dd>{getManualReviewReason(result)}</dd>
                    </div>
                    <div>
                      <dt>Action</dt>
                      <dd>A reviewer should inspect the document.</dd>
                    </div>
                  </dl>
                  <div className="manual-review-actions">
                    <button type="button" className="review-verify" onClick={() => resolveManualReview('verified')} disabled={reviewLoading}>
                      {reviewLoading ? 'Saving...' : 'Mark as Verified'}
                    </button>
                    <button type="button" className="review-correction" onClick={() => resolveManualReview('correction')} disabled={reviewLoading}>
                      Request Correction
                    </button>
                  </div>
                  {reviewError && <p className="manual-review-error" role="alert">{reviewError}</p>}
                </section>
              )}

              {result.review_decision && (
                <div className="review-decision-note" role="status">
                  <strong>Reviewer decision saved</strong>
                  <p>{result.review_note}</p>
                  {result.reviewed_at && <small>{result.reviewed_at}</small>}
                </div>
              )}

              <div className="result-block action-box">
                <h3>Actual Issue Summary</h3>
                <ul>
                  {getIssueSummary(result).map((item, index) => (
                    <li key={`${item}-${index}`}>• {item}</li>
                  ))}
                </ul>
              </div>

              <div className="result-block">
                <h3>Missing Documents</h3>
                <ul>
                  {(result.missing_documents || []).length ? (
                    (result.missing_documents || []).map((item) => <li key={item}>• {formatDocumentLabel(item)}</li>)
                  ) : (
                    <li>None</li>
                  )}
                </ul>
              </div>

              <div className="result-block">
                <h3>Document Checks</h3>
                <ul>
                  {(result.detected_documents || result.documents || []).length ? (
                    (result.detected_documents || result.documents || []).map((document, index) => {
                      const expected = document.key_name || document.expected_type
                      const detected = document.detected_document_type || document.detected_type || 'unknown'
                      const confidence = Number(document.confidence || 0)
                      const confidencePercent = confidence <= 1 ? Math.round(confidence * 100) : Math.round(confidence)
                      return (
                        <li key={`${expected}-${index}`}>
                          <strong>{formatDocumentLabel(expected)}</strong> expected; detected {formatDocumentLabel(detected)} ({confidencePercent}% confidence).
                          {document.status && <span className={`document-check-status ${String(document.status).toUpperCase() === 'VALID' ? 'valid' : 'needs-attention'}`}>{String(document.status).replace(/_/g, ' ')}</span>}
                          {document.reason && <small className="document-check-reason">{document.reason}</small>}
                        </li>
                      )
                    })
                  ) : (
                    <li>No documents were processed.</li>
                  )}
                </ul>
              </div>

              <div className="result-block">
                <h3>Consistency Checks</h3>
                <ul>
                  {(result.issues || []).filter((item) => /(applicant name|date of birth|institution|course|annual income|academic score|address).*?(does not match|differs)/i.test(item)).length ? (
                    (result.issues || []).filter((item) => /(applicant name|date of birth|institution|course|annual income|academic score|address).*?(does not match|differs)/i.test(item)).map((item, index) => <li key={index}>{item}</li>)
                  ) : (
                    <li>No critical mismatches detected.</li>
                  )}
                </ul>
              </div>

              <div className="result-block action-box">
                <h3>Recommended Actions</h3>
                <ul>
                  {(result.recommended_actions || []).length ? (
                    (result.recommended_actions || []).map((item, index) => <li key={index}>• {item}</li>)
                  ) : (
                    <li>No action required.</li>
                  )}
                </ul>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <h2>Verification dashboard</h2>
              <p>Submit an application to see document-level verification results.</p>
            </div>
          )}
        </aside>
      </main>

      <section className="history-panel panel">
        <div className="panel-header compact">
          <h2>Application History</h2>
          <div className="history-filters">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search applicant or application ID"
              aria-label="Search applicant or application ID"
            />
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} aria-label="Filter by status">
              <option value="all">All Statuses</option>
              <option value="COMPLETE">Complete</option>
              <option value="NEEDS_CORRECTION">Needs Correction</option>
              <option value="MANUAL_REVIEW">Manual Review</option>
            </select>
            <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} aria-label="Filter by application type">
              <option value="all">All Types</option>
              {Object.values(APPLICATION_TYPES).map((appType) => (
                <option key={appType.key} value={appType.key}>{appType.title}</option>
              ))}
            </select>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Applicant</th>
              <th>Type</th>
              <th>Status</th>
              <th>Documents</th>
              <th>Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {visibleHistory.length ? (
              visibleHistory.map((item) => {
                const applicationId = item.id || item.application_id
                const issueIsOpen = historyIssueId === applicationId

                return (
                  <Fragment key={applicationId}>
                    <tr>
                      <td>{applicationId}</td>
                      <td>{item.applicant_name || item.applicant?.name || 'Unknown'}</td>
                      <td>{item.application_type || item.type || 'Unknown'}</td>
                      <td><span className={statusClass(item.status || item.overall_status)}>{item.status || item.overall_status}</span></td>
                      <td>{item.document_count || item.documents?.length || 0}</td>
                      <td>{item.created_at || item.date || 'N/A'}</td>
                      <td>
                        <div className="history-actions">
                          <button type="button" className="mini-action" onClick={() => fetchReport(applicationId)}>
                            {issueIsOpen ? 'Hide issue' : 'View issue'}
                          </button>
                          <details className="history-menu">
                            <summary className="history-menu-trigger" aria-label="More history actions" title="More actions">
                              ⋮
                            </summary>
                            <div className="history-menu-popover">
                              <button type="button" className="mini-action danger" onClick={() => deleteApplication(applicationId)}>
                                Delete
                              </button>
                            </div>
                          </details>
                        </div>
                      </td>
                    </tr>
                    {issueIsOpen && (
                      <tr className="history-issue-row">
                        <td colSpan="7">
                          <div className="history-issue-detail">
                            <h3>Actual issue</h3>
                            {historyIssueLoading ? (
                              <p>Loading issue details...</p>
                            ) : historyIssueError ? (
                              <p className="history-issue-error">{historyIssueError}</p>
                            ) : (
                              <ul>
                                {getIssueSummary(historyIssue).map((issue, index) => (
                                  <li key={`${applicationId}-${index}`}>{issue}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })
            ) : (
              <tr>
                <td colSpan="7">No matching applications found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}

export default App
