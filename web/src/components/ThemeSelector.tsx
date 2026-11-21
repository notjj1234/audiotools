// web/src/components/ThemeSelector.tsx
import { useTheme } from '../theme/ThemeContext';
import { ColorSwatch } from './ColorSwatch';
import { ColorPicker } from './ColorPicker';
import { useState } from 'react';
import { Fold } from '../pending';

const TOKEN_GROUPS = {
  'Base layers': [
    { key: '--custom-bg-deepest', label: 'Deepest background', default: '#0a0f0a' },
    { key: '--custom-bg-deep', label: 'Panel background', default: '#141a14' },
    { key: '--custom-bg-raised', label: 'Raised / hover background', default: '#1e261e' },
    { key: '--custom-bg-highlight', label: 'Active / highlight background', default: '#2a342a' },
  ],
  'Text colors': [
    { key: '--custom-text-primary', label: 'Primary text', default: '#e8efe6' },
    { key: '--custom-text-secondary', label: 'Secondary text', default: '#9aa0a6' },
    { key: '--custom-text-muted', label: 'Muted / disabled text', default: '#5f6368' },
  ],
  'Accent colors': [
    { key: '--custom-accent-primary', label: 'Primary accent (buttons, links)', default: '#2f6b4f' },
    { key: '--custom-accent-primary-hover', label: 'Primary accent hover', default: '#255840' },
    { key: '--custom-accent-secondary', label: 'Secondary accent (warnings, solo)', default: '#d4c4a8' },
    { key: '--custom-accent-secondary-hover', label: 'Secondary accent hover', default: '#c4b498' },
    { key: '--custom-accent-tertiary', label: 'Tertiary accent (borders, subtle)', default: '#1e4533' },
    { key: '--custom-accent-tertiary-hover', label: 'Tertiary accent hover', default: '#163626' },
  ],
} as const;

function CustomThemeBuilder({ customTokens, onChange, onReset }: { customTokens: Record<string, string>; onChange: (key: string, value: string) => void; onReset: () => void }) {
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['Accent colors']);

  const getValue = (key: string) => customTokens[key] ?? TOKEN_GROUPS[key as keyof typeof TOKEN_GROUPS]?.[0]?.default ?? '';

  const toggleGroup = (group: string) => {
    setExpandedGroups(prev => prev.includes(group) 
      ? prev.filter(g => g !== group) 
      : [...prev, group]
    );
  };

  return (
    <fieldset style={{ border: '1px solid var(--color-accent-primary)', borderRadius: '8px', padding: '0.75rem', background: 'rgba(47, 107, 79, 0.05)' }}>
      <legend style={{ fontWeight: 500, fontSize: '0.85rem', color: 'var(--color-accent-primary)' }}>
        Custom theme
      </legend>
      <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', margin: '0 0 0.75rem' }}>
        Adjust any color. Changes apply instantly. <button type="button" onClick={onReset} style={{ color: 'var(--color-accent-primary)', background: 'none', border: 'none', textDecoration: 'underline', cursor: 'pointer' }}>Reset to preset</button>
      </p>
      
      {Object.entries(TOKEN_GROUPS).map(([groupName, tokens]) => (
        <div key={groupName} style={{ marginBottom: '0.75rem' }}>
          <button
            type="button"
            aria-expanded={expandedGroups.includes(groupName)}
            onClick={() => toggleGroup(groupName)}
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.5rem',
              background: 'transparent',
              border: 'none',
              color: 'var(--color-text-primary)',
              fontWeight: 600,
              fontSize: '0.8rem',
              cursor: 'pointer',
              textAlign: 'left'
            }}
          >
            {groupName}
            <span
              className={`theme-chevron${expandedGroups.includes(groupName) ? " is-open" : ""}`}
              aria-hidden="true"
            >
              ▼
            </span>
          </button>
          <Fold open={expandedGroups.includes(groupName)}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.5rem', marginTop: '0.5rem', paddingLeft: '0.5rem' }}>
              {tokens.map(({ key, label, default: def }) => (
                <ColorPicker
                  key={key}
                  label={label}
                  value={getValue(key)}
                  onChange={(val) => onChange(key, val)}
                  defaultValue={def}
                />
              ))}
            </div>
          </Fold>
        </div>
      ))}
      
      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
        <button type="button" onClick={onReset} style={{ padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid var(--color-border-subtle)', background: 'var(--color-bg-raised)', color: 'var(--color-text-primary)', fontWeight: 600, cursor: 'pointer' }}>
          Reset All
        </button>
        <button type="button" onClick={() => navigator.clipboard.writeText(JSON.stringify(customTokens, null, 2))} style={{ padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid var(--color-accent-primary)', background: 'var(--color-accent-primary)', color: '#fff', fontWeight: 600, cursor: 'pointer' }}>
          Export JSON
        </button>
        <input type="file" accept=".json" style={{ display: 'none' }} id="theme-import" onChange={e => {
          const file = e.target.files?.[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = () => {
              try {
                const imported = JSON.parse(reader.result as string);
                Object.entries(imported).forEach(([k, v]) => onChange(k, v as string));
              } catch { alert('Invalid theme file'); }
            };
            reader.readAsText(file);
          }
        }} />
        <label htmlFor="theme-import" style={{ padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid var(--color-border-subtle)', background: 'var(--color-bg-raised)', color: 'var(--color-text-primary)', fontWeight: 600, cursor: 'pointer' }}>
          Import JSON
        </label>
      </div>
    </fieldset>
  );
}

export function ThemeSelector({ compact = false }: { compact?: boolean }) {
  const { presetId, mode, setPreset, setMode, availablePresets, currentPreset, customTokens, setCustomToken, resetCustomTokens } = useTheme();

  return (
    <div className="theme-selector" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {/* Mode Toggle */}
      <fieldset style={{ border: '1px solid var(--color-border-subtle)', borderRadius: '8px', padding: '0.75rem' }}>
        <legend style={{ fontWeight: 500, fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
          Theme mode
        </legend>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {(['light', 'dark', 'system'] as const).map(m => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                border: `1px solid ${mode === m ? 'var(--color-accent-primary)' : 'var(--color-border-subtle)'}`,
                background: mode === m ? 'var(--color-accent-primary)' : 'var(--color-bg-raised)',
                color: mode === m ? '#fff' : 'var(--color-text-primary)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>
      </fieldset>

      {/* Preset Grid */}
      <fieldset style={{ border: '1px solid var(--color-border-subtle)', borderRadius: '8px', padding: '0.75rem' }}>
        <legend style={{ fontWeight: 500, fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
          Color preset
          {currentPreset.isColorblindSafe ? (
            <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', color: 'var(--color-text-muted)', fontWeight: 400 }}>
              colorblind-safe
            </span>
          ) : null}
        </legend>
        <div style={{ display: 'grid', gridTemplateColumns: compact ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: '0.5rem' }}>
          {availablePresets.map(preset => (
            <button
              key={preset.id}
              type="button"
              onClick={() => setPreset(preset.id)}
              className="theme-preset"
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.35rem',
                padding: '0.75rem',
                borderRadius: '8px',
                border: `2px solid ${presetId === preset.id ? 'var(--color-accent-primary)' : 'var(--color-border-subtle)'}`,
                background: presetId === preset.id ? 'var(--color-bg-highlight)' : 'var(--color-bg-deep)',
                cursor: 'pointer',
                textAlign: 'center'
              }}
              title={preset.description}
            >
              <div style={{ display: 'flex', gap: '4px' }}>
                <ColorSwatch color={preset.preview.bg} label="BG" />
                <ColorSwatch color={preset.preview.primary} label="Primary" />
                <ColorSwatch color={preset.preview.secondary} label="Accent" />
                <ColorSwatch color={preset.preview.text} label="Text" />
              </div>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{preset.label}</span>
              <span style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)' }}>{preset.description}</span>
            </button>
          ))}
        </div>
      </fieldset>

      {/* Custom Theme Builder (when 'custom' selected) */}
      {presetId === 'custom' && (
        <CustomThemeBuilder customTokens={customTokens} onChange={setCustomToken} onReset={resetCustomTokens} />
      )}
    </div>
  );
}