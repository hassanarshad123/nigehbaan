'use client';

import React, { createContext, useContext, type ReactNode } from 'react';

interface ThemeContextValue {
  theme: 'dark';
}

const ThemeContext = createContext<ThemeContextValue>({ theme: 'dark' });

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const value: ThemeContextValue = { theme: 'dark' };

  return (
    <ThemeContext.Provider value={value}>
      <div className="dark min-h-screen bg-[#0F172A] text-[#F8FAFC]">
        {children}
      </div>
    </ThemeContext.Provider>
  );
}
