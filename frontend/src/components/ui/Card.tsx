import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export function Card({ children, className = '', hover = false, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={`bg-white border border-gray-200 rounded-lg ${hover ? 'hover:shadow-md transition-shadow cursor-pointer' : 'shadow-sm'} ${className}`}
    >
      {children}
    </div>
  );
}
