import React from 'react';
import { Store, ShoppingBag } from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  onClear,
  onLoadSample,
  isOperating,
  catalogCount = 0,
  isSynced = true
}) {
  return (
    <header className="sticky top-0 z-40 bg-[#09090b]/95 backdrop-blur border-b border-[#27272a]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14">
          
          {/* Logo & Product Name */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm tracking-tight text-[#fafafa]">
                StoreLens
              </span>
              <span className="text-[11px] font-mono text-[#71717a] border border-[#27272a] px-1.5 py-0.5 rounded">
                v0.1
              </span>
            </div>
          </div>

          {/* Mode Switcher Toggle */}
          <div className="flex items-center p-0.5 rounded-lg bg-[#121214] border border-[#27272a]">
            <button
              onClick={() => setActiveTab('merchant')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'merchant'
                  ? 'bg-[#fafafa] text-[#09090b]'
                  : 'text-[#a1a1aa] hover:text-[#fafafa]'
              }`}
            >
              <Store className="w-3.5 h-3.5" />
              <span>Merchant studio</span>
              {catalogCount > 0 && (
                <span className={`text-[10px] tabular-nums font-mono px-1 rounded ${
                  activeTab === 'merchant' ? 'bg-[#e4e4e7] text-[#09090b]' : 'bg-[#1c1c1f] text-[#a1a1aa]'
                }`}>
                  {catalogCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('shopper')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'shopper'
                  ? 'bg-[#fafafa] text-[#09090b]'
                  : 'text-[#a1a1aa] hover:text-[#fafafa]'
              }`}
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>Shopper discovery</span>
              <span className="text-[10px] text-[#71717a] hidden sm:inline">
                (&lt;3 km)
              </span>
            </button>
          </div>

          {/* Real Status & Actions */}
          <div className="flex items-center gap-2">
            {/* Real Sync Status Indicator */}
            <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono px-2 py-1 rounded border border-[#27272a] bg-[#121214]">
              <span className={`w-1.5 h-1.5 rounded-full ${isSynced ? 'bg-[#fafafa]' : 'bg-[#71717a]'}`} />
              <span className="text-[#a1a1aa] uppercase">{isSynced ? 'Synced' : 'Offline'}</span>
            </div>

            {/* Clear Button */}
            <button
              onClick={onClear}
              disabled={isOperating}
              className="px-2.5 py-1.5 text-xs font-medium text-[#a1a1aa] hover:text-[#fafafa] bg-[#121214] hover:bg-[#1c1c1f] border border-[#27272a] rounded-md transition-colors disabled:opacity-50"
              title="Clear catalog to upload a new video"
            >
              Clear
            </button>

            {/* Load Sample Button */}
            <button
              onClick={onLoadSample}
              disabled={isOperating}
              className="px-2.5 py-1.5 text-xs font-medium text-[#fafafa] bg-[#1c1c1f] hover:bg-[#27272a] border border-[#27272a] rounded-md transition-colors disabled:opacity-50"
              title="Load 6 pre-recorded sample items"
            >
              Load sample
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}
