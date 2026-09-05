import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";

const ARTWORK_SPECS = [
  { type: "poster", label: "Poster", dims: "600 × 900 (2:3)" },
  { type: "banner", label: "Banner", dims: "1280 × 720 (16:9)" },
  { type: "thumbnail", label: "Thumbnail", dims: "640 × 360 (16:9)" },
];

export function EpisodeDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const role = localStorage.getItem("role");

  const { data: episode, isLoading } = useQuery({
    queryKey: ["episode", id],
    queryFn: () => api.getEpisode(id!),
    enabled: !!id,
  });

  const { data: artwork } = useQuery({
    queryKey: ["artwork", "episode", id],
    queryFn: () => api.listArtwork({ episode_id: id! }),
    enabled: !!id,
  });

  const uploadMut = useMutation({
    mutationFn: (fd: FormData) => api.uploadArtwork(fd),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["artwork", "episode", id] }),
  });

  function handleUpload(type: string, file: File) {
    const fd = new FormData();
    fd.append("artwork_type", type);
    fd.append("episode_id", id!);
    fd.append("file", file);
    uploadMut.mutate(fd);
  }

  if (isLoading) return <div className="loading">Loading episode...</div>;
  if (!episode) return <div className="error-state">Episode not found</div>;

  const artworkByType = (artwork || []).reduce((acc: Record<string, any>, a: any) => {
    acc[a.artwork_type] = a;
    return acc;
  }, {});

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/episodes" style={{ fontSize: 13 }}>← Back to Episodes</Link>
          <h1 style={{ marginTop: 4 }}>{episode.title}</h1>
        </div>
        <span className={`badge badge-${episode.status}`}>{episode.status}</span>
      </div>

      <div className="card">
        <div className="form-row">
          <div><strong>Language:</strong> {episode.language}</div>
          <div><strong>Content Group:</strong> {episode.content_group}</div>
          <div><strong>Duration:</strong> {episode.duration ? `${Math.floor(episode.duration / 60)}m ${episode.duration % 60}s` : "Not set"}</div>
          <div><strong>Number:</strong> S{episode.season_id ? "—" : "?"}E{episode.number}</div>
        </div>
        {episode.description && <p style={{ marginTop: 8, color: "#555" }}>{episode.description}</p>}
      </div>

      {/* Artwork slots */}
      {role && (
        <div className="card">
          <h3>Artwork</h3>
          {uploadMut.isError && <div className="error-state" style={{ marginBottom: 12 }}>{(uploadMut.error as any)?.message}</div>}
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
        </div>
      )}
    </div>
  );
}
