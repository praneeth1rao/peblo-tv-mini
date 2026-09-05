export interface Show {
  id: string;
  title: string;
  description: string;
  slug: string;
  section: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Season {
  id: string;
  show_id: string;
  number: number;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Episode {
  id: string;
  season_id: string;
  show_id: string;
  number: number;
  title: string;
  description: string;
  duration: number | null;
  content_group: string;
  language: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Artwork {
  id: string;
  artwork_type: string;
  url: string;
  width: number;
  height: number;
  show_id: string | null;
  episode_id: string | null;
  created_at: string;
}

export interface ValidationIssue {
  entity_type: string;
  entity_id: string;
  entity_title: string;
  issue: string;
}

export interface ValidationReport {
  issues: ValidationIssue[];
  blocking_count: number;
  publishable: boolean;
}

export interface PublishRun {
  id: string;
  status: string;
  published_by: string;
  published_at: string | null;
  show_count: number;
  season_count: number;
  episode_count: number;
  error_message: string | null;
}
