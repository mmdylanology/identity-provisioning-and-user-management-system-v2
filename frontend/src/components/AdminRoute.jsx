import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const AdminRoute = ({ children }) => {
  const { user, loading, isSuperAdmin } = useAuth()

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (!isSuperAdmin) {
    return (
      <div className="container">
        <div className="card" style={{ marginTop: '40px', textAlign: 'center', padding: '40px' }}>
          <h2 style={{ color: '#dc3545', marginBottom: '20px' }}>Access Denied</h2>
          <p style={{ color: '#666', fontSize: '18px', marginBottom: '20px' }}>
            You do not have permission to access this page.
          </p>
          <p style={{ color: '#666' }}>
            Only users with the <strong>realm-admin</strong> role can access administrative features.
          </p>
          <button 
            onClick={() => window.location.href = '/dashboard'} 
            className="btn btn-primary"
            style={{ marginTop: '20px' }}
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return children
}

export default AdminRoute
