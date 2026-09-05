import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";

export function ShowDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);

  const { data: catalogue, isLoading, error } = useQuery({
    queryKey: ["catalogue-detail"],
    queryFn: () => api.getCatalogue(),
  });

  if (isLoading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error-state">Failed to load catalogue.</div>;

  const show = catalogue?.shows?.find((s: any) => s.slug === slug);
  if (!show) return <div className="empty-state">Show not found.</div>;

  // Season numbers, excluding 0
  const seasonNumbers = Object.keys(show.seasons || {})
    .map(Number)
    .filter((n) => n > 0)
    .sort((a, b) => a - b);

  // Season 0 (trailers) — separate display
  const trailerEps = show.seasons?.[0] || [];

  const activeSeason = selectedSeason !== null ? selectedSeason : (seasonNumbers[0] || 1);
  const episodes = show.seasons?.[activeSeason] || [];

  // Collect languages from all episodes
  const allLanguages = new Set<string>();
  for (const seasonEps of Object.values(show.seasons || {})) {
    for (const ep of seasonEps as any[]) {
      for (const lang of ep.languages || []) allLanguages.add(lang);
    }
  }

  function formatDuration(seconds: number | null) {
    if (!seconds) return "—";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m ${s}s`;
  }

  return (
    <div>
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-brand" onClick={() => navigate("/")} style={{ cursor: "pointer" }}>
          PEBLO TV
        </div>
      </nav>

      <div className="detail-page">
        <a className="back-link" href="/" onClick={(e) => { e.preventDefault(); navigate("/"); }}>← Back to Home</a>

        {/* Hero */}
        <div className="detail-hero">
          {show.artwork?.poster ? (
            <img className="detail-poster" src={show.artwork.poster.url} alt={show.title} />
          ) : (
            <div className="detail-poster-placeholder">No Poster</div>
          )}
          <div className="detail-info">
            {show.section && <div className="section-label">{show.section}</div>}
            <h1>{show.title}</h1>
            {show.description && <p>{show.description}</p>}
            <div style={{ color: "#888", fontSize: 13, marginTop: 8 }}>
              {seasonNumbers.length} season{seasonNumbers.length !== 1 ? "s" : ""}
              {allLanguages.size > 0 && ` · ${allLanguages.size} language${allLanguages.size !== 1 ? "s" : ""}`}
            </div>
          </div>
        </div>

        {/* Season tabs */}
        {seasonNumbers.length > 1 && (
          <div className="season-tabs">
            {seasonNumbers.map((num) => (
              <button
                key={num}
                className={`season-tab ${activeSeason === num ? "active" : ""}`}
                onClick={() => setSelectedSeason(num)}
              >
                Season {num}
              </button>
            ))}
          </div>
        )}

        {/* Episodes */}
        {episodes.length > 0 ? (
          <ul className="episode-list">
            {episodes.map((ep: any) => (
              <li key={ep.id} className="episode-item">
                <div className="ep-number">{ep.number}</div>
                <div className="ep-info">
                  <div className="ep-title">
                    {ep.title}
                    {ep.duration > 0 && <span style={{ fontWeight: 400, color: "#888", fontSize: 13, marginLeft: 8 }}>{formatDuration(ep.duration)}</span>}
                  </div>
                  {ep.description && <div className="ep-desc">{ep.description}</div>}
                  <div className="ep-meta">
                    {ep.languages && ep.languages.length > 0 && (
                      <div>
                        {ep.languages.map((l: string) => (
                          <span key={l} className="lang-badge">{l}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty-state">No episodes in this season.</div>
        )}

        {/* Trailers (season 0) */}
        {trailerEps.length > 0 && (
          <>
            <h2 style={{ marginTop: 32, marginBottom: 16, fontSize: 20 }}>Trailers</h2>
            <ul className="episode-list">
              {trailerEps.map((ep: any) => (
                <li key={ep.id} className="episode-item">
                  <div className="ep-number">{ep.number}</div>
                  <div className="ep-info">
                    <div className="ep-title">{ep.title}</div>
                    {ep.description && <div className="ep-desc">{ep.description}</div>}
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
