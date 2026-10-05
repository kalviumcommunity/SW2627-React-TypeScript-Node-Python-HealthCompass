import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className = '', hover = false }: CardProps) {
  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg ${hover ? 'hover:shadow-md transition-shadow cursor-pointer' : 'shadow-sm'} ${className}`}
    >
      {children}
    </div>
  );
}
