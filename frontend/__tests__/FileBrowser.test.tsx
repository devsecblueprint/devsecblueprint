/**
 * Unit tests for FileBrowser component
 * 
 * Tests:
 * - Rendering of file tree structure
 * - Directory expansion/collapse
 * - File selection and content display
 * - Breadcrumb navigation
 * - Download button presence
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FileBrowser, FileNode } from '@/components/FileBrowser';

// Mock fetch
global.fetch = jest.fn();

describe('FileBrowser', () => {
  const mockFileTree: FileNode[] = [
    {
      name: 'src',
      path: 'src',
      type: 'directory',
      children: [
        {
          name: 'app.py',
          path: 'src/app.py',
          type: 'file'
        }
      ]
    },
    {
      name: 'README.md',
      path: 'README.md',
      type: 'file'
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders file tree structure', () => {
    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={mockFileTree}
      />
    );

    expect(screen.getByText('Code Repository')).toBeInTheDocument();
    expect(screen.getByText('src')).toBeInTheDocument();
    expect(screen.getByText('README.md')).toBeInTheDocument();
  });

  it('displays download button', () => {
    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={mockFileTree}
      />
    );

    const downloadButton = screen.getByLabelText('Download walkthrough as zip');
    expect(downloadButton).toBeInTheDocument();
  });

  it('expands and collapses directories', () => {
    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={mockFileTree}
      />
    );

    // Initially, the directory should be collapsed (children not visible)
    expect(screen.queryByText('app.py')).not.toBeInTheDocument();

    // Click to expand
    const dirButton = screen.getByLabelText('Folder: src');
    fireEvent.click(dirButton);

    // Now children should be visible
    expect(screen.getByText('app.py')).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(dirButton);

    // Children should be hidden again
    expect(screen.queryByText('app.py')).not.toBeInTheDocument();
  });

  it('loads and displays file content when file is selected', async () => {
    const mockContent = 'print("Hello, World!")';
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => mockContent
    });

    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={mockFileTree}
      />
    );

    // Click on a file
    const fileButton = screen.getByLabelText('File: README.md');
    fireEvent.click(fileButton);

    // Wait for content to load
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/walkthroughs/test-walkthrough/files/README.md'
      );
    });

    await waitFor(() => {
      expect(screen.getByText(mockContent)).toBeInTheDocument();
    });
  });

  it('displays breadcrumbs when file is selected', async () => {
    const mockContent = 'test content';
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => mockContent
    });

    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={mockFileTree}
      />
    );

    // Click on a file
    const fileButton = screen.getByLabelText('File: README.md');
    fireEvent.click(fileButton);

    // Wait for breadcrumbs to appear
    await waitFor(() => {
      const breadcrumbs = screen.getByLabelText('File path breadcrumbs');
      expect(breadcrumbs).toBeInTheDocument();
      expect(breadcrumbs).toHaveTextContent('test-walkthrough');
      expect(breadcrumbs).toHaveTextContent('README.md');
    });
  });

  it('shows empty state when no files are provided', () => {
    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={[]}
      />
    );

    expect(screen.getByText('No files found')).toBeInTheDocument();
  });

  it('shows placeholder when no file is selected', () => {
    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={mockFileTree}
      />
    );

    expect(screen.getByText('Select a file to view its contents')).toBeInTheDocument();
  });

  it('handles file loading errors gracefully', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      text: async () => 'Not found'
    });

    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={mockFileTree}
      />
    );

    // Click on a file
    const fileButton = screen.getByLabelText('File: README.md');
    fireEvent.click(fileButton);

    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText('Failed to load file content')).toBeInTheDocument();
    });
  });

  it('displays copy button when file content is loaded', async () => {
    const mockContent = 'test content';
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => mockContent
    });

    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn()
      }
    });

    render(
      <FileBrowser
        walkthroughId="test-walkthrough"
        repositoryPath="walkthroughs/test-walkthrough"
        fileTree={mockFileTree}
      />
    );

    // Click on a file
    const fileButton = screen.getByLabelText('File: README.md');
    fireEvent.click(fileButton);

    // Wait for copy button to appear
    await waitFor(() => {
      expect(screen.getByLabelText('Copy file content')).toBeInTheDocument();
    });
  });
});
