import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

export const AppLayout: React.FC = () => {
  return (
    <div className="d-flex" style={{ minHeight: '100vh', width: '100vw' }}>
      {/* Sidebar Navigation */}
      <nav className="bg-dark text-white p-3 d-flex flex-column" style={{ width: '260px', minWidth: '260px' }}>
        <div className="d-flex align-items-center mb-4 text-decoration-none text-white">
          <i className="bi bi-mic-fill me-2 fs-4 text-primary"></i>
          <span className="fs-5 fw-bold tracking-tight">Auralis V2</span>
        </div>

        <hr className="bg-secondary" />

        <ul className="nav nav-pills flex-column mb-auto">
          <li className="nav-item mb-2">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `nav-link d-flex align-items-center text-white ${isActive ? 'active bg-primary' : 'hover-opacity'}`
              }
            >
              <i className="bi bi-speedometer2 me-2"></i>
              Dashboard
            </NavLink>
          </li>
          <li className="nav-item mb-2">
            <NavLink
              to="/assistant"
              className={({ isActive }) =>
                `nav-link d-flex align-items-center text-white ${isActive ? 'active bg-primary' : 'hover-opacity'}`
              }
            >
              <i className="bi bi-chat-left-dots me-2"></i>
              Assistant
            </NavLink>
          </li>
          <li className="nav-item mb-2">
            <NavLink
              to="/files"
              className={({ isActive }) =>
                `nav-link d-flex align-items-center text-white ${isActive ? 'active bg-primary' : 'hover-opacity'}`
              }
            >
              <i className="bi bi-folder2-open me-2"></i>
              File Manager
            </NavLink>
          </li>
          <li className="nav-item mb-2">
            <NavLink
              to="/workspace"
              className={({ isActive }) =>
                `nav-link d-flex align-items-center text-white ${isActive ? 'active bg-primary' : 'hover-opacity'}`
              }
            >
              <i className="bi bi-kanban me-2"></i>
              Workspace
            </NavLink>
          </li>
          <li className="nav-item mb-2">
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `nav-link d-flex align-items-center text-white ${isActive ? 'active bg-primary' : 'hover-opacity'}`
              }
            >
              <i className="bi bi-gear me-2"></i>
              Settings
            </NavLink>
          </li>
        </ul>

        <hr className="bg-secondary" />
        
        <div className="d-flex align-items-center text-white small">
          <i className="bi bi-info-circle me-2 text-info"></i>
          <span>Phase 16.1 Foundation</span>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="d-flex flex-column flex-grow-1 bg-light">
        {/* Top Navbar */}
        <header className="navbar navbar-expand-lg navbar-light bg-white border-bottom px-4 py-3">
          <div className="container-fluid p-0">
            <span className="navbar-brand mb-0 h1 fs-5 fw-semibold text-secondary">
              Voice File Manager
            </span>
            <div className="d-flex align-items-center">
              <i className="bi bi-bell-fill me-3 text-secondary fs-5 cursor-pointer"></i>
              <div className="rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center" style={{ width: '32px', height: '32px' }}>
                A
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Route Content */}
        <main className="flex-grow-1 p-4 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
