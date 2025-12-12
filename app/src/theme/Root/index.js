import React from 'react';

export default function Root({children}) {
  React.useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://static.cloudflareinsights.com/beacon.min.js';
    script.defer = true;
    script.setAttribute('data-cf-beacon', '{"token": "c97b2d4a38744adf8f6c1addf6262b98"}');
    document.head.appendChild(script);
  }, []);

  return <>{children}</>;
}
