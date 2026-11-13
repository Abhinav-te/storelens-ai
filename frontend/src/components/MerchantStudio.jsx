import React, { useState, useRef } from 'react';
import { 
  Upload, 
  Video, 
  Mic, 
  Plus, 
  Minus, 
  Loader2, 
  Volume2
} from 'lucide-react';
import { onboardVideo, sendVoiceUpdate } from '../services/api';

const SAMPLE_VOICE_QUERIES = [
  'Ek Portronics keyboard bik gaya',
  '2 black headsets sold',
  'Noise smartwatch out of stock',
  'Zebronics mouse 5 aur add karo',
  'SanDisk pendrive ek bech diya'
];

export default function MerchantStudio({
  catalog,
  onRefreshCatalog,
  onShowToast,
  onStockMutated
}) {
  // Dynamically generated voice commands from active catalog or defaults
  const voiceCommands = catalog.length > 0
    ? [
        catalog[0] && `Ek ${catalog[0].brand || ''} ${catalog[0].item_name?.split(' ')[0] || ''} bik gaya`.replace(/\s+/g, ' ').trim(),
        catalog[1] ? `2 ${catalog[1].brand || ''} sold`.replace(/\s+/g, ' ').trim() : `2 ${catalog[0].brand || ''} sold`.trim(),
        catalog[2] ? `${catalog[2].brand || ''} ${catalog[2].item_name?.split(' ')[0] || ''} out of stock`.replace(/\s+/g, ' ').trim() : `${catalog[0].brand || ''} out of stock`.trim(),
        catalog[3] ? `${catalog[3].brand || ''} 3 aur add karo`.replace(/\s+/g, ' ').trim() : `${catalog[0].brand || ''} 3 aur add karo`.trim(),
        catalog[4] ? `${catalog[4].brand || ''} ek bech diya`.replace(/\s+/g, ' ').trim() : `${catalog[0].brand || ''} ek bech diya`.trim()
      ].filter(Boolean)
    : SAMPLE_VOICE_QUERIES;

  // Video Onboarding States
  const [isUploadingVideo, setIsUploadingVideo] = useState(false);
  const [uploadStepText, setUploadStepText] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Audio / Voice States
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);

  // Video Upload Handler
  const handleVideoUpload = async (file = null, useSample = false) => {
    setIsUploadingVideo(true);
    setUploadStepText('Uploading video');

    const stepTimer1 = setTimeout(() => setUploadStepText('Extracting frames and analyzing audio with Gemini'), 1000);
    const stepTimer2 = setTimeout(() => setUploadStepText('Generating studio frames with FFmpeg'), 2500);

    try {
      const response = await onboardVideo(file, useSample);
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);

      onShowToast({
        type: 'success',
        title: 'Video onboarded',
        message: `Extracted ${response.extracted_count || 0} items into the catalog.`
      });

      await onRefreshCatalog();
    } catch (err) {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      console.error('Video upload error:', err);
      onShowToast({
        type: 'error',
        title: 'Upload failed',
        message: err.message || 'Error processing video.'
      });
    } finally {
      setIsUploadingVideo(false);
      setUploadStepText('');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleVideoUpload(e.dataTransfer.files[0], false);
    }
  };

  // MediaRecorder Voice
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        await submitVoicePayload({ audioBlob });
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setRecordingSeconds(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => {
          if (prev >= 4) {
            stopRecording();
            return 5;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err) {
      console.error('Microphone error:', err);
      onShowToast({
        type: 'error',
        title: 'Microphone unavailable',
        message: 'Could not access microphone. Use one of the scenario buttons below.'
      });
    }
  };

  const stopRecording = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const submitVoicePayload = async ({ audioBlob = null, transcript = '' }) => {
    setIsProcessingVoice(true);
    try {
      const result = await sendVoiceUpdate({ audioBlob, transcript });
      
      onShowToast({
        type: 'success',
        title: 'Stock updated',
        message: result.message || `${result.action} on ${result.sku_id}`,
        meta: {
          sku_id: result.sku_id,
          action: result.action,
          quantity: result.quantity
        }
      });

      if (onStockMutated) {
        onStockMutated(result.sku_id);
      }

      await onRefreshCatalog();
    } catch (err) {
      console.error('Voice update error:', err);
      onShowToast({
        type: 'error',
        title: 'Voice update failed',
        message: err.message || 'Could not parse voice command.'
      });
    } finally {
      setIsProcessingVoice(false);
    }
  };

  const handleQuickStockAdjust = async (item, delta) => {
    const action = delta > 0 ? 'INCREMENT' : 'DECREMENT';
    await submitVoicePayload({
      transcript: `${Math.abs(delta)} ${item.brand || ''} ${item.item_name} ${delta > 0 ? 'add karo' : 'bik gaya'}`
    });
  };

  return (
    <div className="space-y-6">
      
      {/* Top Grid: Video Onboarding Dropzone + Voice Command Box */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        {/* Walkthrough Video Upload (7 cols) */}
        <div className="lg:col-span-7 bg-[#121214] rounded-lg border border-[#27272a] p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4 text-[#fafafa]" />
                <h3 className="text-sm font-semibold text-[#fafafa]">Shelf walkthrough</h3>
              </div>
              <span className="text-[11px] font-mono text-[#71717a]">mp4 / webm</span>
            </div>

            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border border-dashed rounded-md p-6 text-center cursor-pointer transition-colors ${
                dragActive
                  ? 'border-[#fafafa] bg-[#1c1c1f]'
                  : 'border-[#27272a] hover:border-[#3f3f46] bg-[#09090b]'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/webm"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleVideoUpload(e.target.files[0], false);
                  }
                }}
              />

              <Upload className="w-5 h-5 text-[#71717a] mx-auto mb-2" />
              <p className="text-xs font-medium text-[#fafafa]">
                Drop shelf video here or browse
              </p>
              <p className="text-[11px] text-[#71717a] mt-0.5">
                Up to 100MB. Audio cues are matched to timestamps.
              </p>
            </div>
          </div>

          {isUploadingVideo && (
            <div className="mt-3 p-3 rounded-md bg-[#1c1c1f] border border-[#27272a]">
              <div className="flex items-center gap-2 text-xs text-[#fafafa]">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#fafafa]" />
                <span>{uploadStepText || 'Processing video'}</span>
              </div>
            </div>
          )}
        </div>

        {/* Voice Stock Update Box (5 cols) */}
        <div className="lg:col-span-5 bg-[#121214] rounded-lg border border-[#27272a] p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-[#fafafa]" />
                <h3 className="text-sm font-semibold text-[#fafafa]">Voice update</h3>
              </div>
              <span className="text-[11px] font-mono text-[#71717a]">Inline audio</span>
            </div>

            {/* Microphone Button */}
            <div className="flex flex-col items-center justify-center py-2">
              <button
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                onTouchStart={startRecording}
                onTouchEnd={stopRecording}
                disabled={isProcessingVoice}
                className={`w-16 h-16 rounded-full border flex flex-col items-center justify-center transition-colors ${
                  isRecording
                    ? 'bg-[#fafafa] text-[#09090b] border-[#fafafa]'
                    : isProcessingVoice
                    ? 'bg-[#1c1c1f] text-[#71717a] border-[#27272a] cursor-wait'
                    : 'bg-[#1c1c1f] hover:bg-[#27272a] text-[#fafafa] border-[#27272a]'
                }`}
              >
                {isRecording ? (
                  <>
                    <Mic className="w-5 h-5" />
                    <span className="text-[9px] font-mono mt-0.5">{recordingSeconds}s</span>
                  </>
                ) : isProcessingVoice ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </button>

              <p className="text-[11px] text-[#71717a] mt-2 font-mono">
                {isRecording
                  ? 'Recording audio. Release to submit.'
                  : isProcessingVoice
                  ? 'Parsing voice instruction...'
                  : 'Hold or click to record 3s voice note'}
              </p>
            </div>
          </div>

          {/* Quick Voice Scenarios */}
          <div className="mt-3 pt-3 border-t border-[#27272a]">
            <span className="text-[10px] font-mono uppercase text-[#71717a] block mb-1.5">
              Quick commands:
            </span>
            <div className="flex flex-wrap gap-1">
              {voiceCommands.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => submitVoicePayload({ transcript: q })}
                  disabled={isProcessingVoice || isRecording}
                  className="text-[11px] px-2 py-1 rounded bg-[#1c1c1f] hover:bg-[#27272a] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a] transition-colors disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* Extracted SKUs Table */}
      <div className="bg-[#121214] rounded-lg border border-[#27272a] overflow-hidden">
        <div className="p-4 border-b border-[#27272a] flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-[#fafafa]">Store inventory</h3>
            <p className="text-xs text-[#71717a] mt-0.5">
              Items extracted from shelf video and synchronized via voice
            </p>
          </div>
          <span className="text-xs font-mono text-[#a1a1aa] border border-[#27272a] bg-[#09090b] px-2 py-0.5 rounded">
            {catalog.length} items
          </span>
        </div>

        {catalog.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-xs text-[#71717a]">
              No items in store. Drop a video or click "Load sample" above.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#09090b] text-[#71717a] font-mono text-[11px] uppercase tracking-wider border-b border-[#27272a]">
                <tr>
                  <th className="py-2.5 px-3">Frame</th>
                  <th className="py-2.5 px-3">Product / Brand</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Price</th>
                  <th className="py-2.5 px-3">Stock</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Adjust</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#27272a]">
                {catalog.map((item) => {
                  const isSoldOut = item.stock_count <= 0;
                  const isLowStock = item.stock_count > 0 && item.stock_count <= 2;

                  return (
                    <tr 
                      key={item.sku_id}
                      className="hover:bg-[#18181b] transition-colors"
                    >
                      {/* Frame */}
                      <td className="py-2.5 px-3">
                        <div className="w-14 h-10 rounded bg-[#09090b] border border-[#27272a] overflow-hidden relative">
                          {item.thumbnail_url ? (
                            <img
                              src={item.thumbnail_url}
                              alt={item.item_name}
                              className="w-full h-full object-contain"
                              onError={(e) => {
                                e.target.onerror = null;
                                e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23121214"/></svg>';
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-[9px] text-[#52525b]">
                              Frame
                            </div>
                          )}
                          <span className="absolute bottom-0.5 right-0.5 bg-black/80 text-[8px] font-mono text-[#a1a1aa] px-1 rounded">
                            {item.timestamp_sec ? `${item.timestamp_sec}s` : '0s'}
                          </span>
                        </div>
                      </td>

                      {/* Product & SKU */}
                      <td className="py-2.5 px-3">
                        <div className="font-medium text-[#fafafa]">
                          {item.item_name}
                        </div>
                        <div className="text-[11px] font-mono text-[#71717a] mt-0.5">
                          <span>{item.sku_id}</span> • <span>{item.brand}</span>
                        </div>
                      </td>

                      {/* Category */}
                      <td className="py-2.5 px-3 text-[#a1a1aa]">
                        {item.category || 'General'}
                      </td>

                      {/* Price */}
                      <td className="py-2.5 px-3 font-mono tabular-nums font-medium text-[#fafafa]">
                        ₹{Number(item.price_inr).toLocaleString('en-IN')}
                      </td>

                      {/* Stock Count */}
                      <td className="py-2.5 px-3 font-mono tabular-nums text-[#fafafa]">
                        {item.stock_count}
                      </td>

                      {/* Status */}
                      <td className="py-2.5 px-3">
                        {isSoldOut ? (
                          <span className="inline-block text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border border-dashed border-[#3f3f46] text-[#71717a]">
                            Sold out
                          </span>
                        ) : isLowStock ? (
                          <span className="inline-block text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border border-zinc-600 bg-transparent text-[#e4e4e7]">
                            Low stock
                          </span>
                        ) : (
                          <span className="inline-block text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border border-[#27272a] bg-[#1c1c1f] text-[#fafafa]">
                            In stock
                          </span>
                        )}
                      </td>

                      {/* Manual Quick Adjust */}
                      <td className="py-2.5 px-3 text-right">
                        <div className="inline-flex items-center gap-1 border border-[#27272a] rounded bg-[#09090b] p-0.5">
                          <button
                            onClick={() => handleQuickStockAdjust(item, -1)}
                            disabled={item.stock_count <= 0}
                            className="p-1 rounded hover:bg-[#1c1c1f] text-[#a1a1aa] hover:text-[#fafafa] disabled:opacity-30 transition-colors"
                            title="Decrement 1"
                          >
                            <Minus className="w-3 h-3" />
                          </button>
                          <span className="px-1.5 font-mono tabular-nums text-xs text-[#fafafa]">
                            {item.stock_count}
                          </span>
                          <button
                            onClick={() => handleQuickStockAdjust(item, 1)}
                            className="p-1 rounded hover:bg-[#1c1c1f] text-[#a1a1aa] hover:text-[#fafafa] transition-colors"
                            title="Increment 1"
                          >
                            <Plus className="w-3 h-3" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
