import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, Check, AlertCircle, XCircle } from 'lucide-react';

export default function ShopperDiscovery({
  catalog,
  onRefreshCatalog,
  lastMutatedSku = null,
  onShowToast
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [reservedSku, setReservedSku] = useState(null);
  const [highlightedSku, setHighlightedSku] = useState(null);
  const prevStockRef = useRef({});

  // Dynamically compute category filter pills from active catalog
  const categories = ['All', ...Array.from(new Set(catalog.map((i) => i.category).filter(Boolean)))];

  // Reset selected category to 'All' if it no longer exists in catalog
  useEffect(() => {
    if (selectedCategory !== 'All' && !categories.includes(selectedCategory)) {
      setSelectedCategory('All');
    }
  }, [catalog, categories, selectedCategory]);

  // Detect stock changes from background 1.5s polling
  useEffect(() => {
    catalog.forEach((item) => {
      const prev = prevStockRef.current[item.sku_id];
      if (prev !== undefined && prev !== item.stock_count) {
        setHighlightedSku(item.sku_id);
        const timer = setTimeout(() => setHighlightedSku(null), 2000);
        return () => clearTimeout(timer);
      }
      prevStockRef.current[item.sku_id] = item.stock_count;
    });
  }, [catalog]);

  useEffect(() => {
    if (lastMutatedSku) {
      setHighlightedSku(lastMutatedSku);
      const timer = setTimeout(() => setHighlightedSku(null), 2500);
      return () => clearTimeout(timer);
    }
  }, [lastMutatedSku]);

  // Filter items
  const filteredItems = catalog.filter((item) => {
    const matchesCat = selectedCategory === 'All' || 
      (item.category && item.category.toLowerCase() === selectedCategory.toLowerCase());
    
    if (!matchesCat) return false;
    if (!searchQuery.trim()) return true;

    const q = searchQuery.toLowerCase();
    const searchable = `${item.item_name} ${item.brand} ${item.category} ${(item.key_specs || []).join(' ')} ${item.color || ''}`.toLowerCase();
    return searchable.includes(q);
  });

  const handleReserve = (item) => {
    if (item.stock_count <= 0) return;
    setReservedSku(item);
    if (onShowToast) {
      onShowToast({
        type: 'success',
        title: 'Item reserved',
        message: `${item.item_name} held at Sharma Electronics for 60 minutes.`
      });
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Store Header */}
      <div className="rounded-lg bg-[#121214] border border-[#27272a] p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-xs text-[#71717a] font-mono mb-1">
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-[#a1a1aa]" />
                0.8 km away
              </span>
              <span>•</span>
              <span className="text-[#a1a1aa]">Sector 14</span>
            </div>
            <h1 className="text-xl font-bold text-[#fafafa] tracking-tight">
              Sharma Electronics & Gear
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#a1a1aa] bg-[#09090b] border border-[#27272a] px-2.5 py-1 rounded">
              1.5s live sync
            </span>
          </div>
        </div>
      </div>

      {/* Search & Category Filter */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 text-[#71717a] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search items or brands..."
            className="w-full pl-9 pr-3 py-1.5 rounded-md bg-[#121214] border border-[#27272a] focus:border-[#fafafa] text-xs text-[#fafafa] placeholder-[#71717a] outline-none transition-colors"
          />
        </div>

        <div className="flex items-center gap-1 overflow-x-auto pb-0.5">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? 'bg-[#fafafa] text-[#09090b]'
                  : 'bg-[#121214] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Product Grid */}
      {filteredItems.length === 0 ? (
        <div className="bg-[#121214] rounded-lg border border-[#27272a] p-10 text-center">
          <p className="text-xs text-[#71717a]">
            No matching items found.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map((item) => {
            const isSoldOut = item.stock_count <= 0;
            const isLowStock = item.stock_count > 0 && item.stock_count <= 2;
            const isHighlighted = highlightedSku === item.sku_id;

            return (
              <div
                key={item.sku_id}
                className={`bg-[#121214] rounded-lg border flex flex-col justify-between overflow-hidden transition-colors ${
                  isHighlighted
                    ? 'border-[#fafafa] bg-[#1c1c1f]'
                    : 'border-[#27272a] hover:border-[#3f3f46]'
                }`}
              >
                <div>
                  {/* Thumbnail */}
                  <div className="relative aspect-[4/3] w-full bg-[#09090b] border-b border-[#27272a] p-2 flex items-center justify-center">
                    <img
                      src={item.thumbnail_url || '/static/thumbnails/sample.jpg'}
                      alt={item.item_name}
                      className="max-h-full max-w-full object-contain"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="%2309090b"/></svg>';
                      }}
                    />

                    {/* Stock Status Badge */}
                    <div className="absolute top-2 right-2">
                      {isSoldOut ? (
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border border-dashed border-[#3f3f46] text-[#71717a] bg-[#09090b]">
                          Sold out
                        </span>
                      ) : isLowStock ? (
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border border-zinc-600 text-[#e4e4e7] bg-[#09090b]">
                          {item.stock_count} left
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border border-[#27272a] text-[#a1a1aa] bg-[#09090b]">
                          {item.stock_count} in stock
                        </span>
                      )}
                    </div>

                    <div className="absolute bottom-2 left-2 text-[10px] font-mono text-[#71717a] bg-[#09090b] px-1.5 py-0.5 rounded border border-[#27272a]">
                      {item.brand}
                    </div>
                  </div>

                  {/* Body Details */}
                  <div className="p-4 space-y-2.5">
                    <div>
                      <h3 className="text-xs font-semibold text-[#fafafa] line-clamp-2">
                        {item.item_name}
                      </h3>
                      {item.color && (
                        <p className="text-[11px] text-[#71717a] mt-0.5">
                          {item.color}
                        </p>
                      )}
                    </div>

                    {/* Key Specs */}
                    {item.key_specs && Array.isArray(item.key_specs) && item.key_specs.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {item.key_specs.map((spec, sidx) => (
                          <span
                            key={sidx}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-[#09090b] text-[#a1a1aa] border border-[#27272a]"
                          >
                            {spec}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer Price & Hold Action */}
                <div className="p-4 pt-0 border-t border-[#27272a] mt-2">
                  <div className="flex items-baseline justify-between pt-2.5 mb-2.5">
                    <span className="text-sm font-semibold font-mono tabular-nums text-[#fafafa]">
                      ₹{Number(item.price_inr).toLocaleString('en-IN')}
                    </span>
                    <span className="text-[11px] font-mono text-[#71717a]">
                      {item.sku_id}
                    </span>
                  </div>

                  <button
                    onClick={() => handleReserve(item)}
                    disabled={isSoldOut}
                    className={`w-full py-1.5 px-3 rounded-md text-xs font-medium transition-colors ${
                      isSoldOut
                        ? 'bg-[#1c1c1f] text-[#52525b] border border-[#27272a] cursor-not-allowed'
                        : 'bg-[#fafafa] text-[#09090b] hover:bg-zinc-200'
                    }`}
                  >
                    {isSoldOut ? 'Sold out' : 'Reserve for pickup'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Reservation Confirmation Modal */}
      {reservedSku && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-[#121214] border border-[#27272a] rounded-lg max-w-sm w-full p-5 space-y-4">
            <div>
              <span className="text-[11px] font-mono text-[#71717a] uppercase">
                Reservation confirmed
              </span>
              <h3 className="text-sm font-semibold text-[#fafafa] mt-1">
                {reservedSku.item_name}
              </h3>
            </div>

            <div className="p-3 rounded-md bg-[#09090b] border border-[#27272a] space-y-1.5 text-xs font-mono">
              <div className="flex justify-between text-[#a1a1aa]">
                <span>Hold window:</span>
                <span className="text-[#fafafa]">60 min</span>
              </div>
              <div className="flex justify-between text-[#a1a1aa]">
                <span>Counter price:</span>
                <span className="text-[#fafafa]">₹{Number(reservedSku.price_inr).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-[#a1a1aa]">
                <span>Location:</span>
                <span className="text-[#fafafa]">Sharma Electronics (0.8 km)</span>
              </div>
            </div>

            <button
              onClick={() => setReservedSku(null)}
              className="w-full py-1.5 rounded-md bg-[#fafafa] hover:bg-zinc-200 text-[#09090b] font-medium text-xs transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
