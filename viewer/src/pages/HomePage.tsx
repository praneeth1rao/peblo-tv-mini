import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export function HomePage() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [section, setSection] = useState("");
  const [language, setLanguage] = useState("");

  const params: Record<string, string> = {};
  if (q) params.q = q;
  if (section) params.section = section;
  if (language) params.language = language;

  const { data, isLoading, error } = useQuery({
    queryKey: ["catalog", params],
    queryFn: () => api.searchCatalogue(params),
  });

  const { data: fullCatalogue } = useQuery({
    queryKey: ["catalogue-full"],
    queryFn: () => api.getCatalogue(),
    enabled: !q && !section && !language,
  });

  // Use search results when filtering, otherwise use full catalogue
  const isFiltering = q || section || language;
  const shows = isFiltering ? (data?.results || []) : (fullCatalogue?.shows || []);

  // Group by section for the rows view
  const sections: Record<string, any[]> = {};
  for (const show of shows) {
    const sec = show.section || "Uncategorized";
    if (!sections[sec]) sections[sec] = [];
    sections[sec].push(show);
  }
  const sectionNames = Object.keys(sections).sort();

  // Featured show = first show with banner or first show overall
  const featured = shows[0];

  // Collect all unique languages for filter
  const allLanguages = new Set<string>();
  for (const show of shows) {
    for (const seasonEps of Object.values(show.seasons || {})) {
      for (const ep of seasonEps as any[]) {
        for (const lang of ep.languages || []) allLanguages.add(lang);
      }
    }
  }

  if (error) return <div className="error-state">Failed to load catalogue. Is it published?</div>;
  if (isLoading) return <div className="loading">Loading catalogue...</div>;

  return (
    <div>
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-brand" onClick={() => { setQ(""); setSection(""); setLanguage(""); navigate("/"); }} style={{ cursor: "pointer" }}>
          PEBLO TV
        </div>
        <div className="navbar-search">
          <input
            placeholder="Search shows, episodes..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select value={section} onChange={(e) => setSection(e.target.value)}>
            <option value="">All Sections</option>
            {sectionNames.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          {allLanguages.size > 0 && (
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="">All Languages</option>
              {Array.from(allLanguages).sort().map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          )}
        </div>
      </nav>

      {/* Empty state */}
      {shows.length === 0 ? (
        <div className="empty-state">
          {isFiltering ? "No results found for your search." : "No shows in the catalogue yet. Publish via the CMS first."}
        </div>
      ) : (
        <>
          {/* Hero banner */}
          {featured && !isFiltering && (
            <div className="hero">
              <div
                className="hero-bg"
                style={{
                  backgroundImage: featured.artwork?.banner
                    ? `url(${featured.artwork.banner.url})`
                    : featured.artwork?.poster
                    ? `url(${featured.artwork.poster.url})`
                    : undefined,
                }}
              />
              <div className="hero-content">
                {featured.section && <div className="section-badge">{featured.section}</div>}
                <h1>{featured.title}</h1>
                <p>{featured.description}</p>
                <a className="hero-btn" href={`/show/${featured.slug}`} onClick={(e) => { e.preventDefault(); navigate(`/show/${featured.slug}`); }}>
                  View Details →
                </a>
              </div>
            </div>
          )}

          {/* Section rows */}
          {sectionNames.map((sec) => (
            <div className="section-row" key={sec}>
              <h2>{sec}</h2>
              <div className="row-scroll">
                {sections[sec].map((show: any) => (
                  <div
                    key={show.id}
                    className="card-show"
                    onClick={() => navigate(`/show/${show.slug}`)}
                  >
                    {show.artwork?.poster ? (
                      <img src={show.artwork.poster.url} alt={show.title} loading="lazy" />
                    ) : (
                      <div className="poster-placeholder">{show.title.substring(0, 15)}</div>
                    )}
                    <div className="card-title">{show.title}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
