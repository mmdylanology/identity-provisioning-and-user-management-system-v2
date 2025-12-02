import React, { useState, useEffect } from 'react'
import api from '../api/axios'

const Roles = () => {
  const [roles, setRoles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [newRoleName, setNewRoleName] = useState('')

  useEffect(() => {
    fetchRoles()
  }, [])

  const fetchRoles = async () => {
    try {
      const response = await api.get('/roles')
      setRoles(response.data.roles || [])
      setError('')
    } catch (err) {
      setError('Failed to fetch roles')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')

    try {
      await api.post('/roles', { name: newRoleName })
      setShowModal(false)
      setNewRoleName('')
      fetchRoles()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create role')
    }
  }

  const handleDelete = async (roleName) => {
    if (!window.confirm(`Are you sure you want to delete role "${roleName}"?`)) {
      return
    }

    try {
      await api.delete(`/roles/${roleName}`)
      fetchRoles()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete role')
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Roles</h1>
        <button onClick={() => setShowModal(true)} className="btn btn-primary">
          Create Role
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {roles.length === 0 ? (
              <tr>
                <td colSpan="3" style={{ textAlign: 'center', padding: '20px' }}>
                  No roles found
                </td>
              </tr>
            ) : (
              roles.map(role => (
                <tr key={role.name}>
                  <td>{role.name}</td>
                  <td>{role.description || '-'}</td>
                  <td>
                    <button 
                      onClick={() => handleDelete(role.name)} 
                      className="btn btn-danger"
                      style={{ padding: '5px 10px' }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal">
          <div className="modal-content">
            <div className="modal-header">
              <h2>Create Role</h2>
              <button onClick={() => setShowModal(false)} className="modal-close">×</button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Role Name *</label>
                <input
                  type="text"
                  className="form-control"
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  required
                  placeholder="e.g., developer, analyst"
                />
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Roles
