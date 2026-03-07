'use client';

import { useState, useEffect } from 'react';
import { ModuleQuiz } from '@/components/ModuleQuiz';
import { parseQuizMarkdown, QuizData } from '@/lib/utils/quizParser';
import { apiClient } from '@/lib/api';

export interface ModuleQuizWrapperProps {
  moduleId: string;
  quizPath: string; // Path to quiz.md file relative to public directory
  onQuizComplete?: () => void;
}

interface ModuleCompletion {
  score: number;
  first_completed_at: string;
  completed_at: string;
}

/**
 * Wrapper component that handles quiz.md loading and module completion state.
 * 
 * This component:
 * - Checks for existence of quiz.md file
 * - Parses quiz.md if it exists
 * - Fetches module completion data from backend
 * - Renders ModuleQuiz component with appropriate props
 * - Does NOT display quiz UI if quiz.md does not exist
 */
export function ModuleQuizWrapper({ moduleId, quizPath, onQuizComplete }: ModuleQuizWrapperProps) {
  const [quizData, setQuizData] = useState<QuizData | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  const [bestScore, setBestScore] = useState<number | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Reset state when moduleId or quizPath changes
    setQuizData(null);
    setIsCompleted(false);
    setBestScore(undefined);
    setIsLoading(true);
    setError(null);

    async function loadQuizData() {
      try {
        // Check if quiz.md exists by attempting to fetch it
        const response = await fetch(quizPath);
        
        // If quiz.md doesn't exist (404), don't display quiz UI
        if (!response.ok) {
          if (response.status === 404) {
            // Quiz doesn't exist for this module - this is normal
            setQuizData(null);
            setIsLoading(false);
            return;
          }
          throw new Error(`Failed to load quiz: ${response.statusText}`);
        }

        // Parse quiz.md
        const markdown = await response.text();
        const parsed = parseQuizMarkdown(markdown);
        setQuizData(parsed);

        // Note: Module completion state is not checked on initial load
        // The quiz submission response will indicate if the module was already completed
        // This avoids the need for a separate API endpoint to check quiz completion
        // The "already_completed" flag in the quiz result will handle retake scenarios

        setIsLoading(false);
      } catch (err) {
        console.error('Error loading quiz:', err);
        setError(err instanceof Error ? err.message : 'Failed to load quiz');
        setIsLoading(false);
      }
    }

    loadQuizData();
  }, [moduleId, quizPath]);

  // Don't render anything while loading
  if (isLoading) {
    return (
      <div className="mt-8 flex justify-center">
        <div className="text-gray-600 dark:text-gray-400">
          Loading quiz...
        </div>
      </div>
    );
  }

  // Don't render if there was an error
  if (error) {
    return (
      <div className="mt-8 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <p className="text-sm text-red-800 dark:text-red-200">
          {error}
        </p>
      </div>
    );
  }

  // Don't render quiz UI if quiz.md doesn't exist
  if (!quizData) {
    return null;
  }

  // Render the quiz component
  return (
    <ModuleQuiz
      quizData={quizData}
      moduleId={moduleId}
      isCompleted={isCompleted}
      bestScore={bestScore}
      onQuizComplete={onQuizComplete}
    />
  );
}
