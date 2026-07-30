'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { apiClient } from '@/lib/api';
import type { PublicTestimonial } from '@/lib/types';

const AUTO_ROTATE_INTERVAL = 12000;
const MIN_TESTIMONIALS = 1;

function useCarouselBreakpoint(): number {
  const [cardsPerView, setCardsPerView] = useState(1);

  useEffect(() => {
    function update() {
      if (window.innerWidth >= 1024) {
        setCardsPerView(3);
      } else if (window.innerWidth >= 768) {
        setCardsPerView(2);
      } else {
        setCardsPerView(1);
      }
    }
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return cardsPerView;
}

export function TestimonialCarousel() {
  const [testimonials, setTestimonials] = useState<PublicTestimonial[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const cardsPerView = useCarouselBreakpoint();

  // Fetch approved testimonials on mount
  useEffect(() => {
    let cancelled = false;
    async function fetchTestimonials() {
      try {
        const { data } = await apiClient.getApprovedTestimonials();
        if (!cancelled && data?.testimonials) {
          setTestimonials(data.testimonials);
        }
      } catch {
        // silently fail — carousel just won't render
      } finally {
        if (!cancelled) setLoaded(true);
      }
    }
    fetchTestimonials();
    return () => { cancelled = true; };
  }, []);

  const maxIndex = Math.max(0, testimonials.length - cardsPerView);

  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev >= maxIndex ? 0 : prev + 1));
  }, [maxIndex]);

  const goToPrev = useCallback(() => {
    setCurrentIndex((prev) => (prev <= 0 ? maxIndex : prev - 1));
  }, [maxIndex]);

  const goToIndex = useCallback((index: number) => {
    setCurrentIndex(Math.min(index, maxIndex));
  }, [maxIndex]);

  // Auto-rotate (only when there are more cards than fit in view)
  useEffect(() => {
    if (isPaused || testimonials.length <= cardsPerView) return;
    const timer = setInterval(goToNext, AUTO_ROTATE_INTERVAL);
    return () => clearInterval(timer);
  }, [isPaused, goToNext, testimonials.length, cardsPerView]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        goToPrev();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        goToNext();
      }
    },
    [goToNext, goToPrev]
  );

  // Show spinner while loading
  if (!loaded) {
    return (
      <section className="px-4 sm:px-6 py-12 sm:py-16 md:py-24 bg-white dark:bg-gray-950" aria-label="Learner testimonials">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-8 sm:mb-12">What Our Learners Say</h2>
          <div className="animate-spin inline-block h-6 w-6 border-2 border-gray-300 dark:border-gray-600 border-t-primary-500 dark:border-t-primary-400 rounded-full" />
        </div>
      </section>
    );
  }

  // Show placeholder when no approved testimonials exist
  if (testimonials.length < MIN_TESTIMONIALS) {
    return (
      <section
        className="px-4 sm:px-6 py-12 sm:py-16 md:py-24 bg-white dark:bg-gray-950"
        aria-label="Learner testimonials"
      >
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 text-center mb-8 sm:mb-12">
            What Our Learners Say
          </h2>
          <div className="flex justify-center">
            <div className="bg-gray-50 dark:bg-gray-800 border border-dashed border-gray-300 dark:border-gray-700 rounded-2xl p-8 max-w-md text-center">
              <svg className="w-10 h-10 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                Testimonials are on the way! Be one of the first to share your experience with the DSB platform.
              </p>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const fitsInView = testimonials.length <= cardsPerView;
  const totalDots = maxIndex + 1;

  return (
    <section
      className="px-4 sm:px-6 py-12 sm:py-16 md:py-24 bg-white dark:bg-gray-950"
      aria-label="Learner testimonials"
    >
      <div className="max-w-7xl mx-auto">
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 text-center mb-8 sm:mb-12">
          What Our Learners Say
        </h2>

        <div
          ref={containerRef}
          className="relative"
          onMouseEnter={() => setIsPaused(true)}
          onMouseLeave={() => setIsPaused(false)}
          onKeyDown={handleKeyDown}
          tabIndex={0}
          role="region"
          aria-roledescription="carousel"
          aria-label="Testimonials"
        >
          {/* Aria-live region for screen reader announcements */}
          <div aria-live="polite" className="sr-only">
            Showing testimonial {currentIndex + 1} of {testimonials.length}
          </div>

          {/* Cards container */}
          <div className="overflow-hidden">
            <div
              className={`flex transition-transform duration-500 ease-in-out ${fitsInView ? 'justify-center' : ''}`}
              style={fitsInView ? undefined : {
                transform: `translateX(-${currentIndex * (100 / cardsPerView)}%)`,
              }}
            >
              {testimonials.map((testimonial, index) => (
                <div
                  key={index}
                  className="flex-shrink-0 px-2 sm:px-3"
                  style={{ width: `${100 / (fitsInView ? testimonials.length : cardsPerView)}%`, maxWidth: `${100 / cardsPerView}%` }}
                  role="group"
                  aria-roledescription="slide"
                  aria-label={`Testimonial ${index + 1} of ${testimonials.length}`}
                >
                  <TestimonialCard testimonial={testimonial} />
                </div>
              ))}
            </div>
          </div>

          {/* Previous button */}
          {!fitsInView && (
            <button
              type="button"
              onClick={goToPrev}
              aria-label="Previous testimonial"
              className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 sm:-translate-x-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full p-2 shadow-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-400 transition-colors"
            >
              <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}

          {/* Next button */}
          {!fitsInView && (
            <button
              type="button"
              onClick={goToNext}
              aria-label="Next testimonial"
              className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 sm:translate-x-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full p-2 shadow-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-400 transition-colors"
            >
              <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}
        </div>

        {/* Indicator dots (only when scrolling is needed) */}
        {!fitsInView && (
          <div className="flex justify-center gap-2 mt-6" role="tablist" aria-label="Testimonial navigation">
            {Array.from({ length: totalDots }, (_, i) => (
              <button
                key={i}
                type="button"
                role="tab"
                aria-selected={i === currentIndex}
                aria-label={`Go to testimonial group ${i + 1}`}
                onClick={() => goToIndex(i)}
                className={`w-2.5 h-2.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 dark:focus:ring-offset-gray-950 ${
                  i === currentIndex
                    ? 'bg-primary-500 dark:bg-primary-400'
                    : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
                }`}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}


interface TestimonialCardProps {
  testimonial: PublicTestimonial;
}

function TestimonialCard({ testimonial }: TestimonialCardProps) {
  const { display_name, linkedin_url, quote } = testimonial;
  const isAnonymous = display_name === 'Anonymous';
  const hasLink = !isAnonymous && !!linkedin_url;

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-lg p-6 h-full flex flex-col justify-between min-h-[220px]">
      {/* Large quote icon */}
      <div className="mb-3">
        <svg className="w-8 h-8 text-primary-400" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4.583 17.321C3.553 16.227 3 15 3 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5c-1.073 0-2.099-.49-2.748-1.179zm10 0C13.553 16.227 13 15 13 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5c-1.073 0-2.099-.49-2.748-1.179z" />
        </svg>
      </div>

      {/* Quote */}
      <blockquote className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed mb-4 flex-1">
        {quote}
      </blockquote>

      {/* Attribution */}
      <div className="pt-4 border-t border-gray-100 dark:border-gray-800 flex items-center gap-3">
        {/* Avatar placeholder */}
        <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
          <span className="text-xs font-semibold text-gray-600 dark:text-gray-300">
            {display_name.charAt(0).toUpperCase()}
          </span>
        </div>
        <div>
          {hasLink ? (
            <a
              href={linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-gray-900 dark:text-gray-100 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
            >
              {display_name}
            </a>
          ) : (
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {display_name}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
