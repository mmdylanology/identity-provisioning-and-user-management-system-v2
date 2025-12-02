import React from 'react'
import { Outlet, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Layout = () => {
  const { user, logout, isSuperAdmin } = useAuth()

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  return (
    <div>
      <nav className="navbar">
        <h1>IAM Admin Portal V2</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <Link to="/dashboard">Dashboard</Link>
          {isSuperAdmin && (
            <>
              <Link to="/users">Users</Link>
              <Link to="/roles">Roles</Link>
              <Link to="/groups">Groups</Link>
            </>
          )}
          <span style={{ color: '#666', margin: '0 10px' }}>|</span>
          <span style={{ color: '#ffffff', fontWeight: '600' }}>{user?.username}</span>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '5px 15px' }}>
            Logout
          </button>
        </div>
      </nav>
      <div className="container">
        <Outlet />
      </div>
    </div>
  )
}

export default Layout
