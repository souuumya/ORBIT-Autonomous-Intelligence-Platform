'use client';

import React, { useState, useEffect } from 'react';

interface FormattedTimeProps {
  isoTimestamp: string;
  className?: string;
}

export const FormattedTime: React.FC<FormattedTimeProps> = ({ isoTimestamp, className = '' }) => {
  const [formatted, setFormatted] = useState<string>('');

  useEffect(() => {
    try {
      setFormatted(new Date(isoTimestamp).toLocaleTimeString());
    } catch {
      setFormatted(isoTimestamp);
    }
  }, [isoTimestamp]);

  return (
    <span className={className} suppressHydrationWarning>
      {formatted || (isoTimestamp ? isoTimestamp.substring(11, 19) : '')}
    </span>
  );
};
