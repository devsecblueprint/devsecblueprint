'use client';

import { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import hljs from 'highlight.js/lib/core';
// Import common languages
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import python from 'highlight.js/lib/languages/python';
import json from 'highlight.js/lib/languages/json';
import yaml from 'highlight.js/lib/languages/yaml';
import bash from 'highlight.js/lib/languages/bash';
import dockerfile from 'highlight.js/lib/languages/dockerfile';
import markdown from 'highlight.js/lib/languages/markdown';
import 'highlight.js/styles/github-dark.css';

// Register languages
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('python', python);
hljs.registerLanguage('json', json);
hljs.registerLanguage('yaml', yaml);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('dockerfile', dockerfile);
hljs.registerLanguage('markdown', markdown);

export interface FileBrowserProps {
  walkthroughId: string;
  repositoryPath: string;
  fileTree: FileNode[];
}

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  content?: string;
}

export function FileBrowser({ walkthroughId, repositoryPath, fileTree }: FileBrowserProps) {
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(['']));
  const [loadingFile, setLoadingFile] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mainHeadingRef = useRef<HTMLHeadingElement>(null);

  // Focus management: focus on main heading when component mounts
  useEffect(() => {
    if (mainHeadingRef.current) {
      mainHeadingRef.current.focus();
    }
  }, []);

  const loadFileContent = async (file: FileNode) => {
    if (file.type === 'directory') return;
    
    try {
      setLoadingFile(true);
      setError(null);
      
      // Fetch file content from the API route
      const response = await fetch(`/api/walkthroughs/${walkthroughId}/files/${file.path}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('File not found');
        }
        throw new Error('Failed to load file content');
      }
      
      const content = await response.text();
      setSelectedFile({ ...file, content });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load file';
      setError(errorMessage);
      setSelectedFile({ ...file, content: undefined });
    } finally {
      setLoadingFile(false);
    }
  };

  const retryLoadFile = () => {
    if (selectedFile) {
      loadFileContent(selectedFile);
    }
  };

  // Apply syntax highlighting when file content changes
  useEffect(() => {
    if (selectedFile?.content) {
      const codeElement = document.querySelector('.file-content code');
      if (codeElement) {
        hljs.highlightElement(codeElement as HTMLElement);
      }
    }
  }, [selectedFile?.content]);

  const toggleDirectory = (path: string) => {
    const newExpanded = new Set(expandedDirs);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedDirs(newExpanded);
  };

  const handleDownload = () => {
    // For now, show a message that download is not yet implemented
    alert('Download functionality will be available soon. You can view and copy individual files for now.');
  };

  const getFileIcon = (node: FileNode) => {
    if (node.type === 'directory') {
      return expandedDirs.has(node.path) ? '📂' : '📁';
    }
    
    const ext = node.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py':
        return '🐍';
      case 'js':
      case 'jsx':
      case 'ts':
      case 'tsx':
        return '📜';
      case 'json':
        return '📋';
      case 'md':
        return '📝';
      case 'yml':
      case 'yaml':
        return '⚙️';
      case 'dockerfile':
        return '🐳';
      default:
        return '📄';
    }
  };

  const getLanguageFromFilename = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py':
        return 'python';
      case 'js':
        return 'javascript';
      case 'jsx':
        return 'jsx';
      case 'ts':
        return 'typescript';
      case 'tsx':
        return 'tsx';
      case 'json':
        return 'json';
      case 'md':
        return 'markdown';
      case 'yml':
      case 'yaml':
        return 'yaml';
      case 'sh':
        return 'bash';
      case 'dockerfile':
        return 'dockerfile';
      default:
        return 'text';
    }
  };

  const renderFileTree = (nodes: FileNode[], depth: number = 0) => {
    return nodes.map((node) => (
      <div key={node.path}>
        <button
          onClick={() => {
            if (node.type === 'directory') {
              toggleDirectory(node.path);
            } else {
              loadFileContent(node);
            }
          }}
          className={`w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center gap-2 ${
            selectedFile?.path === node.path ? 'bg-amber-50 dark:bg-amber-900/20' : ''
          }`}
          style={{ paddingLeft: `${depth * 1.5 + 0.75}rem` }}
          aria-label={`${node.type === 'directory' ? 'Folder' : 'File'}: ${node.name}`}
        >
          <span className="text-lg" aria-hidden="true">{getFileIcon(node)}</span>
          <span className="text-sm text-gray-900 dark:text-gray-100 truncate">
            {node.name}
          </span>
        </button>
        {node.type === 'directory' && expandedDirs.has(node.path) && node.children && (
          <div>
            {renderFileTree(node.children, depth + 1)}
          </div>
        )}
      </div>
    ));
  };

  const renderBreadcrumbs = () => {
    if (!selectedFile) return null;
    
    const parts = selectedFile.path.split('/').filter(p => p);
    
    return (
      <nav aria-label="File path breadcrumbs" className="flex items-center gap-2 text-sm mb-4 flex-wrap">
        <button
          onClick={() => setSelectedFile(null)}
          className="text-amber-600 dark:text-amber-400 hover:underline"
        >
          {walkthroughId}
        </button>
        {parts.map((part, index) => (
          <span key={index} className="flex items-center gap-2">
            <span className="text-gray-400">/</span>
            <span className={index === parts.length - 1 ? 'text-gray-900 dark:text-gray-100 font-medium' : 'text-gray-600 dark:text-gray-400'}>
              {part}
            </span>
          </span>
        ))}
      </nav>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header with Download Button */}
      <div className="flex items-center justify-between">
        <h2 
          ref={mainHeadingRef}
          tabIndex={-1}
          className="text-2xl font-bold text-gray-900 dark:text-gray-100 focus:outline-none"
        >
          Code Repository
        </h2>
        <button
          onClick={handleDownload}
          className="inline-flex items-center px-4 py-2 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
          aria-label="Download walkthrough as zip"
        >
          <svg 
            className="w-5 h-5 mr-2" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" 
            />
          </svg>
          Download ZIP
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* File Tree */}
        <Card padding="sm" className="lg:col-span-1">
          <div className="border-b border-gray-200 dark:border-gray-700 pb-3 mb-3">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Files</h3>
          </div>
          <div className="overflow-y-auto max-h-[600px] -mx-4">
            {fileTree.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-600 dark:text-gray-400">
                No files found
              </div>
            ) : (
              renderFileTree(fileTree)
            )}
          </div>
        </Card>

        {/* File Content Viewer */}
        <Card padding="lg" className="lg:col-span-2">
          {selectedFile ? (
            <div>
              {renderBreadcrumbs()}
              
              {loadingFile ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500 mb-3"></div>
                    <div className="text-gray-600 dark:text-gray-400">Loading file...</div>
                  </div>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="text-red-500 dark:text-red-400 mb-4">
                    <svg 
                      className="w-12 h-12 mx-auto" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Unable to Load File
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    {error}
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={retryLoadFile}
                      className="px-4 py-2 bg-amber-500 dark:bg-amber-400 text-gray-900 font-semibold rounded-lg hover:bg-amber-600 dark:hover:bg-amber-500 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
                      aria-label="Retry loading file"
                    >
                      Try Again
                    </button>
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 font-semibold rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500"
                      aria-label="Back to file list"
                    >
                      Back to Files
                    </button>
                  </div>
                </div>
              ) : selectedFile.content !== undefined ? (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <Badge variant="default" size="sm">
                      {getLanguageFromFilename(selectedFile.name)}
                    </Badge>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(selectedFile.content || '');
                        alert('Copied to clipboard!');
                      }}
                      className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
                      aria-label="Copy file content"
                    >
                      Copy
                    </button>
                  </div>
                  <div className="file-content">
                    <pre className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 overflow-x-auto text-sm">
                      <code className={`language-${getLanguageFromFilename(selectedFile.name)}`}>
                        {selectedFile.content}
                      </code>
                    </pre>
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <svg 
                className="w-16 h-16 text-gray-400 mb-4" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
                />
              </svg>
              <p className="text-gray-600 dark:text-gray-400">
                Select a file to view its contents
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
