"use client";

import { useLanguage } from "../context/LanguageContext";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { Search, ShieldCheck, ExternalLink, ChevronLeft } from "lucide-react";
import Link from "next/link";

export default function OptOutPage() {
    const { t } = useLanguage();

    return (
        <main className="flex min-h-screen flex-col items-center relative overflow-hidden bg-background selection:bg-blue-500/30">
            {/* Dynamic Background Elements */}
            <div className="absolute inset-0 bg-grid-white/5 bg-[size:40px_40px] pointer-events-none" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background pointer-events-none" />

            {/* Navigation */}
            <header className="w-full max-w-7xl flex justify-between items-center px-8 py-8 z-50">
                <Link href="/" className="flex items-center gap-3 group cursor-pointer">
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-2xl transition-transform group-hover:scale-110">
                        <Search className="text-white w-5 h-5" strokeWidth={3} />
                    </div>
                    <span className="text-xl font-black tracking-tighter text-white uppercase italic">
                        {t.common.appName}
                    </span>
                </Link>
                <LanguageSwitcher />
            </header>

            <div className="w-full max-w-xl px-8 z-10 mt-12 mb-24">
                <div className="glass-panel p-8 md:p-12 rounded-[2.5rem] border-white/5 shadow-2xl">
                    <div className="w-16 h-16 rounded-[1.5rem] bg-zinc-900 border border-white/5 flex items-center justify-center text-blue-500 mb-8 mx-auto shadow-2xl">
                        <ShieldCheck size={32} />
                    </div>

                    <h1 className="text-4xl font-black tracking-tighter text-white mb-6 text-center uppercase italic">
                        {t.optOut.title}
                    </h1>
                    <p className="text-zinc-500 text-center font-medium leading-relaxed mb-12">
                        {t.optOut.description}
                    </p>

                    <div className="flex justify-center mb-8">
                        <a
                            href="https://mametarovv.booth.pm/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black tracking-widest uppercase py-5 px-6 rounded-2xl transition-all shadow-xl shadow-blue-500/20 active:scale-95 flex items-center justify-center gap-3 text-center"
                        >
                            <ExternalLink size={18} strokeWidth={3} className="shrink-0" />
                            <span className="text-sm md:text-base">{t.optOut.buttonText}</span>
                        </a>
                    </div>

                    <div className="mt-12 text-center">
                        <Link href="/" className="text-xs font-black text-zinc-600 hover:text-white uppercase tracking-widest transition-colors flex items-center justify-center gap-2">
                            <ChevronLeft size={16} strokeWidth={3} />
                            {t.common.backToHome}
                        </Link>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="w-full py-12 px-8 border-t border-white/5 bg-zinc-950/50 z-10 backdrop-blur-3xl mt-auto">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8 text-[10px] font-bold text-zinc-600 tracking-[0.3em] uppercase">
                    &copy; 2026 豆々庵. BoothPic. ALL RIGHTS RESERVED.
                    <div className="flex gap-6">
                        <Link href="/privacy" className="text-zinc-500 hover:text-white transition-colors">{t.home.footer.privacy}</Link>
                        <Link href="/terms" className="text-zinc-500 hover:text-white transition-colors">{t.home.footer.terms}</Link>
                    </div>
                </div>
            </footer>
        </main>
    );
}
