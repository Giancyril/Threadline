import React, { useState } from 'react';
import { Sliders, Save, Check } from 'lucide-react';

export const SettingsView: React.FC = () => {
  const [conciseness, setConciseness] = useState(70);
  const [tone, setTone] = useState<'casual' | 'professional' | 'technical'>('professional');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-50 overflow-hidden">
      <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-600" />
            Persona & Interaction Style
          </h2>
          <p className="text-xs text-slate-500">Configure behavioral preferences (kept distinct from factual memories)</p>
        </div>

        <button
          type="button"
          onClick={handleSave}
          className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold flex items-center gap-2 hover:bg-indigo-700 transition-all cursor-pointer shadow-sm shadow-indigo-200"
        >
          {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          {saved ? 'Saved!' : 'Save Style'}
        </button>
      </header>

      <div className="p-8 max-w-3xl space-y-6">
        <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-4 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900">Communication Tone</h3>
          <div className="grid grid-cols-3 gap-3">
            {(['casual', 'professional', 'technical'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTone(t)}
                className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                  tone === t
                    ? 'border-indigo-600 bg-indigo-50/60 text-indigo-950 font-bold'
                    : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <p className="text-xs capitalize font-semibold">{t}</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {t === 'casual' && 'Friendly, conversational, concise'}
                  {t === 'professional' && 'Polished, structured, business-ready'}
                  {t === 'technical' && 'In-depth, code-first, rigorous'}
                </p>
              </button>
            ))}
          </div>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Conciseness Bias</h3>
            <span className="text-xs font-mono font-bold text-indigo-600">{conciseness}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={conciseness}
            onChange={(e) => setConciseness(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>Detailed & Explanatory</span>
            <span>Balanced</span>
            <span>Ultra Concise & Direct</span>
          </div>
        </div>
      </div>
    </div>
  );
};
