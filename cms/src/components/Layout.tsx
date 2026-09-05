import React from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";

export function Layout() {
  const navigate = useNavigate();
  const role = localStorage.getItem("role") || "";
  const username = localStorage.getItem("username") || "";

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("username");
    navigate("/login");
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h2>Peblo TV CMS</h2>
        <nav>
          <NavLink to="/shows" className={({ isActive }) => isActive ? "active" : ""}>
            Shows
          </NavLink>
          <NavLink to="/episodes" className={({ isActive }) => isActive ? "active" : ""}>
            Episodes
          </NavLink>
          <NavLink to="/publish" className={({ isActive }) => isActive ? "active" : ""}>
            Publish
          </NavLink>
        </nav>
        <div style={{ position: "absolute", bottom: 20, left: 0, right: 0, padding: "0 20px" }}>
          <div style={{ fontSize: 12, color: "#888", marginBottom: 8 }}>
            {username} <span className={`badge badge-${role === "admin" ? "published" : "draft"}`}>{role}</span>
          </div>
          <button onClick={logout} className="btn btn-secondary btn-sm" style={{ width: "100%" }}>
            Logout
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
