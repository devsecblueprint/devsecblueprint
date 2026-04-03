/**
 * API Client for backend Lambda function via API Gateway
 * 
 * Handles all HTTP communication with the backend, including:
 * - GitHub OAuth authentication
 * - User session verification
 * - Progress tracking
 * - Walkthrough browsing and progress
 * 
 * All requests automatically include credentials (cookies) for JWT authentication.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

if (!API_BASE_URL && typeof window !== 'undefined') {
  console.warn('NEXT_PUBLIC_API_URL is not set. API calls will fail.');
}

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  statusCode?: number;
}

/**
 * Authentication response from /me endpoint
 */
export interface AuthResponse {
  user_id: string;
  authenticated: boolean;
  avatar_url?: string;
  username?: string;
  github_username?: string;
  gitlab_username?: string;
  bitbucket_username?: string;
  provider?: string;
  is_admin?: boolean;
}

/**
 * Progress save response from /progress endpoint
 */
export interface ProgressResponse {
  message: string;
}

/**
 * Capstone submission response from /progress/capstone/{contentId} endpoint
 */
export interface CapstoneSubmissionResponse {
  repo_url?: string;
  github_username?: string;
  gitlab_username?: string;
  repo_name?: string;
  submitted_at?: string;
  updated_at?: string;
  submission?: null;
}

/**
 * Progress item from backend
 */
export interface ProgressItem {
  content_id: string;
  status: string;
  completed_at: string;
}

/**
 * User statistics from /progress/stats endpoint
 */
export interface UserStatsResponse {
  current_streak: number;
  longest_streak: number;
  overall_completion: number;
  completed_count: number;
  quizzes_passed: number;
  walkthroughs_completed: number;
}

/**
 * User profile from /user/profile endpoint
 */
export interface UserProfileResponse {
  user_id: string;
  username: string;
  avatar_url: string;
  registered_at: string;
  last_login: string;
  is_new_user: boolean;
  total_completions: number;
}

/**
 * Recent activities response from /progress/recent endpoint
 */
export interface RecentActivitiesResponse {
  recent: ProgressItem[];
}

/**

/**
 * Badge object from backend
 */
export interface BadgeData {
  id: string;
  title: string;
  description: string;
  icon: string;
  earned: boolean;
  earned_date?: string;
}

/**
 * Badges response from /progress/badges endpoint
 */
export interface BadgesResponse {
  badges: BadgeData[];
}

/**
 * User list item from /admin/users endpoint
 */
export interface UserListItem {
  user_id: string;
  username: string;
  github_username: string;
  gitlab_username: string;
  bitbucket_username?: string;
  provider: string;
  avatar_url: string;
  registered_at: string;
  last_login: string;
}

/**
 * Paginated user list response from /admin/users endpoint
 */
export interface UserListResponse {
  users: UserListItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Admin user profile response from /admin/users/{user_id}/profile endpoint
 */
export interface AdminUserProfileResponse {
  user: UserListItem;
  stats: {
    completed_count: number;
    overall_completion: number;
    quizzes_passed: number;
    walkthroughs_completed: number;
    capstone_submissions: number;
    current_streak: number;
    longest_streak: number;
  };
  badges: Array<{
    id: string;
    title: string;
    icon: string;
    earned: boolean;
    earned_date?: string;
  }>;
  walkthrough_progress: Array<{
    walkthrough_id: string;
    status: string;
    started_at: string;
    completed_at?: string | null;
  }>;
}

/**
 * Capstone submission from /admin/submissions endpoint
 */
export interface CapstoneSubmission {
  user_id: string;
  content_id: string;
  github_username: string;
  gitlab_username?: string;
  bitbucket_username?: string;
  provider?: string;
  repo_url: string;
  submitted_at: string;
  updated_at: string;
}

/**
 * Capstone submissions response from /admin/submissions endpoint
 */
export interface CapstoneSubmissionsResponse {
  submissions: CapstoneSubmission[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Registry status response from /admin/registry-status endpoint
 */
export interface RegistryStatusResponse {
  schema_version: string | null;
  last_updated: string | null;
  total_entries: number;
  cache_status: 'loaded' | 'not_loaded' | 'error';
  cache_ttl_seconds: number | null;
  cache_expires_in_seconds: number | null;
  s3_bucket: string;
  s3_key: string;
  status: 'healthy' | 'unavailable';
  error?: string;
}

/**
 * Validation error from /admin/module-health endpoint
 */
export interface ValidationError {
  module_id: string;
  error_type: string;
  error_message: string;
}

/**
 * Module health response from /admin/module-health endpoint
 */
export interface ModuleHealthResponse {
  total_modules: number;
  validation_pass_percentage: number;
  content_by_type: {
    quiz: number;
    module: number;
    capstone: number;
    walkthrough: number;
  };
  validation_errors: ValidationError[];
  status: 'healthy' | 'warning' | 'error';
}

/**
 * Active session record from /admin/sessions endpoint
 */
export interface ActiveSession {
  user_id: string;
  username: string;
  created_at: number;
  expires_at: number;
}

/**
 * Active sessions response from /admin/sessions endpoint
 */
export interface ActiveSessionsResponse {
  sessions: ActiveSession[];
  total_active: number;
}

/**
 * Walkthrough statistics response from /admin/walkthrough-statistics endpoint
 */
export interface WalkthroughStatisticsResponse {
  completed_count: number;
  in_progress_count: number;
  most_popular_walkthrough: string | null;
}

/**
 * API Client class for making HTTP requests to the backend
 */
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic request method with error handling
   * 
   * @param endpoint - API endpoint (e.g., '/me')
   * @param options - Fetch options
   * @returns Promise with data or error
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    if (!this.baseUrl) {
      console.error('API_BASE_URL not configured');
      return { error: 'API URL not configured' };
    }

    try {
      const url = `${this.baseUrl}${endpoint}`;

      // Read session token from cookie and send as Authorization header
      // so the backend receives it even when the API is on a different domain.
      const authHeaders: Record<string, string> = {};
      if (typeof document !== 'undefined') {
        const match = document.cookie.match(/(?:^|;\s*)dsb_session=([^;]*)/);
        if (match) {
          authHeaders['Authorization'] = `Bearer ${match[1]}`;
        }
      }
      
      const response = await fetch(url, {
        ...options,
        credentials: 'include', // Include cookies for JWT authentication
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
          ...options.headers,
        },
      });

      // Handle non-OK responses
      if (!response.ok) {
        // Try to parse error message from response
        const errorData = await response.json().catch(() => ({ error: 'Request failed' }));
        return { 
          error: errorData.error || `HTTP ${response.status}: ${response.statusText}`,
          statusCode: response.status
        };
      }

      // Parse successful response
      const data = await response.json();
      return { data, statusCode: response.status };
    } catch (error) {
      // Network errors or other exceptions
      console.error('API request failed:', error);
      return { 
        error: error instanceof Error ? error.message : 'Network error' 
      };
    }
  }

  /**
   * GET request
   * 
   * @param endpoint - API endpoint
   * @returns Promise with data or error
   */
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  /**
   * PUT request
   * 
   * @param endpoint - API endpoint
   * @param body - Request body
   * @returns Promise with data or error
   */
  async put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  /**
   * POST request
   * 
   * @param endpoint - API endpoint
   * @param body - Request body
   * @returns Promise with data or error
   */
  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // ============================================================================
  // Authentication Methods
  // ============================================================================

  /**
   * Get the GitHub OAuth start URL
   * 
   * @returns Full URL to initiate GitHub OAuth flow
   */
  getAuthStartUrl(): string {
    return `${this.baseUrl}/auth/github/start`;
  }

  /**
   * Get the GitLab OAuth start URL
   * 
   * @returns Full URL to initiate GitLab OAuth flow
   */
  getGitLabAuthStartUrl(): string {
    return `${this.baseUrl}/auth/gitlab/start`;
  }

  getBitbucketAuthStartUrl(): string {
    return `${this.baseUrl}/auth/bitbucket/start`;
  }

  /**
   * Check authentication status
   * 
   * Calls GET /me endpoint to verify JWT cookie and get user info
   * 
   * @returns Promise with user_id and authenticated status
   */
  async checkAuth(): Promise<ApiResponse<AuthResponse>> {
    return this.get<AuthResponse>('/me');
  }

  /**
   * Logout user and clear JWT cookie
   * 
   * Calls POST /logout endpoint to delete the JWT cookie
   * 
   * @returns Promise with success message
   */
  async logout(): Promise<ApiResponse<{ message: string }>> {
    return this.post<{ message: string }>('/logout', {});
  }

  // ============================================================================
  // Progress Tracking Methods
  // ============================================================================

  /**
   * Save user progress for a content page
   * 
   * Calls PUT /progress endpoint with content_id and optional repo_url
   * 
   * @param contentId - Unique identifier for the content page
   * @param repoUrl - Optional GitHub repository URL (for capstone submissions)
   * @returns Promise with success message
   */
  async saveProgress(contentId: string, repoUrl?: string): Promise<ApiResponse<ProgressResponse>> {
    const body: { content_id: string; repo_url?: string } = { content_id: contentId };
    if (repoUrl) {
      body.repo_url = repoUrl;
    }
    return this.put<ProgressResponse>('/progress', body);
  }

  /**
   * Get capstone submission
   * 
   * Calls GET /progress/capstone/{contentId} endpoint to retrieve capstone submission data
   * 
   * @param contentId - Unique identifier for the capstone content
   * @returns Promise with capstone submission data or null if not submitted
   */
  async getCapstoneSubmission(contentId: string): Promise<ApiResponse<CapstoneSubmissionResponse>> {
    return this.get<CapstoneSubmissionResponse>(`/progress/capstone/${contentId}`);
  }

  /**
   * Get all user progress
   * 
   * Calls GET /progress endpoint to retrieve all completed content
   * 
   * @returns Promise with list of completed content
   */
  async getProgress(): Promise<ApiResponse<{ progress: ProgressItem[] }>> {
    return this.get<{ progress: ProgressItem[] }>('/progress');
  }

  /**
   * Get user statistics
   * 
   * Calls GET /progress/stats endpoint to retrieve aggregated statistics
   * 
   * @returns Promise with user statistics (streaks, completion percentage)
   */
  async getStats(): Promise<ApiResponse<UserStatsResponse>> {
    return this.get<UserStatsResponse>('/progress/stats');
  }

  /**
   * Get recent activities
   * 
   * Calls GET /progress/recent endpoint to retrieve recently completed content
   * 
   * @returns Promise with recent activities
   */
  async getRecentActivities(): Promise<ApiResponse<RecentActivitiesResponse>> {
    return this.get<RecentActivitiesResponse>('/progress/recent');
  }

  /**
   * Get user badges
   * 
   * Calls GET /progress/badges endpoint to retrieve badges with earned status
   * 
   * @returns Promise with badges list
   */
  async getBadges(): Promise<ApiResponse<BadgesResponse>> {
    return this.get<BadgesResponse>('/progress/badges');
  }

  /**
   * Save the learner's last active lesson
   * 
   * Calls PUT /progress/last-active endpoint to record the current lesson
   * as the learner's resume point.
   * 
   * @param pageId - Unique identifier for the lesson page
   * @param pageSlug - URL slug for the lesson page
   * @returns Promise with success message
   */
  async saveLastActiveLesson(pageId: string, pageSlug: string): Promise<ApiResponse<{ message: string }>> {
    return this.put<{ message: string }>('/progress/last-active', { page_id: pageId, page_slug: pageSlug });
  }

  /**
   * Get the learner's last active lesson
   * 
   * Calls GET /progress/last-active endpoint to retrieve the lesson
   * the learner should resume from.
   * 
   * @returns Promise with page_id and page_slug (both null if no last active lesson)
   */
  async getLastActiveLesson(): Promise<ApiResponse<{ page_id: string | null; page_slug: string | null }>> {
    return this.get<{ page_id: string | null; page_slug: string | null }>('/progress/last-active');
  }

  /**
   * Reset all progress (admin only)
   * 
   * Calls DELETE /progress/reset endpoint to delete all user progress
   * 
   * @returns Promise with success message
   */
  async resetProgress(): Promise<ApiResponse<{ message: string; user_id: string }>> {
    return this.request<{ message: string; user_id: string }>('/progress/reset', {
      method: 'DELETE',
    });
  }

  /**
   * Get system analytics (admin only)
   * 
   * Calls GET /admin/analytics endpoint to retrieve system-wide statistics
   * 
   * @returns Promise with analytics data
   */
  async getAnalytics(): Promise<ApiResponse<{
    total_registered_users: number;
    active_sessions: number;
    users_with_progress: number;
    users_completed_all: number;
    total_completions: number;
    average_completion_rate: number;
    engagement_rate: number;
    registration_timeline: Array<{
      date: string;
      count: number;
    }>;
    completion_by_user: Array<{
      user_id: string;
      username: string;
      completed: number;
      percentage: number;
    }>;
  }>> {
    return this.get('/admin/analytics');
  }

  /**
   * Get capstone submissions (admin only)
   * 
   * Calls GET /admin/submissions endpoint to retrieve all capstone submissions
   * 
   * @param page - Page number (default: 1)
   * @param pageSize - Items per page (default: 50, max: 100)
   * @returns Promise with capstone submissions data
   */
  async getCapstoneSubmissions(page: number = 1, pageSize: number = 50): Promise<ApiResponse<CapstoneSubmissionsResponse>> {
    return this.get<CapstoneSubmissionsResponse>(`/admin/submissions?page=${page}&page_size=${pageSize}`);
  }

  /**
   * Get content registry status (admin only)
   * 
   * Calls GET /admin/registry-status endpoint to retrieve registry health information
   * 
   * @returns Promise with registry status data
   */
  async getRegistryStatus(): Promise<ApiResponse<RegistryStatusResponse>> {
    return this.get<RegistryStatusResponse>('/admin/registry-status');
  }

  /**
   * Get module health metrics (admin only)
   * 
   * Calls GET /admin/module-health endpoint to retrieve module validation metrics
   * 
   * @returns Promise with module health data
   */
  async getModuleHealth(): Promise<ApiResponse<ModuleHealthResponse>> {
    return this.get<ModuleHealthResponse>('/admin/module-health');
  }

  /**
   * Get walkthrough statistics (admin only)
   * 
   * Calls GET /admin/walkthrough-statistics endpoint to retrieve walkthrough engagement metrics
   * 
   * @returns Promise with walkthrough statistics data
   */
  async getWalkthroughStatistics(): Promise<ApiResponse<WalkthroughStatisticsResponse>> {
    return this.get<WalkthroughStatisticsResponse>('/admin/walkthrough-statistics');
  }

  /**
   * Get active sessions (admin only)
   *
   * Calls GET /admin/sessions endpoint to retrieve all active session records
   *
   * @returns Promise with active sessions data
   */
  async getActiveSessions(): Promise<ApiResponse<ActiveSessionsResponse>> {
    return this.get<ActiveSessionsResponse>('/admin/sessions');
  }

  /**
   * Search users (admin only)
   * 
   * Calls GET /admin/users/search endpoint to search for users by username
   * 
   * @param query - Search query string
   * @returns Promise with matching users and their stats
   */
  async searchUsers(query: string): Promise<ApiResponse<{
    users: Array<{
      user_id: string;
      username: string;
      github_username: string;
      gitlab_username?: string;
      provider?: string;
      avatar_url: string;
      registered_at: string;
      stats: {
        completed_count: number;
        overall_completion: number;
        current_streak: number;
        quizzes_passed: number;
      };
    }>;
    total_results: number;
  }>> {
    return this.get(`/admin/users/search?q=${encodeURIComponent(query)}`);
  }

  /**
   * List users with pagination (admin only)
   *
   * Calls GET /admin/users endpoint to retrieve a paginated list of all registered users
   *
   * @param page - Page number (default: 1)
   * @param pageSize - Items per page (default: 20, max: 100)
   * @returns Promise with paginated user list
   */
  async listUsers(page: number = 1, pageSize: number = 20, search?: string): Promise<ApiResponse<UserListResponse>> {
    let url = `/admin/users?page=${page}&page_size=${pageSize}`;
    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }
    return this.get<UserListResponse>(url);
  }

  /**
   * Get detailed user profile (admin only)
   *
   * Calls GET /admin/users/{user_id}/profile endpoint to retrieve user info, stats, and badges
   *
   * @param userId - The user ID to fetch profile for
   * @returns Promise with user profile data including stats and badges
   */
  async getAdminUserProfile(userId: string): Promise<ApiResponse<AdminUserProfileResponse>> {
    return this.get<AdminUserProfileResponse>(`/admin/users/${encodeURIComponent(userId)}/profile`);
  }

  /**
   * Export users data as CSV (admin only)
   * 
   * Calls GET /admin/export/users endpoint to download all users with stats
   * 
   * @returns Promise with CSV file URL
   */
  async exportUsers(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/admin/export/users`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'users_export.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export users:', error);
      throw error;
    }
  }

  /**
   * Export capstone submissions as CSV (admin only)
   * 
   * Calls GET /admin/export/capstone-submissions endpoint to download all submissions
   * 
   * @returns Promise with CSV file URL
   */
  async exportCapstoneSubmissions(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/admin/export/capstone-submissions`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'capstone_submissions.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export capstone submissions:', error);
      throw error;
    }
  }

  /**
   * Get user profile
   * 
   * Calls GET /user/profile endpoint to retrieve user profile information
   * 
   * @returns Promise with user profile data including is_new_user flag
   */
  async getUserProfile(): Promise<ApiResponse<UserProfileResponse>> {
    return this.get<UserProfileResponse>('/user/profile');
  }

  // ============================================================================
  // Walkthrough Methods
  // ============================================================================
  // NOTE: Walkthrough content is now loaded from local filesystem (frontend/content/walkthroughs/)
  // Only progress tracking uses backend API calls

  /**
   * Get walkthrough progress for a specific walkthrough
   * 
   * Calls GET /api/walkthroughs/[id]/progress endpoint
   * 
   * @param id - Walkthrough identifier
   * @returns Promise with progress data
   */
  async getWalkthroughProgress(
    id: string
  ): Promise<ApiResponse<{ progress: { status: string; started_at?: string; completed_at?: string } }>> {
    return this.get<{ progress: { status: string; started_at?: string; completed_at?: string } }>(
      `/api/walkthroughs/${id}/progress`
    );
  }

  /**
   * Update progress for a walkthrough
   * 
   * Calls POST /api/walkthroughs/[id]/progress endpoint
   * 
   * @param id - Walkthrough identifier
   * @param status - New progress status ('in_progress' or 'completed')
   * @returns Promise with success message
   */
  async updateWalkthroughProgress(
    id: string,
    status: 'in_progress' | 'completed'
  ): Promise<ApiResponse<{ message: string }>> {
    return this.post<{ message: string }>(`/api/walkthroughs/${id}/progress`, { status });
  }

  /**
   * Delete user account
   * 
   * Calls DELETE /user/account endpoint to permanently delete the user's account
   * and all associated data (progress, submissions, etc.)
   * 
   * @returns Promise with success message
   */
  async deleteAccount(): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>('/user/account', {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // Email Methods
  // ============================================================================

  /**
   * Send success story email
   * 
   * Calls POST /api/email/success-story endpoint to send a success story email.
   * This is a public endpoint that does not require authentication.
   * 
   * @param name - User's name
   * @param email - User's email address
   * @param story - Success story text (minimum 50 characters)
   * @param sharePublicly - Whether the user consents to sharing publicly
   * @returns Promise with success message
   */
  async sendSuccessStory(
    name: string,
    email: string,
    story: string,
    sharePublicly: boolean
  ): Promise<ApiResponse<{ message: string }>> {
    return this.post<{ message: string }>('/api/email/success-story', {
      name,
      email,
      story,
      sharePublicly,
    });
  }
}

/**
 * Singleton API client instance
 * 
 * Import and use this instance throughout the application:
 * 
 * ```typescript
 * import { apiClient } from '@/lib/api';
 * 
 * const { data, error } = await apiClient.checkAuth();
 * ```
 */
export const apiClient = new ApiClient(API_BASE_URL);
