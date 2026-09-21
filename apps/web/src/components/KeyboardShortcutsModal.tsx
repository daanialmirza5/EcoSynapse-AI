import React, { useEffect } from "react";

export interface ShortcutItem {
  keyCombo: string;
  description: string;
  category: "Navigation" | "Reasoning" | "Export";
}

const SHORTCUTS: ShortcutItem[] = [
  { keyCombo: "Ctrl + K / ⌘ + K", description: "Focus ecological query input", category: "Navigation" },
  { keyCombo: "Ctrl + G / ⌘ + G", description: "Toggle Knowledge Graph view", category: "Reasoning" },
  { keyCombo: "Ctrl + E / ⌘ + E", description: "Export assessment to Markdown", category: "Export" },
  { keyCombo: "Ctrl + Shift + T", description: "Toggle retrieval inspection trace", category: "Reasoning" },
  { keyCombo: "Esc", description: "Close modal / dismiss overlay", category: "Navigation" },
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const KeyboardShortcutsModal: React.FC<Props> = ({ isOpen, onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "/") {
        e.preventDefault();
        if (isOpen) onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard Shortcuts"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-6 text-slate-100 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 font-mono text-sm">⌨</span>
            <h3 className="text-lg font-semibold text-white">Keyboard Shortcuts</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
            aria-label="Close shortcuts modal"
          >
            ✕
          </button>
        </div>

        <div className="mt-4 space-y-3 max-h-80 overflow-y-auto pr-1">
          {SHORTCUTS.map((item, i) => (
            <div
              key={i}
              className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-800/60 border border-slate-700/40 hover:border-slate-600 transition"
            >
              <span className="text-sm text-slate-300">{item.description}</span>
              <kbd className="px-2.5 py-1 text-xs font-mono font-semibold text-emerald-300 bg-slate-900 border border-slate-700 rounded-md shadow-inner">
                {item.keyCombo}
              </kbd>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>Tip: Press <kbd className="px-1.5 py-0.5 font-mono text-slate-300 bg-slate-800 rounded">Esc</kbd> anytime to dismiss</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
