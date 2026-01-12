import React from 'react';
import type { Props } from '@theme/Footer/Copyright';

export default function Copyright({ copyright }: Props): React.JSX.Element {
  return (
    <div className="footer__copyright">
      <div>
        Made with ❤️ using{' '}
        <strong>
          <span style={{ color: '#4fd1c7' }}>Docusaurus</span>
        </strong>{' '}
        and a <span style={{ fontStyle: 'italic' }}>sprinkle</span> of{' '}
        <strong>
          <span style={{ color: '#a78bfa' }}>Kiro</span>
        </strong>
        . Powered by{' '}
        <strong>
          <span style={{ color: '#ffa726' }}>AWS</span>.
        </strong>
      </div>
      <div>
        Copyright © {new Date().getFullYear()} DevSec Blueprint LLC
      </div>
    </div>
  );
}