"use client";

import { useState } from "react";
import { Coffee, Globe, Shield, X, Menu } from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";
import Link from "next/link";

interface MobileMenuProps {
    t: any;
}

export default function MobileMenu({ t }: MobileMenuProps) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="md:hidden flex items-center">
            <button
                onClick={() => setIsOpen(true)}
                className="p-2 text-zinc-400 hover:text-white transition-colors"
                aria-label="Open menu"
            >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect y="4" width="24" height="2" rx="1" fill="currentColor" />
                    <rect y="11" width="24" height="2" rx="1" fill="currentColor" />
                    <rect y="18" width="24" height="2" rx="1" fill="currentColor" />
                </svg>
            </button>

            {isOpen && (
                <div className="fixed inset-0 z-[200] bg-background/95 backdrop-blur-xl animate-in fade-in duration-300">
                    <div className="flex flex-col h-full p-8">
                        <div className="flex justify-between items-center mb-12">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                                    <span className="text-white text-xs font-black">B</span>
                                </div>
                                <span className="text-lg font-black tracking-tighter text-white uppercase italic">
                                    {t.common.appName}
                                </span>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2 text-zinc-400 hover:text-white transition-colors bg-zinc-900 rounded-full"
                            >
                                <X size={24} />
                            </button>
                        </div>

                        <nav className="flex flex-col gap-6">
                            <a
                                href="https://mametaro-vv.fanbox.cc/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-4 p-4 rounded-2xl bg-zinc-900/50 border border-white/5 text-lg font-bold text-zinc-300 hover:text-white transition-all active:scale-95"
                                onClick={() => setIsOpen(false)}
                            >
                                <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-500">
                                    <Coffee size={20} />
                                </div>
                                {t.common.support}
                            </a>

                            <Link
                                href="/opt-out"
                                className="flex items-center gap-4 p-4 rounded-2xl bg-zinc-900/50 border border-white/5 text-lg font-bold text-zinc-300 hover:text-white transition-all active:scale-95"
                                onClick={() => setIsOpen(false)}
                            >
                                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500">
                                    <Shield size={20} />
                                </div>
                                {t.common.optOut}
                            </Link>

                            <div className="mt-4 pt-8 border-t border-white/5">
                                <p className="text-xs font-black tracking-widest text-zinc-600 uppercase mb-4">Language / 言語</p>
                                <div className="bg-zinc-900/50 p-2 rounded-2xl border border-white/5 inline-block">
                                    <LanguageSwitcher />
                                </div>
                            </div>
                        </nav>

                        <div className="mt-auto text-center">
                            <p className="text-[10px] font-bold text-zinc-700 tracking-[0.3em] uppercase">
                                &copy; 2026 豆々庵. BoothPic.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
