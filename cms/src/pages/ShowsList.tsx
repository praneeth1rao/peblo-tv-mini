import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Show } from "../types";

export function ShowsList() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [section, setSection] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const params: Record<string, string> = { offset: String(page * limit), limit: String(limit) };
  if (q) params.q = q;
  if (section) params.section = section;
  if (status) params.status = status;

  const { data: shows, isLoading, error } = useQuery({
    queryKey: ["shows", params],
    queryFn: () => api.listShows(params),
  });

  const [showForm, setShowForm] = useState(false);
  const [editShow, setEditShow] = useState<Show | null>(null);
  const [form, setForm] = useState({ title: "", slug: "", description: "", section: "Entertainment", status: "draft" });

  const createMut = useMutation({
    mutationFn: (data: any) => api.createShow(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["shows"] }); setShowForm(false); setForm({ title: "", slug: "", description: "", section: "Entertainment", status: "draft" }); },
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: any) => api.updateShow(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["shows"] }); setEditShow(null); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.deleteShow(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shows"] }),
  });

  function openEdit(show: Show) {
    setEditShow(show);
    setForm({ title: show.title, slug: show.slug, description: show.description, section: show.section || "", status: show.status });
  }

  const role = localStorage.getItem("role");

  if (error) return <div className="error-state">Error loading shows</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Shows</h1>
        {role && (
          <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditShow(null); setForm({ title: "", slug: "", description: "", section: "Entertainment", status: "draft" }); }}>
            + New Show
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <input placeholder="Search shows..." value={q} onChange={(e) => { setQ(e.target.value); setPage(0); }} />
        <select value={section} onChange={(e) => { setSection(e.target.value); setPage(0); }}>
          <option value="">All Sections</option>
          <option value="Entertainment">Entertainment</option>
          <option value="Documentaries">Documentaries</option>
          <option value="Nature">Nature</option>
          <option value="Food & Culture">Food & Culture</option>
        </select>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(0); }}>
          <option value="">All Status</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
      </div>

      {/* Create / Edit form */}
      {(showForm || editShow) && (
        <div className="card">
          <h3>{editShow ? "Edit Show" : "New Show"}</h3>
          <form onSubmit={(e) => {
            e.preventDefault();
            if (editShow) {
              updateMut.mutate({ id: editShow.id, data: form });
            } else {
              createMut.mutate(form);
            }
          }}>
            <div className="form-row">
              <div className="form-group">
                <label>Title</label>
                <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Slug</label>
                <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} required />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Section</label>
                <select value={form.section} onChange={(e) => setForm({ ...form, section: e.target.value })}>
                  <option value="">None</option>
                  <option value="Entertainment">Entertainment</option>
                  <option value="Documentaries">Documentaries</option>
                  <option value="Nature">Nature</option>
                  <option value="Food & Culture">Food & Culture</option>
                </select>
              </div>
              <div className="form-group">
                <label>Status</label>
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            {(createMut.isError || updateMut.isError) && (
              <div className="error-state" style={{ marginBottom: 12 }}>
                {((createMut.error || updateMut.error) as any)?.message || "Error saving show"}
              </div>
            )}
            <div style={{ display: "flex", gap: 8 }}>
              <button type="submit" className="btn btn-primary" disabled={createMut.isPending || updateMut.isPending}>
                {createMut.isPending || updateMut.isPending ? "Saving..." : "Save"}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => { setShowForm(false); setEditShow(null); }}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Shows table */}
      {isLoading ? (
        <div className="loading">Loading shows...</div>
      ) : !shows?.length ? (
        <div className="empty-state">No shows found.</div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Slug</th>
                  <th>Section</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {shows.map((s: Show) => (
                  <tr key={s.id}>
                    <td><Link to={`/shows/${s.id}`}>{s.title}</Link></td>
                    <td>{s.slug}</td>
                    <td>{s.section || "—"}</td>
                    <td><span className={`badge badge-${s.status}`}>{s.status}</span></td>
                    <td>
                      {role && (
                        <>
                          <button className="btn btn-secondary btn-sm" onClick={() => openEdit(s)} style={{ marginRight: 4 }}>Edit</button>
                          <button className="btn btn-danger btn-sm" onClick={() => { if (confirm("Delete this show?")) deleteMut.mutate(s.id); }}>Delete</button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button disabled={page === 0} onClick={() => setPage(page - 1)}>Prev</button>
            <span style={{ padding: "6px 12px" }}>Page {page + 1}</span>
            <button disabled={shows.length < limit} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
