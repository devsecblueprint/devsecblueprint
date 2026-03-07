import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { ModuleHealth } from '@/components/admin/ModuleHealth';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    getModuleHealth: jest.fn(),
  },
}));

describe('ModuleHealth Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays loading state initially', () => {
    // Mock API to never resolve
    (apiClient.getModuleHealth as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(<ModuleHealth />);

    expect(screen.getByText('Module Health')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays module health data after successful fetch', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 98.7,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getAllByText('98.7%').length).toBeGreaterThan(0);
    });

    expect(screen.getByText('156')).toBeInTheDocument();
    expect(screen.getByText('Validation Pass Rate')).toBeInTheDocument();
  });

  it('displays error state when fetch fails', async () => {
    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: null,
      error: 'Failed to fetch module health',
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('Failed to Load Module Health')).toBeInTheDocument();
    });

    expect(screen.getByText('Failed to fetch module health')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('displays total modules metric', async () => {
    const mockHealth = {
      total_modules: 200,
      validation_pass_percentage: 100,
      content_by_type: {
        quiz: 50,
        module: 100,
        capstone: 5,
        walkthrough: 45,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('Total Modules')).toBeInTheDocument();
      expect(screen.getByText('200')).toBeInTheDocument();
    });
  });

  it('displays validation pass percentage', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 95.5,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('Validation Pass Rate')).toBeInTheDocument();
      expect(screen.getAllByText('95.5%').length).toBeGreaterThan(0);
    });
  });

  it('displays content type breakdown for quiz', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 100,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('Quizzes')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
    });
  });

  it('displays content type breakdown for module', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 100,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('Modules')).toBeInTheDocument();
      expect(screen.getByText('96')).toBeInTheDocument();
    });
  });

  it('displays content type breakdown for capstone', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 100,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('Capstones')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
    });
  });

  it('displays content type breakdown for walkthrough', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 100,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('Walkthroughs')).toBeInTheDocument();
      expect(screen.getByText('11')).toBeInTheDocument();
    });
  });

  it('displays validation errors when present', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 98.7,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [
        {
          module_id: 'secure-sdlc/broken-quiz',
          error_type: 'missing_field',
          error_message: "Required field 'passing_score' is missing",
        },
        {
          module_id: 'auth/invalid-module',
          error_type: 'validation_error',
          error_message: 'Invalid content structure',
        },
      ],
      status: 'warning' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    // Wait for the expandable section header to appear
    await waitFor(() => {
      expect(screen.getByText('Validation Errors (2)')).toBeInTheDocument();
    });

    // Initially, error details should not be visible (collapsed)
    expect(screen.queryByText('secure-sdlc/broken-quiz')).not.toBeInTheDocument();

    // Click to expand the errors section
    const expandButton = screen.getByRole('button', { name: /Validation Errors \(2\)/i });
    fireEvent.click(expandButton);

    // Now error details should be visible
    await waitFor(() => {
      expect(screen.getByText('secure-sdlc/broken-quiz')).toBeInTheDocument();
    });

    expect(screen.getByText(/missing_field:/)).toBeInTheDocument();
    expect(screen.getByText(/Required field 'passing_score' is missing/)).toBeInTheDocument();
    expect(screen.getByText('auth/invalid-module')).toBeInTheDocument();
    expect(screen.getByText(/validation_error:/)).toBeInTheDocument();
    expect(screen.getByText(/Invalid content structure/)).toBeInTheDocument();
  });

  it('does not display validation errors section when no errors', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 100,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getAllByText('100.0%').length).toBeGreaterThan(0);
    });

    expect(screen.queryByText(/Validation Errors/)).not.toBeInTheDocument();
  });

  it('uses green color for 100% validation pass rate', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 100,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    const { container } = render(<ModuleHealth />);

    await waitFor(() => {
      const progressBar = container.querySelector('.bg-green-600');
      expect(progressBar).toBeInTheDocument();
    });
  });

  it('uses yellow color for 90-99% validation pass rate', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 95,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'warning' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    const { container } = render(<ModuleHealth />);

    await waitFor(() => {
      const progressBar = container.querySelector('.bg-yellow-600');
      expect(progressBar).toBeInTheDocument();
    });
  });

  it('uses red color for less than 90% validation pass rate', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 85,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'error' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    const { container } = render(<ModuleHealth />);

    await waitFor(() => {
      const progressBar = container.querySelector('.bg-red-600');
      expect(progressBar).toBeInTheDocument();
    });
  });

  it('displays passing modules count', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 98.7,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [
        {
          module_id: 'secure-sdlc/broken-quiz',
          error_type: 'missing_field',
          error_message: "Required field 'passing_score' is missing",
        },
        {
          module_id: 'auth/invalid-module',
          error_type: 'validation_error',
          error_message: 'Invalid content structure',
        },
      ],
      status: 'warning' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('154 of 156 modules passing')).toBeInTheDocument();
    });
  });

  it('displays progress bar with correct width', async () => {
    const mockHealth = {
      total_modules: 100,
      validation_pass_percentage: 75,
      content_by_type: {
        quiz: 25,
        module: 50,
        capstone: 10,
        walkthrough: 15,
      },
      validation_errors: [],
      status: 'error' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    const { container } = render(<ModuleHealth />);

    await waitFor(() => {
      const progressBar = container.querySelector('[style*="width: 75%"]');
      expect(progressBar).toBeInTheDocument();
    });
  });

  it('displays content by type section header', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 100,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [],
      status: 'healthy' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    await waitFor(() => {
      expect(screen.getByText('Content by Type')).toBeInTheDocument();
    });
  });

  it('toggles validation errors section when clicked', async () => {
    const mockHealth = {
      total_modules: 156,
      validation_pass_percentage: 98.7,
      content_by_type: {
        quiz: 45,
        module: 96,
        capstone: 4,
        walkthrough: 11,
      },
      validation_errors: [
        {
          module_id: 'test-module',
          error_type: 'test_error',
          error_message: 'Test error message',
        },
      ],
      status: 'warning' as const,
    };

    (apiClient.getModuleHealth as jest.Mock).mockResolvedValue({
      data: mockHealth,
      error: null,
    });

    render(<ModuleHealth />);

    // Wait for the expandable section header to appear
    await waitFor(() => {
      expect(screen.getByText('Validation Errors (1)')).toBeInTheDocument();
    });

    // Initially collapsed - error details not visible
    expect(screen.queryByText('test-module')).not.toBeInTheDocument();

    // Click to expand
    const expandButton = screen.getByRole('button', { name: /Validation Errors \(1\)/i });
    fireEvent.click(expandButton);

    // Now visible
    await waitFor(() => {
      expect(screen.getByText('test-module')).toBeInTheDocument();
    });

    // Click to collapse
    fireEvent.click(expandButton);

    // Should be hidden again
    await waitFor(() => {
      expect(screen.queryByText('test-module')).not.toBeInTheDocument();
    });
  });
});
