// Core domain types
export interface LearningPath {
  id: string;
  title: string;
  description: string;
  slug: string;
  moduleCount: number;
}

export interface Module {
  id: string;
  title: string;
  learningPath?: string;
  order: number;
  pages: Page[];
}

export interface Page {
  id: string;
  title: string;
  slug: string;
  order: number;
  completed: boolean;
  content?: string; // MDX content placeholder
}

// Dashboard types
export interface UserStats {
  currentStreak: number;
  longestStreak: number;
  overallCompletion: number;
  badgesEarned: number;
}

export interface Badge {
  id: string;
  title: string;
  description: string;
  icon: string;
  earned: boolean;
  earnedDate?: string;
}

export interface RecentActivity {
  id: string;
  type: 'completed' | 'started';
  title: string;
  timestamp: string;
}

// UI component types
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';
export type CardPadding = 'sm' | 'md' | 'lg';
export type BadgeVariant = 'default' | 'success' | 'warning';
export type BadgeSize = 'sm' | 'md';
export type ProgressBarHeight = 'sm' | 'md' | 'lg';

// API types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface AuthResponse {
  user_id: string;
  authenticated: boolean;
  avatar_url?: string;
  username?: string;
  github_username?: string;
  is_admin?: boolean;
}

export interface ProgressResponse {
  message: string;
}

export interface ApiError {
  error: string;
}

// Walkthrough types
export interface Walkthrough {
  id: string;
  title: string;
  description: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  topics: string[];
  estimatedTime: number;  // minutes
  prerequisites: string[];
  repository: string;
  repositoryUrl?: string;  // Optional full GitHub URL
  authors?: Array<{ name: string; url?: string }>;  // Optional authors with links
}

export interface WalkthroughProgress {
  status: 'not_started' | 'in_progress' | 'completed';
  startedAt?: string;
  completedAt?: string;
}

export interface WalkthroughWithProgress extends Walkthrough {
  progress: WalkthroughProgress;
}

export interface WalkthroughDetail extends Walkthrough {
  readme: string;  // Markdown content
  progress: WalkthroughProgress;
}

export interface WalkthroughFilters {
  difficulty?: 'Beginner' | 'Intermediate' | 'Advanced';
  topics?: string[];
  search?: string;
  status?: 'in_progress' | 'completed';
}

// Content Registry types
export interface ContentRegistry {
  schema_version: string;
  generated_at: string;
  generator_version: string;
  entries: Record<string, ContentEntry>;
}

export interface QuizQuestion {
  id: string;
  question_text: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

export interface QuizEntry {
  content_type: "quiz";
  topic_slug: string;
  module_id: string;
  passing_score: number;
  question_count: number;
  questions: QuizQuestion[];
}

export interface ModuleEntry {
  content_type: "module";
  topic_slug: string;
  module_id: string;
  module_number: number;
  title: string;
  reading_time: number;
  has_quiz: boolean;
}

export interface CapstoneEntry {
  content_type: "capstone";
  topic_slug: string;
  module_id: string;
  title: string;
  description: string;
  submission_requirements: string[];
  evaluation_criteria: string[];
}

export interface WalkthroughEntry {
  content_type: "walkthrough";
  id: string;
  title: string;
  description: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  topics: string[];
  estimated_time: number;
  prerequisites: string[];
  repository: string;
}

export type ContentEntry = QuizEntry | ModuleEntry | CapstoneEntry | WalkthroughEntry;

// Curriculum page types
export interface CurriculumStage {
  id: string;
  name: string;
  description: string;
  stageNumber?: number;
  moduleCount?: number;
  modules?: CurriculumModule[];
  projects?: string[];
}

export interface CurriculumModule {
  id: string;
  name: string;
  description?: string;
  topics: string[];
  submodules?: CurriculumSubmodule[];
}

export interface CurriculumSubmodule {
  id: string;
  title: string;
  moduleNumber: number;
  readingTime: number;
}
