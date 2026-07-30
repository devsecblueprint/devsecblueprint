'use client';

interface ExpandableBioProps {
  bio: string;
  className?: string;
}

/**
 * Renders a bio with paragraph support (\n\n splits into separate <p> tags).
 * Always shows the full content — no truncation.
 */
export function ExpandableBio({ bio, className = '' }: ExpandableBioProps) {
  const paragraphs = bio.split('\n\n').filter(Boolean);

  return (
    <div className={className}>
      {paragraphs.map((paragraph, index) => (
        <p key={index} className={index > 0 ? 'mt-3' : ''}>
          {paragraph}
        </p>
      ))}
    </div>
  );
}
