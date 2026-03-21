import { create } from 'zustand';

interface WelcomeState {
  hasSeenIntro: boolean;
  hasSeenTour: boolean;
  mounted: boolean;
  completeIntro: () => void;
  completeTour: () => void;
  resetWelcome: () => void;
  setMounted: () => void;
}

function getStoredBoolean(key: string): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem(key) === 'true';
}

export const useWelcomeStore = create<WelcomeState>((set) => ({
  hasSeenIntro: false,
  hasSeenTour: false,
  mounted: false,
  completeIntro: () => {
    localStorage.setItem('nigehbaan-intro-seen', 'true');
    set({ hasSeenIntro: true });
  },
  completeTour: () => {
    localStorage.setItem('nigehbaan-tour-seen', 'true');
    set({ hasSeenTour: true });
  },
  resetWelcome: () => {
    localStorage.removeItem('nigehbaan-intro-seen');
    localStorage.removeItem('nigehbaan-tour-seen');
    set({ hasSeenIntro: false, hasSeenTour: false });
  },
  setMounted: () => {
    const hasSeenIntro = getStoredBoolean('nigehbaan-intro-seen');
    const hasSeenTour = getStoredBoolean('nigehbaan-tour-seen');
    set({ hasSeenIntro, hasSeenTour, mounted: true });
  },
}));
