import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LoginPage } from "./pages/Login";
import { ShowsList } from "./pages/ShowsList";
import { ShowDetail } from "./pages/ShowDetail";
import { EpisodesList } from "./pages/EpisodesList";
import { EpisodeDetail } from "./pages/EpisodeDetail";
import { PublishPage } from "./pages/PublishPage";
import { Layout } from "./components/Layout";
import "./styles.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("token");
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<ShowsList />} />
            <Route path="shows" element={<ShowsList />} />
            <Route path="shows/:id" element={<ShowDetail />} />
            <Route path="episodes" element={<EpisodesList />} />
            <Route path="episodes/:id" element={<EpisodeDetail />} />
            <Route path="publish" element={<PublishPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
