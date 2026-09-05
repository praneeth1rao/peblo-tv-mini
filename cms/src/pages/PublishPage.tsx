import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { ValidationReport, PublishRun } from "../types";

export function PublishPage() {
  const qc = useQueryClient();
  const role = localStorage.getItem("role");

  const { data: report, isLoading: reportLoading } = useQuery({
    queryKey: ["validation-report"],
    queryFn: () => api.getValidationReport(),
    refetchInterval: 30000,
  });

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["publish-runs"],
    queryFn: () => api.listPublishRuns(),
  });

  const publishMut = useMutation({
    mutationFn: () => api.publish(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["publish-runs"] });
      qc.invalidateQueries({ queryKey: ["validation-report"] });
    },
  });

  const vr: ValidationReport | undefined = report;

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>Publish Catalogue</h1>

      {/* Validation Report */}
      <div className="card">
        <h3>Validation Report</h3>
        {reportLoading ? (
          <div className="loading">Loading validation report...</div>
        ) : vr ? (
          <>
            <div style={{ display: "flex", gap: 16, marginBottom: 16, alignItems: "center" }}>
              <span style={{ fontSize: 14 }}>
                {vr.blocking_count === 0 ? (
                  <span style={{ color: "#155724", fontWeight: 600 }}>✓ No blocking issues — ready to publish</span>
                ) : (
                  <span style={{ color: "#721c24", fontWeight: 600 }}>✗ {vr.blocking_count} blocking issue(s) found</span>
                )}
              </span>
            </div>
            {vr.issues.length > 0 && (
              <ul className="issue-list">
                {vr.issues.map((issue, idx) => (
                  <li key={idx}>
                    <span className="entity">{issue.entity_type}: {issue.entity_title}</span> — {issue.issue}
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : null}
      </div>

      {/* Publish button */}
      {role === "admin" ? (
        <div className="card" style={{ textAlign: "center" }}>
          <button
            className="btn btn-primary"
            style={{ fontSize: 16, padding: "12px 32px" }}
            disabled={publishMut.isPending || (vr?.blocking_count ?? 0) > 0}
            onClick={() => {
              if (confirm("Publish the catalogue now?")) publishMut.mutate();
            }}
          >
            {publishMut.isPending ? "Publishing..." : "Publish Now"}
          </button>
          {publishMut.isError && <div className="error-state" style={{ marginTop: 12 }}>{(publishMut.error as any)?.message}</div>}
          {publishMut.isSuccess && <div style={{ marginTop: 12, color: "#155724", fontWeight: 600 }}>Catalogue published successfully!</div>}
        </div>
      ) : (
        <div className="permission-denied">
          Only administrators can publish. Your role: <strong>{role || "none"}</strong>
        </div>
      )}

      {/* Publish run history */}
      <div className="card">
        <h3>Publish History</h3>
        {runsLoading ? (
          <div className="loading">Loading...</div>
        ) : !runs?.length ? (
          <div className="empty-state">No publish runs yet.</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Date</th><th>Status</th><th>Published By</th><th>Shows</th><th>Episodes</th><th>Error</th></tr>
              </thead>
              <tbody>
                {runs.map((r: PublishRun) => (
                  <tr key={r.id}>
                    <td>{r.published_at ? new Date(r.published_at).toLocaleString() : "—"}</td>
                    <td><span className={`badge badge-${r.status}`}>{r.status}</span></td>
                    <td>{r.published_by}</td>
                    <td>{r.show_count}</td>
                    <td>{r.episode_count}</td>
                    <td style={{ color: "#dc3545", fontSize: 12 }}>{r.error_message || "—"}</td>
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
