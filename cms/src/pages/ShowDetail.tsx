import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { Show, Season } from "../types";

const ARTWORK_SPECS = [
  { type: "poster", label: "Poster", dims: "600 × 900 (2:3)" },
  { type: "banner", label: "Banner", dims: "1280 × 720 (16:9)" },
  { type: "thumbnail", label: "Thumbnail", dims: "640 × 360 (16:9)" },
];

export function ShowDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const role = localStorage.getItem("role");

  const { data: show, isLoading } = useQuery({
    queryKey: ["show", id],
    queryFn: () => api.getShow(id!),
    enabled: !!id,
  });

  const { data: seasons } = useQuery({
    queryKey: ["seasons", id],
    queryFn: () => api.listSeasons(id!),
    enabled: !!id,
  });

  const { data: artwork } = useQuery({
    queryKey: ["artwork", "show", id],
    queryFn: () => api.listArtwork({ show_id: id! }),
    enabled: !!id,
  });

  const [newSeason, setNewSeason] = useState(false);
  const [seasonNum, setSeasonNum] = useState(1);

  const createSeasonMut = useMutation({
    mutationFn: (data: any) => api.createSeason(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["seasons", id] }); setNewSeason(false); },
  });

  const uploadMut = useMutation({
    mutationFn: (fd: FormData) => api.uploadArtwork(fd),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["artwork", "show", id] }),
  });

  function handleUpload(type: string, file: File) {
    const fd = new FormData();
    fd.append("artwork_type", type);
    fd.append("show_id", id!);
    fd.append("file", file);
    uploadMut.mutate(fd);
  }

  if (isLoading) return <div className="loading">Loading show...</div>;
  if (!show) return <div className="error-state">Show not found</div>;

  const artworkByType = (artwork || []).reduce((acc: Record<string, any>, a: any) => {
    acc[a.artwork_type] = a;
    return acc;
  }, {});

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/shows" style={{ fontSize: 13 }}>← Back to Shows</Link>
          <h1 style={{ marginTop: 4 }}>{show.title}</h1>
        </div>
        <span className={`badge badge-${show.status}`}>{show.status}</span>
      </div>

      {/* Show info */}
      <div className="card">
        <div className="form-row">
          <div><strong>Slug:</strong> {show.slug}</div>
          <div><strong>Section:</strong> {show.section || "None"}</div>
        </div>
        {show.description && <p style={{ marginTop: 8, color: "#555" }}>{show.description}</p>}
      </div>

      {/* Artwork slots */}
      {role && (
        <div className="card">
          <h3>Artwork</h3>
          <div className="artwork-slots">
            {ARTWORK_SPECS.map((spec) => {
              const existing = artworkByType[spec.type];
              return (
                <div key={spec.type} className={`artwork-slot ${existing ? "has-art" : ""}`}>
                  <div className="type-label">{spec.label}</div>
                  {existing ? (
                    <>
                      <img src={existing.url} alt={spec.label} />
                      <div className="dims">{existing.width} × {existing.height}</div>
                    </>
                  ) : (
                    <>
                      <div className="dims" style={{ marginBottom: 8 }}>{spec.dims}</div>
                      <label className="btn btn-secondary btn-sm" style={{ cursor: "pointer" }}>
                        Upload
                        <input type="file" accept="image/*" hidden onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) handleUpload(spec.type, f);
                        }} />
                      </label>
                    </>
                  )}
                </div>
              );
            })}
          </div>
          {uploadMut.isError && <div className="error-state" style={{ marginTop: 12 }}>{(uploadMut.error as any)?.message}</div>}
        </div>
      )}

      {/* Seasons */}
      <div className="card">
        <div className="card-header">
          <h3>Seasons</h3>
          {role && <button className="btn btn-primary btn-sm" onClick={() => setNewSeason(true)}>+ New Season</button>}
        </div>
        {newSeason && (
          <form onSubmit={(e) => {
            e.preventDefault();
            createSeasonMut.mutate({ show_id: id, number: seasonNum, title: `Season ${seasonNum}` });
          }} style={{ marginBottom: 12, display: "flex", gap: 8, alignItems: "end" }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Season #</label>
              <input type="number" value={seasonNum} onChange={(e) => setSeasonNum(Number(e.target.value))} min={0} style={{ width: 80 }} />
            </div>
            <button type="submit" className="btn btn-primary btn-sm">Create</button>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setNewSeason(false)}>Cancel</button>
          </form>
        )}
        {!seasons?.length ? (
          <div className="empty-state">No seasons yet.</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>#</th><th>Title</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {seasons.map((s: Season) => (
                  <tr key={s.id}>
                    <td>{s.number === 0 ? "0 (Trailers)" : s.number}</td>
                    <td>{s.title}</td>
                    <td><span className={`badge badge-${s.status}`}>{s.status}</span></td>
                    <td>
                      <Link to={`/episodes?season_id=${s.id}&show_id=${id}`} className="btn btn-secondary btn-sm" style={{ marginRight: 4 }}>Episodes</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
