import React from 'react';

interface AvatarProps {
  name: string;
  size?: number;
  color?: string;
}

export const Avatar: React.FC<AvatarProps> = ({ name, size = 40, color = '#4f46e5' }) => {
  // Get initials from name
  const initials = name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className={`flex h-[${size}px] w-[${size}px] items-center justify-center rounded-full bg-${color}-200 text-${color}-800 font-medium text-sm`}>
      {initials}
    </div>
  );
};
