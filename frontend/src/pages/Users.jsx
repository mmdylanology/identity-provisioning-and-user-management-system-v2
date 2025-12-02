import React, { useState, useEffect } from 'react'
import api from '../api/axios'

const Users = () => {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [roles, setRoles] = useState([])
  const [groups, setGroups] = useState([])
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    firstName: '',
    lastName: '',
    password: '',
    enabled: true,
    roles: [],
    groups: []
  })

  useEffect(() => {
    fetchUsers()
    fetchRolesAndGroups()
  }, [searchTerm])

  const fetchRolesAndGroups = async () => {
    try {
      const [rolesRes, groupsRes] = await Promise.all([
        api.get('/roles'),
        api.get('/groups')
      ])
      setRoles(rolesRes.data.roles || [])
      setGroups(groupsRes.data.groups || [])
    } catch (err) {
      console.error('Failed to fetch roles/groups:', err)
    }
  }

  const fetchUsers = async () => {
    try {
      const params = searchTerm ? { search: searchTerm } : {}
      const response = await api.get('/users', { params })
      setUsers(response.data.users || [])
      setError('')
    } catch (err) {
      setError('Failed to fetch users')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    try {
      if (editingUser) {
        // Update user basic info
        await api.put(`/users/${editingUser.id}`, {
          email: formData.email,
          firstName: formData.firstName,
          lastName: formData.lastName,
          enabled: formData.enabled
        })
        
        // Get current roles and groups
        const [currentRolesRes, currentGroupsRes] = await Promise.all([
          api.get(`/users/${editingUser.id}/roles`),
          api.get(`/users/${editingUser.id}/groups`)
        ])
        
        const currentRoles = currentRolesRes.data.roles
          .filter(r => !['default-roles-iam-realm-v2', 'offline_access', 'uma_authorization'].includes(r.name))
          .map(r => r.name)
        
        const currentGroups = currentGroupsRes.data.groups.map(g => ({ id: g.id, name: g.name }))
        
        // Handle role changes
        const rolesToAdd = formData.roles.filter(r => !currentRoles.includes(r))
        const rolesToRemove = currentRoles.filter(r => !formData.roles.includes(r))
        
        if (rolesToAdd.length > 0) {
          await api.post(`/users/${editingUser.id}/roles`, { roles: rolesToAdd })
        }
        
        if (rolesToRemove.length > 0) {
          await api.delete(`/users/${editingUser.id}/roles`, { data: { roles: rolesToRemove } })
        }
        
        // Handle group changes
        const currentGroupNames = currentGroups.map(g => g.name)
        const groupsToAdd = formData.groups.filter(g => !currentGroupNames.includes(g))
        const groupsToRemove = currentGroups.filter(g => !formData.groups.includes(g.name))
        
        // Add to new groups
        if (groupsToAdd.length > 0) {
          const allGroups = await api.get('/groups')
          const groupMap = {}
          allGroups.data.groups.forEach(g => { groupMap[g.name] = g.id })
          
          for (const groupName of groupsToAdd) {
            if (groupMap[groupName]) {
              await api.put(`/users/${editingUser.id}/groups/${groupMap[groupName]}`)
            }
          }
        }
        
        // Remove from old groups
        for (const group of groupsToRemove) {
          await api.delete(`/users/${editingUser.id}/groups/${group.id}`)
        }
      } else {
        await api.post('/users', formData)
      }
      
      setShowModal(false)
      resetForm()
      fetchUsers()
    } catch (err) {
      setError(err.response?.data?.detail || 'Operation failed')
    }
  }

  const handleDelete = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return
    }

    try {
      await api.delete(`/users/${userId}`)
      fetchUsers()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete user')
    }
  }

  const handleEdit = async (user) => {
    setEditingUser(user)
    
    // Fetch user's current roles and groups
    try {
      const [rolesRes, groupsRes] = await Promise.all([
        api.get(`/users/${user.id}/roles`),
        api.get(`/users/${user.id}/groups`)
      ])
      
      const userRoles = rolesRes.data.roles
        .filter(r => !['default-roles-iam-realm-v2', 'offline_access', 'uma_authorization'].includes(r.name))
        .map(r => r.name)
      
      const userGroups = groupsRes.data.groups.map(g => g.name)
      
      setFormData({
        username: user.username,
        email: user.email || '',
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        password: '',
        enabled: user.enabled !== false,
        roles: userRoles,
        groups: userGroups
      })
    } catch (err) {
      console.error('Failed to fetch user roles/groups:', err)
      setFormData({
        username: user.username,
        email: user.email || '',
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        password: '',
        enabled: user.enabled !== false,
        roles: [],
        groups: []
      })
    }
    
    setShowModal(true)
  }

  const resetForm = () => {
    setEditingUser(null)
    setFormData({
      username: '',
      email: '',
      firstName: '',
      lastName: '',
      password: '',
      enabled: true,
      roles: [],
      groups: []
    })
  }

  const openCreateModal = () => {
    resetForm()
    setShowModal(true)
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Users</h1>
        <button onClick={openCreateModal} className="btn btn-primary">
          Create User
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <div className="form-group">
          <input
            type="text"
            className="form-control"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>First Name</th>
              <th>Last Name</th>
              <th>Enabled</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>
                  No users found
                </td>
              </tr>
            ) : (
              users.map(user => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>{user.firstName}</td>
                  <td>{user.lastName}</td>
                  <td>{user.enabled ? '✓' : '✗'}</td>
                  <td>
                    <button 
                      onClick={() => handleEdit(user)} 
                      className="btn btn-primary"
                      style={{ marginRight: '10px', padding: '5px 10px' }}
                    >
                      Edit
                    </button>
                    <button 
                      onClick={() => handleDelete(user.id)} 
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
              <h2>{editingUser ? 'Edit User' : 'Create User'}</h2>
              <button onClick={() => setShowModal(false)} className="modal-close">×</button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Username *</label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                  disabled={!!editingUser}
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  className="form-control"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>First Name</label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.firstName}
                  onChange={(e) => setFormData({...formData, firstName: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Last Name</label>
                <input
                  type="text"
                  className="form-control"
                  value={formData.lastName}
                  onChange={(e) => setFormData({...formData, lastName: e.target.value})}
                />
              </div>

              {!editingUser && (
                <div className="form-group">
                  <label>Password *</label>
                  <input
                    type="password"
                    className="form-control"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    required={!editingUser}
                  />
                </div>
              )}

              <div className="form-group">
                <label>Roles (Hold Ctrl/Cmd to select multiple)</label>
                <select
                  multiple
                  className="form-control"
                  value={formData.roles}
                  onChange={(e) => {
                    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value)
                    setFormData({...formData, roles: selectedOptions})
                  }}
                  style={{ minHeight: '100px' }}
                >
                  {roles.filter(r => !['default-roles-iam-realm-v2', 'offline_access', 'uma_authorization'].includes(r.name)).map(role => (
                    <option key={role.id} value={role.name}>
                      {role.name}
                    </option>
                  ))}
                </select>
                <small className="form-text text-muted">
                  Selected: {formData.roles.length > 0 ? formData.roles.join(', ') : 'None'}
                </small>
              </div>

              <div className="form-group">
                <label>Groups (Optional - Hold Ctrl/Cmd to select multiple)</label>
                <select
                  multiple
                  className="form-control"
                  value={formData.groups}
                  onChange={(e) => {
                    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value)
                    setFormData({...formData, groups: selectedOptions})
                  }}
                  style={{ minHeight: '100px' }}
                >
                  {groups.map(group => (
                    <option key={group.id} value={group.name}>
                      {group.name}
                    </option>
                  ))}
                </select>
                <small className="form-text text-muted">
                  Selected: {formData.groups.length > 0 ? formData.groups.join(', ') : 'None'}
                </small>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => setFormData({...formData, enabled: e.target.checked})}
                    style={{ marginRight: '5px' }}
                  />
                  Enabled
                </label>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingUser ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Users
