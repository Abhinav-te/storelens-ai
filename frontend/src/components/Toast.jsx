import React from 'react';
import { X } from 'lucide-react';

export default function Toast({ toast, onClose }) {
  if (!toast) return null;

  const isError = toast.type === 'error';

  return (
    <div className="fixed bottom-5 right-5 z-50 max-w-sm w-full">
      <div className={`p-3.5 rounded-lg border bg-[#121214] text-[#fafafa] shadow-xl ${
        isError ? 'border-zinc-500' : 'border-[#27272a]'
      }`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${isError ? 'bg-zinc-400' : 'bg-[#fafafa]'}`} />
              <h4 className="text-xs font-semibold text-[#fafafa]">
                {toast.title || (isError ? 'Error' : 'Catalog update')}
              </h4>
            </div>
            <p className="text-xs text-[#a1a1aa] mt-1 leading-relaxed">
              {toast.message}
            </p>
            {toast.meta && (
              <div className="mt-2 text-[11px] font-mono bg-[#09090b] px-2 py-1 rounded border border-[#27272a] text-[#a1a1aa] flex items-center justify-between">
                <span>{toast.meta.sku_id}</span>
                <span className="text-[#fafafa] font-medium uppercase">
                  {toast.meta.action} ({toast.meta.quantity}x)
                </span>
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-[#71717a] hover:text-[#fafafa] p-0.5 rounded transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
