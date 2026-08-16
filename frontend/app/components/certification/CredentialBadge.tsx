'use client';

export type CredentialStatus =
  | 'ACTIVE'
  | 'RENEWAL_ELIGIBLE'
  | 'EXPIRED'
  | 'REVOKED';

export interface CredentialBadgeProps {
  credential_id: string;
  credential_status: CredentialStatus;
  issued_at: string;
  expires_at: string;
}

const STATUS_BADGE_STYLES: Record<CredentialStatus, string> = {
  ACTIVE: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  RENEWAL_ELIGIBLE: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  EXPIRED: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  REVOKED: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const STATUS_LABELS: Record<CredentialStatus, string> = {
  ACTIVE: 'Active',
  RENEWAL_ELIGIBLE: 'Renewal Eligible',
  EXPIRED: 'Expired',
  REVOKED: 'Revoked',
};

function formatDate(isoDate: string): string {
  try {
    const date = new Date(isoDate);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return isoDate;
  }
}

export function CredentialBadge({
  credential_id,
  credential_status,
  issued_at,
  expires_at,
}: CredentialBadgeProps) {
  return (
    <div
      className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"
      aria-label={`Credential ${credential_id}, status: ${STATUS_LABELS[credential_status]}`}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="text-base font-semibold text-gray-900 dark:text-gray-100">
          {credential_id}
        </span>
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${STATUS_BADGE_STYLES[credential_status]}`}
          aria-label={`Status: ${STATUS_LABELS[credential_status]}`}
        >
          {STATUS_LABELS[credential_status]}
        </span>
      </div>
      <div className="mt-3 flex flex-col gap-1 text-sm text-gray-600 dark:text-gray-400">
        <span>
          <span className="font-medium text-gray-700 dark:text-gray-300">Issued:</span>{' '}
          {formatDate(issued_at)}
        </span>
        <span>
          <span className="font-medium text-gray-700 dark:text-gray-300">Expires:</span>{' '}
          {formatDate(expires_at)}
        </span>
      </div>
    </div>
  );
}
