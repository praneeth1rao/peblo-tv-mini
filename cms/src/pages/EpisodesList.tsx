import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import type { Episode } from "../types";

export function EpisodesList() {
  const [searchParams] = useSearchParams();
  const qc = useQueryClient();
  const role = localStorage.getItem("role");

  const [showId, setShowId] = useState(searchParams.get("show_id") || "");
  const [seasonId, setSeasonId] = useState(searchParams.get("season_id") || "");
  const [epStatus, setEpStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const params: Record<string, string> = { offset: String(page * limit), limit: String(limit) };
  if (showId) params.show_id = showId;
  if (seasonId) params.season_id = seasonId;
  if (epStatus) params.status = epStatus;
  if (language) params.language = language;

  const { data: episodes, isLoading } = useQuery({
    queryKey: ["episodes", params],
    queryFn: () => api.listEpisodes(params),
  });

  const { data: shows } = useQuery({
    queryKey: ["shows-list"],
    queryFn: () => api.listShows(),
  });

  const [showForm, setShowForm] = useState(false);
  const [editEp, setEditEp] = useState<Episode | null>(null);
  const [form, setForm] = useState({
    show_id: showId || "", season_id: seasonId || "", number: 1, title: "",
    description: "", duration: "", content_group: "", language: "en", status: "draft",
  });

  const createMut = useMutation({
    mutationFn: (data: any) => api.createEpisode({ ...data, duration: data.duration ? Number(data.duration) : null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["episodes"] }); setShowForm(false); },
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: any) => api.updateEpisode(id, { ...data, duration: data.duration ? Number(data.duration) : null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["episodes"] }); setEditEp(null); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.deleteEpisode(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["episodes"] }),
  });

  function openEdit(ep: Episode) {
    setEditEp(ep);
    setForm({
      show_id: ep.show_id, season_id: ep.season_id, number: ep.number, title: ep.title,
      description: ep.description, duration: ep.duration ? String(ep.duration) : "",
      content_group: ep.content_group, language: ep.language, status: ep.status,
    });
  }

  return (
    <div>
      <div className="page-header">
        <h1>Episodes</h1>
        {role && (
          <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditEp(null); setForm({ show_id: showId || "", season_id: seasonId || "", number: 1, title: "", description: "", duration: "", content_group: "", language: "en", status: "draft" }); }}>
            + New Episode
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <select value={showId} onChange={(e) => { setShowId(e.target.value); setPage(0); }}>
          <option value="">All Shows</option>
          {shows?.map((s: any) => <option key={s.id} value={s.id}>{s.title}</option>)}
        </select>
        <select value={epStatus} onChange={(e) => { setEpStatus(e.target.value); setPage(0); }}>
          <option value="">All Status</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
        <select value={language} onChange={(e) => { setLanguage(e.target.value); setPage(0); }}>
          <option value="">All Languages</option>
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
        </select>
      </div>

      {/* Create/Edit form */}
      {(showForm || editEp) && (
        <div className="card">
          <h3>{editEp ? "Edit Episode" : "New Episode"}</h3>
          <form onSubmit={(e) => {
            e.preventDefault();
            if (editEp) {
              updateMut.mutate({ id: editEp.id, data: form });
            } else {
              createMut.mutate(form);
            }
          }}>
            <div className="form-row">
              <div className="form-group">
                <label>Show</label>
                <select value={form.show_id} onChange={(e) => setForm({ ...form, show_id: e.target.value })} required>
                  <option value="">Select show...</option>
                  {shows?.map((s: any) => <option key={s.id} value={s.id}>{s.title}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Season ID</label>
                <input value={form.season_id} onChange={(e) => setForm({ ...form, season_id: e.target.value })} placeholder="UUID" required />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Number</label>
                <input type="number" value={form.number} onChange={(e) => setForm({ ...form, number: Number(e.target.value) })} required />
              </div>
              <div className="form-group">
                <label>Title</label>
                <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Content Group</label>
                <input value={form.content_group} onChange={(e) => setForm({ ...form, content_group: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Language</label>
                <select value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}>
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                </select>
              </div>
              <div className="form-group">
                <label>Duration (seconds)</label>
                <input type="number" value={form.duration} onChange={(e) => setForm({ ...form, duration: e.target.value })} />
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
                {((createMut.error || updateMut.error) as any)?.message}
              </div>
            )}
            <div style={{ display: "flex", gap: 8 }}>
              <button type="submit" className="btn btn-primary" disabled={createMut.isPending || updateMut.isPending}>
                {createMut.isPending || updateMut.isPending ? "Saving..." : "Save"}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => { setShowForm(false); setEditEp(null); }}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Episodes table */}
      {isLoading ? (
        <div className="loading">Loading episodes...</div>
      ) : !episodes?.length ? (
        <div className="empty-state">No episodes found.</div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>#</th><th>Title</th><th>Language</th><th>Content Group</th><th>Duration</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {episodes.map((ep: Episode) => (
                  <tr key={ep.id}>
                    <td>{ep.number}</td>
                    <td><Link to={`/episodes/${ep.id}`}>{ep.title}</Link></td>
                    <td>{ep.language}</td>
                    <td style={{ fontSize: 12 }}>{ep.content_group}</td>
                    <td>{ep.duration ? `${Math.floor(ep.duration / 60)}m ${ep.duration % 60}s` : "—"}</td>
                    <td><span className={`badge badge-${ep.status}`}>{ep.status}</span></td>
                    <td>
                      {role && (
                        <>
                          <button className="btn btn-secondary btn-sm" onClick={() => openEdit(ep)} style={{ marginRight: 4 }}>Edit</button>
                          <button className="btn btn-danger btn-sm" onClick={() => { if (confirm("Delete?")) deleteMut.mutate(ep.id); }}>Del</button>
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
            <button disabled={episodes.length < limit} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
