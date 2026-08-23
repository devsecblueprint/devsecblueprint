'use client';

import { useState, useEffect } from 'react';

export interface CertificatePreviewProps {
  pathwayId: string;
}

export function CertificatePreview({ pathwayId }: CertificatePreviewProps) {
  const [svgUrl, setSvgUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;

    const fetchSvg = async () => {
      setIsLoading(true);
      setError(false);

      try {
        // Fetch the SVG as a blob from the preview endpoint
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || ''}/certifications/${encodeURIComponent(pathwayId)}/credential/preview`,
          {
            credentials: 'include',
          }
        );

        if (!response.ok) {
          setError(true);
          return;
        }

        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        setSvgUrl(objectUrl);
      } catch {
        setError(true);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSvg();

    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [pathwayId]);

  if (isLoading) {
    return (
      <div className="w-full aspect-[16/11] bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse flex items-center justify-center">
        <p className="text-sm text-gray-400 dark:text-gray-500">Loading certificate preview...</p>
      </div>
    );
  }

  if (error || !svgUrl) {
    return (
      <div className="w-full aspect-[16/11] bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center border border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-500 dark:text-gray-400">Certificate preview unavailable</p>
      </div>
    );
  }

  return (
    <div className="w-full rounded-xl overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700">
      <img
        src={svgUrl}
        alt="Certificate of Achievement"
        className="w-full h-auto"
      />
    </div>
  );
}
