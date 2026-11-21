// web/src/theme/ThemeContext.tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { THEME_PRESETS, ThemePreset, DEFAULT_PRESET_ID } from '../../../src/theme-presets';

interface ThemeState {
  presetId: string;
  mode: 'light' | 'dark' | 'system';
  customTokens: Record<string, string>;
  setPreset: (id: string) => void;
  setMode: (mode: 'light' | 'dark' | 'system') => void;
  setCustomToken: (key: string, value: string) => void;
  resetCustomTokens: () => void;
  availablePresets: readonly ThemePreset[];
  currentPreset: ThemePreset;
}

const ThemeContext = createContext<ThemeState | null>(null);

const STORAGE_KEY = 'audiotools-theme';

/** Map semantic --color-* tokens to --custom-* slots expected by design-tokens.css. */
export function colorTokenToCustomVar(key: string): string {
  if (key.startsWith('--custom-')) return key;
  if (key.startsWith('--color-')) return `--custom-${key.slice('--color-'.length)}`;
  if (key.startsWith('--')) return `--custom-${key.slice(2)}`;
  return key;
}

function modeFromPresetId(id: string): 'light' | 'dark' | null {
  if (id.endsWith('-light') || id.includes('-light-')) return 'light';
  if (id.endsWith('-dark') || id.includes('-dark-')) return 'dark';
  return null;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [presetId, setPresetId] = useState(DEFAULT_PRESET_ID);
  const [mode, setMode] = useState<'light' | 'dark' | 'system'>('system');
  const [customTokens, setCustomTokens] = useState<Record<string, string>>({});
  const [hydrated, setHydrated] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setPresetId(parsed.presetId ?? DEFAULT_PRESET_ID);
        setMode(parsed.mode ?? 'system');
        setCustomTokens(parsed.customTokens ?? {});
      }
    } catch { /* ignore */ }
    setHydrated(true);
  }, []);

  // Persist changes. A blocked or missing store must not take Settings down.
  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ presetId, mode, customTokens }));
    } catch { /* ignore */ }
  }, [presetId, mode, customTokens, hydrated]);

  // Apply to document.documentElement
  useEffect(() => {
    if (!hydrated) return;
    const root = document.documentElement;
    const preset = THEME_PRESETS.find(p => p.id === presetId) ?? THEME_PRESETS[0];
    
    root.setAttribute('data-accent', preset.accentId);

    const applyThemeAttr = () => {
      root.setAttribute(
        'data-theme',
        mode === 'system'
          ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
          : mode
      );
    };
    applyThemeAttr();

    // Drop previous inline custom vars so leftover custom colors cannot override presets.
    Array.from(root.style)
      .filter((name) => name.startsWith('--custom-'))
      .forEach((name) => root.style.removeProperty(name));

    if (preset.accentId === 'custom') {
      Object.entries(customTokens).forEach(([key, value]) => {
        root.style.setProperty(key, value);
      });
    }

    if (mode !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => applyThemeAttr();
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, [presetId, mode, customTokens, hydrated]);

  const currentPreset = THEME_PRESETS.find(p => p.id === presetId) ?? THEME_PRESETS[0];

  const setPreset = (id: string) => {
    setPresetId(id);
    const fromName = modeFromPresetId(id);
    if (fromName) setMode(fromName);

    if (id === 'custom') {
      // Initialize custom tokens from current preset
      const preset = THEME_PRESETS.find(p => p.id === presetId);
      if (preset && preset.accentId !== 'custom') {
        const computed = getComputedStyle(document.documentElement);
        const newCustom: Record<string, string> = {};
        [
          '--color-accent-primary', '--color-accent-primary-hover',
          '--color-accent-secondary', '--color-accent-secondary-hover',
          '--color-accent-tertiary', '--color-accent-tertiary-hover',
          '--color-bg-deepest', '--color-bg-deep', '--color-bg-raised', '--color-bg-highlight',
          '--color-text-primary', '--color-text-secondary', '--color-text-muted'
        ].forEach(key => {
          const val = computed.getPropertyValue(key).trim();
          if (val) newCustom[colorTokenToCustomVar(key)] = val;
        });
        setCustomTokens(newCustom);
      }
    } else {
      // Leaving Custom: clear so --custom-* inline vars cannot override accents.
      setCustomTokens({});
    }
  };

  const setCustomToken = (key: string, value: string) => {
    setCustomTokens(prev => ({ ...prev, [key]: value }));
  };

  const resetCustomTokens = () => setCustomTokens({});

  return (
    <ThemeContext.Provider value={{
      presetId, mode, customTokens,
      setPreset, setMode, setCustomToken, resetCustomTokens,
      availablePresets: THEME_PRESETS,
      currentPreset
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
