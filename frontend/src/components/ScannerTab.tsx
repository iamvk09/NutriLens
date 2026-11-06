import React, { useState, useRef } from 'react';
import { Barcode, ScanLine, AlertTriangle, CheckCircle, RefreshCw, Camera, AlertCircle } from 'lucide-react';
import { BarcodeProduct, LabelAnalysis } from '../types';
import { scanBarcode, scanLabel } from '../services/api';

export const ScannerTab: React.FC = () => {
  const [mode, setMode] = useState<'barcode' | 'label'>('barcode');
  const [barcodeInput, setBarcodeInput] = useState('');
  const [barcodeFile, setBarcodeFile] = useState<File | null>(null);
  const [labelFile, setLabelFile] = useState<File | null>(null);
  const [scanning, setScanning] = useState(false);
  const [barcodeResult, setBarcodeResult] = useState<BarcodeProduct | null>(null);
  const [labelResult, setLabelResult] = useState<LabelAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const barcodeInputRef = useRef<HTMLInputElement>(null);
  const labelInputRef = useRef<HTMLInputElement>(null);

  const handleBarcodeLookup = async () => {
    if (!barcodeInput.trim() && !barcodeFile) return;
    setScanning(true);
    setError(null);
    setBarcodeResult(null);

    try {
      const res = await scanBarcode(barcodeFile || undefined, barcodeInput.trim() || undefined);
      setBarcodeResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to lookup barcode in OpenFoodFacts.');
    } finally {
      setScanning(false);
    }
  };

  const handleLabelInspect = async () => {
    if (!labelFile) return;
    setScanning(true);
    setError(null);
    setLabelResult(null);

    try {
      const res = await scanLabel(labelFile);
      setLabelResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to inspect nutrition label with Gemini Vision.');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pb-24 md:pb-12 space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Product & Nutrition Scanner</h1>
        <p className="text-gray-400 text-sm mt-1">
          Scan standard barcodes via OpenFoodFacts or evaluate ingredients with AI OCR inspection.
        </p>
      </div>

      {/* Mode Switcher */}
      <div className="flex bg-[#121620] border border-[#272e3d] rounded-2xl p-1.5 max-w-md">
        <button
          onClick={() => {
            setMode('barcode');
            setError(null);
          }}
          className={`flex-1 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center space-x-2 transition ${
            mode === 'barcode'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <Barcode className="w-4 h-4" />
          <span>Barcode (OpenFoodFacts)</span>
        </button>

        <button
          onClick={() => {
            setMode('label');
            setError(null);
          }}
          className={`flex-1 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center space-x-2 transition ${
            mode === 'label'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <ScanLine className="w-4 h-4" />
          <span>Label Vision (Gemini OCR)</span>
        </button>
      </div>

      {/* Mode 1: Barcode Scanner */}
      {mode === 'barcode' && (
        <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-6 shadow-xl space-y-6">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block mb-2">
                Enter Barcode Number
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={barcodeInput}
                  onChange={(e) => setBarcodeInput(e.target.value)}
                  placeholder="e.g. 3017620422003 (Nutella), 737628064502..."
                  className="flex-1 bg-[#181d2a] border border-[#272e3d] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition font-mono"
                />
                <button
                  onClick={handleBarcodeLookup}
                  disabled={scanning || (!barcodeInput.trim() && !barcodeFile)}
                  className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl font-semibold text-sm flex items-center space-x-2 shadow-lg shadow-emerald-600/20 transition flex-shrink-0"
                >
                  {scanning ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Searching...</span>
                    </>
                  ) : (
                    <span>Lookup</span>
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-2 text-xs text-gray-400">
              <span className="h-px flex-1 bg-[#242b3b]" />
              <span>OR UPLOAD BARCODE PHOTO</span>
              <span className="h-px flex-1 bg-[#242b3b]" />
            </div>

            <div
              onClick={() => barcodeInputRef.current?.click()}
              className="border-2 border-dashed border-[#272e3d] hover:border-emerald-500/40 rounded-xl p-4 text-center cursor-pointer bg-[#181d2a]/50 transition"
            >
              <p className="text-xs text-gray-300">
                {barcodeFile ? `Selected: ${barcodeFile.name}` : 'Click to select or photograph a product barcode image'}
              </p>
              <input
                ref={barcodeInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setBarcodeFile(e.target.files[0]);
                  }
                }}
              />
            </div>
          </div>

          {/* Barcode Results */}
          {barcodeResult && (
            <div className="p-5 rounded-2xl bg-[#181d2a] border border-[#272e3d] space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    OpenFoodFacts Verified
                  </span>
                  <h3 className="text-lg font-bold text-white mt-1.5">{barcodeResult.product_name}</h3>
                  <p className="text-xs text-gray-400">Brand: {barcodeResult.brand || 'Unspecified'}</p>
                </div>
                {barcodeResult.image_url && (
                  <img
                    src={barcodeResult.image_url}
                    alt={barcodeResult.product_name}
                    className="w-16 h-16 object-contain rounded-lg border border-[#272e3d] bg-white p-1"
                  />
                )}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-[#121620] border border-[#222938]">
                  <p className="text-[10px] text-gray-500 uppercase">Nutri-Score</p>
                  <p className="text-base font-bold text-emerald-400 uppercase mt-0.5">
                    {barcodeResult.nutriscore_grade || 'N/A'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-[#121620] border border-[#222938]">
                  <p className="text-[10px] text-gray-500 uppercase">NOVA Group</p>
                  <p className="text-base font-bold text-amber-400 mt-0.5">
                    {barcodeResult.nova_group ? `Group ${barcodeResult.nova_group}` : 'N/A'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-[#121620] border border-[#222938] col-span-2 sm:col-span-1">
                  <p className="text-[10px] text-gray-500 uppercase">Allergens</p>
                  <p className="text-xs font-medium text-gray-300 mt-0.5 line-clamp-1">
                    {barcodeResult.allergens || 'None detected'}
                  </p>
                </div>
              </div>

              {barcodeResult.ingredients_text && (
                <div className="pt-2 border-t border-[#222938]">
                  <p className="text-[11px] font-semibold text-gray-400 uppercase mb-1">Ingredients</p>
                  <p className="text-xs text-gray-300 leading-relaxed">{barcodeResult.ingredients_text}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Mode 2: Label Vision (Gemini Vision) */}
      {mode === 'label' && (
        <div className="bg-[#121620] border border-[#272e3d] rounded-2xl p-6 shadow-xl space-y-6">
          <div
            onClick={() => labelInputRef.current?.click()}
            className="border-2 border-dashed border-[#272e3d] hover:border-emerald-500/40 rounded-xl p-8 text-center cursor-pointer bg-[#181d2a]/50 transition"
          >
            <Camera className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-gray-200">
              {labelFile ? `Selected: ${labelFile.name}` : 'Upload photo of ingredients or nutrition label'}
            </p>
            <p className="text-xs text-gray-400 mt-1">Our AI extracts preservatives, harmful additives, and scores health</p>
            <input
              ref={labelInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setLabelFile(e.target.files[0]);
                }
              }}
            />
          </div>

          {labelFile && (
            <button
              onClick={handleLabelInspect}
              disabled={scanning}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-lg shadow-emerald-600/20 flex items-center justify-center space-x-2 transition"
            >
              {scanning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Inspecting Ingredients with Vision AI...</span>
                </>
              ) : (
                <span>Analyze Nutrition Facts Label</span>
              )}
            </button>
          )}

          {/* Label Results */}
          {labelResult && (
            <div className="p-5 rounded-2xl bg-[#181d2a] border border-[#272e3d] space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">{labelResult.product_name}</h3>
                  <span className="text-xs text-gray-400">AI Health Assessment</span>
                </div>
                <div className="px-3 py-1 rounded-xl bg-emerald-500/10 text-emerald-400 font-bold text-sm border border-emerald-500/20">
                  Rating: {labelResult.health_rating || 'B+'}
                </div>
              </div>

              {labelResult.warnings && labelResult.warnings.length > 0 && (
                <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-1.5 text-xs text-amber-300">
                  <div className="flex items-center space-x-1.5 font-bold">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <span>Ingredient Warnings</span>
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-amber-200/90 pl-1">
                    {labelResult.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {labelResult.positive_points && labelResult.positive_points.length > 0 && (
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-1.5 text-xs text-emerald-300">
                  <div className="flex items-center space-x-1.5 font-bold">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span>Health Highlights</span>
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-emerald-200/90 pl-1">
                    {labelResult.positive_points.map((p, idx) => (
                      <li key={idx}>{p}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start space-x-2 text-red-400 text-xs">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
