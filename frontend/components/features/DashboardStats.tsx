import React from 'react';
import { Card } from '@/components/ui/Card';

export interface Stat {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
}

export interface DashboardStatsProps {
  stats: Stat[];
}

export function DashboardStats({ stats }: DashboardStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {stats.map((stat, index) => (
        <Card key={index} padding="md">
          <div className="flex flex-col items-center text-center">
            {stat.icon && (
              <div className="mb-3 text-amber-500 dark:text-amber-400">
                {stat.icon}
              </div>
            )}
            <div className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {stat.value}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {stat.label}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
