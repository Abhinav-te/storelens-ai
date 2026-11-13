import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import MerchantStudio from './components/MerchantStudio';
import ShopperDiscovery from './components/ShopperDiscovery';
import Toast from './components/Toast';
import { getCatalog, resetCatalog } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('merchant');
  const [catalog, setCatalog] = useState([]);
  const [isOperating, setIsOperating] = useState(false);
  const [isSynced, setIsSynced] = useState(true);
  const [toast, setToast] = useState(null);
  const [lastMutatedSku, setLastMutatedSku] = useState(null);
  const toastTimeoutRef = useRef(null);

  const showToast = (toastData) => {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToast(toastData);
    toastTimeoutRef.current = setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  const fetchStoreCatalog = async () => {
    try {
      const data = await getCatalog();
      if (data && data.items) {
        setCatalog(data.items);
        setIsSynced(true);
      }
    } catch (err) {
      console.error('Failed to poll catalog:', err);
      setIsSynced(false);
    }
  };

  useEffect(() => {
    fetchStoreCatalog();
  }, []);

  // Real-time 1.5s background polling
  useEffect(() => {
    const pollInterval = setInterval(() => {
      fetchStoreCatalog();
    }, 1500);

    return () => clearInterval(pollInterval);
  }, []);

  const handleReset = async (seed = false) => {
    setIsOperating(true);
    try {
      const res = await resetCatalog(seed);
      setCatalog(res.items || []);
      showToast({
        type: 'info',
        title: seed ? 'Sample catalog loaded' : 'Catalog cleared',
        message: seed 
          ? 'Loaded 6 pre-recorded items with studio thumbnails.' 
          : 'Store catalog emptied. Ready for video walkthrough upload.'
      });
    } catch (err) {
      console.error('Reset error:', err);
      showToast({
        type: 'error',
        title: 'Reset failed',
        message: err.message
      });
    } finally {
      setIsOperating(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#09090b] text-[#fafafa] font-sans">
      
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onClear={() => handleReset(false)}
        onLoadSample={() => handleReset(true)}
        isOperating={isOperating}
        catalogCount={catalog.length}
        isSynced={isSynced}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6">
        {activeTab === 'merchant' ? (
          <MerchantStudio
            catalog={catalog}
            onRefreshCatalog={fetchStoreCatalog}
            onShowToast={showToast}
            onStockMutated={(skuId) => setLastMutatedSku(skuId)}
          />
        ) : (
          <ShopperDiscovery
            catalog={catalog}
            onRefreshCatalog={fetchStoreCatalog}
            lastMutatedSku={lastMutatedSku}
            onShowToast={showToast}
          />
        )}
      </main>

      {/* Notification Toast */}
      <Toast toast={toast} onClose={() => setToast(null)} />

      {/* Minimal Monochrome Footer */}
      <footer className="border-t border-[#27272a] bg-[#09090b] py-3 text-center text-[11px] font-mono text-[#71717a]">
        StoreLens • Multimodal inventory synchronization
      </footer>

    </div>
  );
}
