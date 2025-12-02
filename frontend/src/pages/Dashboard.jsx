import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'

const Dashboard = () => {
  const { user, isSuperAdmin } = useAuth()
  const [stats, setStats] = useState({ users: 0, roles: 0, groups: 0 })
  const [userRoles, setUserRoles] = useState([])
  const [userGroups, setUserGroups] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isSuperAdmin) {
      fetchStats()
    } else {
      fetchUserInfo()
    }
  }, [isSuperAdmin])

  const fetchStats = async () => {
    try {
      const [usersRes, rolesRes, groupsRes] = await Promise.all([
        api.get('/users'),
        api.get('/roles'),
        api.get('/groups')
      ])

      setStats({
        users: usersRes.data.total || 0,
        roles: rolesRes.data.total || 0,
        groups: groupsRes.data.total || 0
      })
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchUserInfo = async () => {
    try {
      if (user?.id) {
        const [rolesRes, groupsRes] = await Promise.all([
          api.get(`/users/${user.id}/roles`),
          api.get(`/users/${user.id}/groups`)
        ])

        setUserRoles(rolesRes.data.roles || [])
        setUserGroups(groupsRes.data.groups || [])
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div>
      <h1 style={{ marginBottom: '30px' }}>Dashboard</h1>
      
      <div className="card">
        <h2 style={{ marginBottom: '20px' }}>Welcome, {user?.username}!</h2>
        <p style={{ color: '#666', marginBottom: '10px' }}>
          <strong>Email:</strong> {user?.email || 'N/A'}
        </p>
        <p style={{ color: '#666', marginBottom: '10px' }}>
          <strong>Name:</strong> {user?.name || 'N/A'}
        </p>
        <p style={{ color: '#666' }}>
          <strong>User ID:</strong> {user?.id}
        </p>
      </div>

      {isSuperAdmin ? (
        // Superadmin view - Show statistics
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginTop: '20px' }}>
          <div className="card" style={{ textAlign: 'center' }}>
            <h3 style={{ color: '#007bff', fontSize: '48px', margin: '20px 0' }}>{stats.users}</h3>
            <p style={{ color: '#666', fontSize: '18px' }}>Total Users</p>
          </div>

          <div className="card" style={{ textAlign: 'center' }}>
            <h3 style={{ color: '#28a745', fontSize: '48px', margin: '20px 0' }}>{stats.roles}</h3>
            <p style={{ color: '#666', fontSize: '18px' }}>Total Roles</p>
          </div>

          <div className="card" style={{ textAlign: 'center' }}>
            <h3 style={{ color: '#ffc107', fontSize: '48px', margin: '20px 0' }}>{stats.groups}</h3>
            <p style={{ color: '#666', fontSize: '18px' }}>Total Groups</p>
          </div>
        </div>
      ) : (
        // Regular user view - Show their roles and groups
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px', marginTop: '20px' }}>
          <div className="card">
            <h3 style={{ marginBottom: '15px', color: '#007bff' }}>My Roles</h3>
            {userRoles.length > 0 ? (
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {userRoles.filter(r => !['default-roles-iam-realm-v2', 'offline_access', 'uma_authorization'].includes(r.name)).map(role => (
                  <li key={role.id} style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>
                    <strong>{role.name}</strong>
                    {role.description && <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '14px' }}>{role.description}</p>}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ color: '#666' }}>No roles assigned</p>
            )}
          </div>

          <div className="card">
            <h3 style={{ marginBottom: '15px', color: '#28a745' }}>My Groups</h3>
            {userGroups.length > 0 ? (
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {userGroups.map(group => (
                  <li key={group.id} style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>
                    <strong>{group.name}</strong>
                    <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '14px' }}>{group.path}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ color: '#666' }}>No group memberships</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
