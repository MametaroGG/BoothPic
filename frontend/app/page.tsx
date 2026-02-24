"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import ImageUploader from "./components/ImageUploader";
import ProductCard from "./components/ProductCard";
import LanguageSwitcher from "./components/LanguageSwitcher";
import Link from "next/link";
import axios from "axios";
import { Loader2, Search, Zap, Globe, Shield, Crop as CropIcon, Check, X } from "lucide-react";
import { useLanguage } from "./context/LanguageContext";
import ReactCrop, { type Crop, type PixelCrop, centerCrop, makeAspectCrop } from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css";
import getCroppedImg from "./utils/cropImage";

// Helper for initial crop
function centerAspectCrop(mediaWidth: number, mediaHeight: number, aspect: number) {
  return centerCrop(
    makeAspectCrop({ unit: "%", width: 90 }, aspect, mediaWidth, mediaHeight),
    mediaWidth, mediaHeight
  )
}


interface SearchResultItem {
  id: string;
  score: number;
  payload: {
    title: string;
    price: number;
    thumbnailUrl: string;
    shopName: string;
    boothUrl: string;
  };
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { t } = useLanguage();

  // Cropping State
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<Crop>();
  const [isCropping, setIsCropping] = useState(false);
  const [imgRef, setImgRef] = useState<HTMLImageElement | null>(null);
  const [zoom, setZoom] = useState(1);

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height } = e.currentTarget;
    const initialCrop = centerAspectCrop(width, height, 1);
    setCrop(initialCrop);
    setCompletedCrop(initialCrop);
    setImgRef(e.currentTarget); // Ensure imgRef is set explicitly here
  }

  const handleImageSelect = async (file: File) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      setImageSrc(reader.result as string);
      setIsCropping(true);
      setError(null);
      setResults([]);
    });
    reader.readAsDataURL(file);
  };


  // Zoom via scroll
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isCropping) return;

    const container = scrollContainerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const delta = -Math.sign(e.deltaY);
      const step = 0.1;

      setZoom((prev) => {
        const newZoom = prev + (delta * step);
        return Math.min(Math.max(newZoom, 0.1), 5.0);
      });
    };

    container.addEventListener("wheel", handleWheel, { passive: false });
    return () => {
      container.removeEventListener("wheel", handleWheel);
    };
  }, [isCropping]);

  const handleSearch = async () => {
    if (!imageSrc || !completedCrop || !imgRef) return;

    setLoading(true);
    setIsCropping(false);

    try {
      const truePixelCrop = {
        x: (completedCrop.x / 100) * imgRef.naturalWidth,
        y: (completedCrop.y / 100) * imgRef.naturalHeight,
        width: (completedCrop.width / 100) * imgRef.naturalWidth,
        height: (completedCrop.height / 100) * imgRef.naturalHeight,
      };

      const croppedImageBlob = await getCroppedImg(imageSrc, truePixelCrop);
      if (!croppedImageBlob) {
        throw new Error("Failed to crop image");
      }

      const formData = new FormData();
      formData.append("file", croppedImageBlob, "cropped_image.jpg");

      const response = await axios.post("/api/search", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResults(response.data.results || []);
    } catch (err) {
      console.error(err);
      setError(t.home.failedSearch);
    } finally {
      setLoading(false);
    }
  };

  const cancelCrop = () => {
    setIsCropping(false);
    setImageSrc(null);
    setZoom(1);
  };

  return (
    <main className="flex min-h-screen flex-col items-center relative overflow-hidden bg-background selection:bg-blue-500/30">
      {/* Dynamic Background Elements */}
      <div className="absolute inset-0 bg-grid-white/5 bg-[size:40px_40px] pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background pointer-events-none" />
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/5 rounded-full blur-[120px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Cropping Modal Overlay */}
      {isCropping && imageSrc && (
        <div className="fixed inset-0 z-[100] bg-black/90 backdrop-blur-md flex flex-col items-center justify-center p-4">
          <style jsx global>{`
                /* Google Lens Style Crop Box Overrides */
                .ReactCrop__crop-selection {
                   border: 2px dashed rgba(255, 255, 255, 0.8) !important;
                   box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.6);
                   background-image: none !important;
                }
                /* Price Variation Display Tasks */
                /* - [x] 商品価格のバリエーション表示の修正 */
                /* - [x] 「〜」サフィックスが表示されない原因の調査 (スクレイパーのプロセス競合・古いコードの実行が原因) */
                /* - [x] 「アズキ」モデルのスクレイピングデータ確認 (JSON-LDでの価格変動を確認) */
                /* - [x] バリエーションがある場合に「〜」を付与する修正の適用 (全角チルダへの統一) */
                /* - [x] 修正内容の反映と再起動 (metadata.jsonlの修正およびプロセスの再起動) */

                /* General Handle Reset */
                .ReactCrop__drag-handle {
                    width: 0; height: 0;
                    margin: 0;
                    border: none !important;
                    background-color: transparent !important;
                    border-radius: 0 !important;
                    opacity: 1 !important;
                }

                /* --- CORNERS (L-Shapes) --- */
                /* Common style for corners to create the L-shape look */
                .ReactCrop__drag-handle::after {
                    content: '';
                    position: absolute;
                    background-color: white;
                    display: block;
                }

                /* NW Corner */
                .ReactCrop__drag-handle.ord-nw {
                    width: 25px !important; height: 25px !important;
                    top: -4px !important; left: -4px !important;
                    border-top: 5px solid white !important;
                    border-left: 5px solid white !important;
                    border-top-left-radius: 4px;
                }
                
                /* NE Corner */
                .ReactCrop__drag-handle.ord-ne {
                    width: 25px !important; height: 25px !important;
                    top: -4px !important; right: -4px !important;
                    border-top: 5px solid white !important;
                    border-right: 5px solid white !important;
                    border-top-right-radius: 4px;
                }

                /* SW Corner */
                .ReactCrop__drag-handle.ord-sw {
                    width: 25px !important; height: 25px !important;
                    bottom: -4px !important; left: -4px !important;
                    border-bottom: 5px solid white !important;
                    border-left: 5px solid white !important;
                    border-bottom-left-radius: 4px;
                }

                /* SE Corner */
                .ReactCrop__drag-handle.ord-se {
                    width: 25px !important; height: 25px !important;
                    bottom: -4px !important; right: -4px !important;
                    border-bottom: 5px solid white !important;
                    border-right: 5px solid white !important;
                    border-bottom-right-radius: 4px;
                }

                /* --- EDGE HANDLES (Pills) --- */
                
                /* Top & Bottom (Horizontal Pills) */
                .ReactCrop__drag-handle.ord-n,
                .ReactCrop__drag-handle.ord-s {
                    width: 40px !important; height: 6px !important;
                    background-color: white !important;
                    border-radius: 3px !important;
                    left: 50% !important;
                    transform: translateX(-50%);
                    top: -3px !important; /* Center on line */
                }
                .ReactCrop__drag-handle.ord-s {
                    top: auto !important;
                    bottom: -3px !important;
                }

                /* Left & Right (Vertical Pills) */
                .ReactCrop__drag-handle.ord-w,
                .ReactCrop__drag-handle.ord-e {
                    width: 6px !important; height: 40px !important;
                    background-color: white !important;
                    border-radius: 3px !important;
                    top: 50% !important;
                    transform: translateY(-50%);
                    left: -3px !important;
                }
                .ReactCrop__drag-handle.ord-e {
                    left: auto !important;
                    right: -3px !important;
                }
            
            `}</style>

          <div
            ref={scrollContainerRef}
            className="relative w-full max-w-5xl h-[70vh] flex items-center justify-center bg-zinc-900/50 rounded-xl overflow-auto border border-white/10"
          >
            <div style={{ position: "relative", display: "inline-block" }}>

              <ReactCrop
                crop={crop}
                onChange={(_, percentCrop) => setCrop(percentCrop)}
                onComplete={(_, percentCrop) => setCompletedCrop(percentCrop)}
              >
                <img
                  src={imageSrc}
                  alt="Crop target"
                  onLoad={onImageLoad}
                  ref={(r) => setImgRef(r)}
                  style={{
                    height: `${65 * zoom}vh`,
                    maxWidth: 'none',
                    width: 'auto',
                    transition: 'height 0.1s ease-out',
                    display: 'block' // Ensure no bottom gap
                  }}
                  crossOrigin="anonymous" // Helpful for some browser restrictions
                />
              </ReactCrop>


            </div>
          </div>

          <div className="flex gap-4 mt-8">
            <button
              onClick={cancelCrop}
              className="flex items-center gap-2 px-6 py-3 rounded-full bg-zinc-800 hover:bg-zinc-700 text-white font-bold transition-all border border-white/5"
            >
              <X size={20} />
              {t.common?.cancel || "Cancel"}
            </button>
            <button
              onClick={handleSearch}
              className="flex items-center gap-2 px-8 py-3 rounded-full bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-500/25 transition-all transform hover:scale-105"
            >
              <Search size={20} />
              {completedCrop && (completedCrop.width < 90 || completedCrop.height < 90) ? "この範囲で検索" : "画像全体で検索"}
            </button>
          </div>
          <p className="mt-4 text-zinc-400 text-sm font-medium">ドラッグで移動、スクロールで拡大縮小</p>

          {/* DEBUG INFO */}
          <div className="absolute top-4 left-4 p-4 bg-black/80 text-white text-xs font-mono rounded pointer-events-none z-[100]">
            <p>Debug Info:</p>
            <p>ImgRef: {imgRef ? `Loaded (${imgRef.naturalWidth}x${imgRef.naturalHeight})` : 'Null'}</p>
          </div>
        </div>
      )}

      {/* Navigation */}
      <header className="w-full max-w-7xl flex justify-between items-center px-8 py-8 z-50">
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-2xl shadow-blue-500/30 transition-transform group-hover:scale-110 group-active:scale-95">
            <Search className="text-white w-5 h-5" strokeWidth={3} />
          </div>
          <span className="text-xl font-black tracking-tighter text-white uppercase italic">
            {t.common.appName}
          </span>
        </div>
        <nav className="hidden md:flex items-center gap-1 p-1.5 bg-zinc-900/50 backdrop-blur-3xl rounded-2xl border border-white/5 shadow-2xl">
          <a href="https://mametarovv.booth.pm/items/8024907" target="_blank" rel="noopener noreferrer" className="text-xs font-bold text-zinc-400 hover:text-white px-4 py-2.5 rounded-xl transition-all hover:bg-white/5 flex items-center gap-1.5">
            <span className="text-pink-500 text-sm">♥</span> {t.common.support}
          </a>
          <a href="/opt-out" className="text-xs font-bold text-zinc-400 hover:text-white px-4 py-2.5 rounded-xl transition-all hover:bg-white/5">{t.common.optOut}</a>
          <div className="w-[1px] h-4 bg-white/10 mx-2" />
          <LanguageSwitcher />
        </nav>
      </header>

      {/* Hero Section */}
      <section className="w-full max-w-5xl mt-24 mb-24 text-center px-6 z-10 relative">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 mb-8 animate-in fade-in slide-in-from-top-4 duration-1000">
          <Zap size={14} className="text-blue-400 fill-blue-400" />
          <span className="text-[10px] font-black tracking-[0.2em] text-blue-400 uppercase">Version 1.0</span>
        </div>

        <h2 className="text-6xl md:text-8xl font-black tracking-[calc(-0.05em)] mb-8 leading-[0.9] text-white">
          {t.home.titlePrimary} <span className="text-transparent bg-clip-text bg-gradient-to-b from-blue-400 to-indigo-600">{t.home.titleAccent}</span>{t.home.titleSecondary}
        </h2>
        <p className="text-lg md:text-xl text-zinc-500 mb-16 max-w-2xl mx-auto leading-relaxed font-medium">
          {t.home.subtitle}
        </p>



        <div className="relative animate-in fade-in zoom-in duration-1000 delay-300 mt-8">
          <div className="absolute -inset-4 bg-blue-500/5 blur-3xl rounded-[3rem] pointer-events-none" />
          <ImageUploader onImageSelect={handleImageSelect} />
        </div>
      </section>

      {/* Main Content Area */}
      <div className="w-full max-w-7xl px-8 pb-32 z-10">
        {loading && (
          <div className="flex flex-col items-center justify-center py-24 animate-in fade-in duration-500">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500/20 blur-2xl rounded-full" />
              <Loader2 className="animate-spin text-blue-500 relative" size={64} strokeWidth={1.5} />
            </div>
            <p className="mt-8 text-sm font-black tracking-widest text-zinc-400 uppercase">{t.home.analyzing}</p>
          </div>
        )}

        {error && (
          <div className="max-w-md mx-auto bg-red-500/10 border border-red-500/20 p-6 rounded-3xl backdrop-blur-xl flex items-center gap-4 animate-in shake duration-500">
            <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center text-red-500 shrink-0">
              <Shield size={20} />
            </div>
            <p className="text-sm font-bold text-red-300">{error}</p>
          </div>
        )}

        {results.length > 0 && (
          <div className="space-y-12">

            {/* Search Query Visualization */}
            {imageSrc && completedCrop && (
              <div className="flex flex-col items-center animate-in fade-in slide-in-from-top-4 duration-700">
                <div className="relative rounded-xl overflow-hidden shadow-2xl border border-white/10">
                  {/* Backend and Frontend Tasks */}
                  {/* - [x] バックエンドの再起動とシード処理の実行 */}
                  {/* - [x] フロントエンドでの最終確認とUI微調整 */}
                  {/* Background Image */}
                  <img
                    src={imageSrc}
                    alt="Query Context"
                    className="max-h-[300px] w-auto"
                  />
                  {/* Highlight Outline */}
                  <div
                    className="absolute border-2 border-white box-content shadow-[0_0_0_9999px_rgba(0,0,0,0.6)]"
                    style={{
                      left: `${completedCrop.x}%`,
                      top: `${completedCrop.y}%`,
                      width: `${completedCrop.width}%`,
                      height: `${completedCrop.height}%`,
                    }}
                  />
                </div>
                <p className="mt-4 text-xs font-bold text-zinc-500 tracking-widest uppercase">検索対象エリア</p>
              </div>
            )}

            <div className="flex items-center gap-4">
              <h3 className="text-2xl font-black tracking-tighter text-white uppercase italic">{t.home.searchResults}</h3>
              <div className="h-[1px] flex-1 bg-white/5" />
              <span className="text-xs font-black text-zinc-500 tracking-widest uppercase">{results.length} {t.home.matches}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 animate-in slide-in-from-bottom-12 duration-1000">
              {results.map((item) => (
                <ProductCard
                  key={item.id}
                  title={item.payload?.title || "Unknown Item"}
                  price={item.payload?.price || 0}
                  thumbnailUrl={item.payload?.thumbnailUrl || "/placeholder.png"}
                  shopName={item.payload?.shopName || "Unknown Shop"}
                  boothUrl={item.payload?.boothUrl || "#"}
                  score={item.score}
                />
              ))}
            </div>
          </div>
        )}

        {!loading && results.length === 0 && !error && (
          <div className="pt-24 border-t border-white/5 grid md:grid-cols-3 gap-12">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center text-blue-500 border border-white/5 shadow-xl">
                <Zap size={24} />
              </div>
              <h4 className="text-lg font-bold text-white tracking-tight">{t.home.features.analysis.title}</h4>
              <p className="text-sm text-zinc-500 leading-relaxed font-medium">{t.home.features.analysis.desc}</p>
            </div>
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center text-indigo-500 border border-white/5 shadow-xl">
                <Globe size={24} />
              </div>
              <h4 className="text-lg font-bold text-white tracking-tight">{t.home.features.search.title}</h4>
              <p className="text-sm text-zinc-500 leading-relaxed font-medium">{t.home.features.search.desc}</p>
            </div>
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center text-purple-500 border border-white/5 shadow-xl">
                <Shield size={24} />
              </div>
              <h4 className="text-lg font-bold text-white tracking-tight">{t.home.features.secure.title}</h4>
              <p className="text-sm text-zinc-500 leading-relaxed font-medium">{t.home.features.secure.desc}</p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="w-full py-12 px-8 border-t border-white/5 bg-zinc-950/50 z-10 backdrop-blur-3xl">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-blue-500 flex items-center justify-center">
              <Search className="text-white w-3 h-3" strokeWidth={4} />
            </div>
            <span className="text-sm font-black tracking-tighter text-white uppercase italic">{t.common.appName}</span>
          </div>
          <div className="text-[10px] font-bold text-zinc-600 tracking-[0.3em] uppercase">
            &copy; 2026 豆々庵. BOOTH-LENS. ALL RIGHTS RESERVED.
          </div>
          <div className="flex gap-6">
            <Link href="/privacy" className="text-xs font-bold text-zinc-500 hover:text-white transition-colors">{t.home.footer.privacy}</Link>
            <Link href="/terms" className="text-xs font-bold text-zinc-500 hover:text-white transition-colors">{t.home.footer.terms}</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
