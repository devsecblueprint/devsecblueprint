'use client';

import { useState } from 'react';
import { QuizData } from '@/lib/utils/quizParser';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { apiClient } from '@/lib/api';
import { triggerBadgeCheck } from '@/lib/events';

export interface ModuleQuizProps {
  quizData: QuizData;
  moduleId: string;
  isCompleted: boolean;
  bestScore?: number;
  onQuizComplete?: () => void;
}

export interface QuestionResult {
  question_id: string;
  correct: boolean;
  correct_answer: string;
  explanation: string;
}

export interface QuizResult {
  passed: boolean;
  score: number;
  passing_score: number;
  already_completed: boolean;
  results: QuestionResult[];
  current_streak: number;
}

/**
 * Convert markdown bold syntax to React elements
 */
function renderTextWithBold(text: string) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

export function ModuleQuiz({ quizData, moduleId, isCompleted, bestScore, onQuizComplete }: ModuleQuizProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);

  const handleAnswerSelect = (questionId: string, answer: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleRetry = () => {
    // Reset quiz state for retry
    setSelectedAnswers({});
    setQuizResult(null);
    setError(null);
  };

  const handleContinue = () => {
    // Reset quiz state to allow retake
    setSelectedAnswers({});
    setQuizResult(null);
    setError(null);
    
    // Refresh user stats and update sidebar state
    if (onQuizComplete) {
      onQuizComplete();
    }
  };

  const allQuestionsAnswered = quizData.questions.every(
    question => selectedAnswers[question.id]
  );

  const handleSubmit = async () => {
    // Clear any previous errors
    setError(null);
    setIsSubmitting(true);

    try {
      // Send POST request to /quiz/submit with module_id and answers
      const response = await apiClient.post<QuizResult>('/quiz/submit', {
        module_id: moduleId,
        answers: selectedAnswers
      });

      // Handle error response
      if (response.error) {
        // Use status code for precise error handling
        if (response.statusCode === 404) {
          // Quiz not found in registry (QUIZ_NOT_FOUND)
          setError('This quiz is not available. Please contact support if this problem persists.');
        } else if (response.statusCode === 503) {
          // Registry unavailable (REGISTRY_UNAVAILABLE)
          setError('The quiz service is temporarily unavailable. Please try again in a few moments.');
        } else {
          // Generic error message for other errors
          setError(response.error);
        }
        
        setIsSubmitting(false);
        return;
      }

      // Handle success response
      if (response.data) {
        setQuizResult(response.data);
        
        // Trigger badge check after completing a quiz (whether passed or failed)
        triggerBadgeCheck();
      }
    } catch (err) {
      // Handle network errors
      setError(err instanceof Error ? err.message : 'Failed to submit quiz. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mt-8">
      <Card padding="lg">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Module Quiz
          </h2>
          
          {/* Completed Module Indicator */}
          {isCompleted && bestScore !== undefined && (
            <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <svg 
                  className="w-5 h-5 text-green-600 dark:text-green-400" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
                  />
                </svg>
                <h3 className="text-sm font-bold text-green-900 dark:text-green-100">
                  Module Completed
                </h3>
              </div>
              <p className="text-sm text-green-800 dark:text-green-200">
                Best Score: <span className="font-semibold">{bestScore}%</span>
              </p>
              <p className="text-xs text-green-700 dark:text-green-300 mt-2">
                You can retake this quiz to improve your score.
              </p>
            </div>
          )}
          
          {/* Retake Indicator - shown when taking quiz after completion */}
          {isCompleted && !quizResult && Object.keys(selectedAnswers).length > 0 && (
            <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
              <p className="text-sm text-amber-800 dark:text-amber-200">
                <span className="font-semibold">Retake Attempt:</span> This is a retake to improve your score.
              </p>
            </div>
          )}
          
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Passing Score: {quizData.passingScore}%
          </p>
        </div>

        {/* Questions */}
        <div className="space-y-6">
          {quizData.questions.map((question, index) => {
            // Get result for this question if quiz has been submitted
            const questionResult = quizResult?.results.find(r => r.question_id === question.id);
            const showResults = !!quizResult;
            
            return (
              <div key={question.id} className="border-b border-gray-200 dark:border-gray-700 pb-6 last:border-b-0">
                {/* Question Text */}
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {index + 1}. {renderTextWithBold(question.text)}
                  </h3>
                </div>

                {/* Options */}
                <div className="space-y-2">
                  {question.options.map((option) => {
                    const isSelected = selectedAnswers[question.id] === option.key;
                    const isCorrectAnswer = questionResult?.correct_answer === option.key;
                    const isUserAnswer = showResults && isSelected;
                    const isCorrect = questionResult?.correct;
                    
                    // Determine styling based on result state
                    let optionStyles = '';
                    if (showResults) {
                      if (isUserAnswer && isCorrect) {
                        // User's answer is correct - green
                        optionStyles = 'border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-400';
                      } else if (isUserAnswer && !isCorrect) {
                        // User's answer is incorrect - red
                        optionStyles = 'border-red-500 bg-red-50 dark:bg-red-900/20 dark:border-red-400';
                      } else if (isCorrectAnswer) {
                        // Show correct answer - green
                        optionStyles = 'border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-400';
                      } else {
                        optionStyles = 'border-gray-200 dark:border-gray-700';
                      }
                    } else {
                      // Normal quiz-taking mode
                      optionStyles = isSelected
                        ? 'border-amber-500 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-400'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600';
                    }
                    
                    return (
                      <button
                        key={option.key}
                        onClick={() => !showResults && handleAnswerSelect(question.id, option.key)}
                        disabled={showResults}
                        className={`w-full text-left p-4 rounded-lg border-2 transition-all ${optionStyles} ${
                          showResults ? 'cursor-default' : ''
                        }`}
                      >
                        <div className="flex items-start">
                          <span className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center mr-3 ${
                            showResults
                              ? (isUserAnswer && isCorrect) || isCorrectAnswer
                                ? 'border-green-500 bg-green-500 dark:border-green-400 dark:bg-green-400'
                                : isUserAnswer && !isCorrect
                                ? 'border-red-500 bg-red-500 dark:border-red-400 dark:bg-red-400'
                                : 'border-gray-300 dark:border-gray-600'
                              : isSelected
                              ? 'border-amber-500 bg-amber-500 dark:border-amber-400 dark:bg-amber-400'
                              : 'border-gray-300 dark:border-gray-600'
                          }`}>
                            {((showResults && ((isUserAnswer && isCorrect) || isCorrectAnswer)) || (!showResults && isSelected)) && (
                              <svg 
                                className="w-4 h-4 text-white" 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                                aria-hidden="true"
                              >
                                <path 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round" 
                                  strokeWidth={3} 
                                  d="M5 13l4 4L19 7" 
                                />
                              </svg>
                            )}
                            {showResults && isUserAnswer && !isCorrect && (
                              <svg 
                                className="w-4 h-4 text-white" 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                                aria-hidden="true"
                              >
                                <path 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round" 
                                  strokeWidth={3} 
                                  d="M6 18L18 6M6 6l12 12" 
                                />
                              </svg>
                            )}
                          </span>
                          <div className="flex-1">
                            <span className="font-medium text-gray-900 dark:text-gray-100 mr-2">
                              {option.key}.
                            </span>
                            <span className="text-gray-700 dark:text-gray-300">
                              {renderTextWithBold(option.text)}
                            </span>
                            {showResults && isCorrectAnswer && (
                              <span className="ml-2 text-sm font-semibold text-green-600 dark:text-green-400">
                                (Correct Answer)
                              </span>
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Explanation for incorrect answers */}
                {showResults && questionResult && !questionResult.correct && (
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                      Explanation:
                    </h4>
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      {questionResult.explanation}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Submit Button / Results */}
        <div className="mt-6">
          {/* Quiz Results - Show for both passed and failed */}
          {quizResult && (
            <div className="mb-6">
              {/* Score Display */}
              <div className={`p-6 border-2 rounded-lg mb-4 ${
                quizResult.passed 
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                  : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
              }`}>
                <div className="text-center">
                  <h3 className={`text-xl font-bold mb-2 ${
                    quizResult.passed
                      ? 'text-green-900 dark:text-green-100'
                      : 'text-red-900 dark:text-red-100'
                  }`}>
                    {quizResult.passed ? 'Quiz Passed!' : 'Quiz Not Passed'}
                  </h3>
                  <div className="flex items-center justify-center gap-4 text-lg">
                    <div>
                      <span className="text-gray-700 dark:text-gray-300">Your Score: </span>
                      <span className={`font-bold ${
                        quizResult.passed
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {quizResult.score}%
                      </span>
                    </div>
                    <div className="text-gray-400 dark:text-gray-600">|</div>
                    <div>
                      <span className="text-gray-700 dark:text-gray-300">Passing Score: </span>
                      <span className="font-bold text-gray-900 dark:text-gray-100">
                        {quizResult.passing_score}%
                      </span>
                    </div>
                  </div>
                  <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">
                    {quizResult.passed 
                      ? 'Review your answers below to see what you got right and wrong.'
                      : 'Review the explanations below and try again when you\'re ready.'}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-center gap-4">
                {!quizResult.passed && (
                  <Button
                    variant="primary"
                    onClick={handleRetry}
                    className="px-8 py-3"
                  >
                    Retry Quiz
                  </Button>
                )}
                {quizResult.passed && (
                  <Button
                    variant="primary"
                    onClick={handleContinue}
                    className="px-8 py-3"
                  >
                    Continue Learning
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && !quizResult && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-800 dark:text-red-200">
                {error}
              </p>
            </div>
          )}

          {/* Submit Button - only show if quiz not yet submitted or passed */}
          {!quizResult && (
            <div className="flex justify-center">
              <Button
                variant="primary"
                disabled={!allQuestionsAnswered || isSubmitting}
                onClick={handleSubmit}
                className="px-8 py-3"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Quiz'}
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
