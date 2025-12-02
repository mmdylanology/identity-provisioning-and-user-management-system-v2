import React, { useState, useEffect } from 'react'
import api from '../api/axios'

const Groups = () => {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')

  useEffect(() => {
    fetchGroups()
  }, [])

  const fetchGroups = async () => {
    try {
      const response = await api.get('/groups')
      setGroups(response.data.groups || [])
      setError('')
    } catch (err) {
      setError('Failed to fetch groups')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')

    try {
      await api.post('/groups', { name: newGroupName })
      setShowModal(false)
      setNewGroupName('')
      fetchGroups()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create group')
    }
  }

  const handleDelete = async (groupId) => {
    if (!window.confirm('Are you sure you want to delete this group?')) {
      return
    }

    try {
      await api.delete(`/groups/${groupId}`)
      fetchGroups()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete group')
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Groups</h1>
        <button onClick={() => setShowModal(true)} className="btn btn-primary">
          Create Group
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Path</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {groups.length === 0 ? (
              <tr>
                <td colSpan="3" style={{ textAlign: 'center', padding: '20px' }}>
                  No groups found
                </td>
              </tr>
            ) : (
              groups.map(group => (
                <tr key={group.id}>
                  <td>{group.name}</td>
                  <td>{group.path}</td>
                  <td>
                    <button 
                      onClick={() => handleDelete(group.id)} 
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
              <h2>Create Group</h2>
              <button onClick={() => setShowModal(false)} className="modal-close">×</button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Group Name *</label>
                <input
                  type="text"
                  className="form-control"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  required
                  placeholder="e.g., engineering, marketing"
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

export default Groups
