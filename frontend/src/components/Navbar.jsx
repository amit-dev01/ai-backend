import React from 'react';
import Logo from './Logo';

export default function Navbar() {
  return (
    <nav className="animate-fade-down relative z-20 w-full bg-transparent">
      <div className="max-w-[1200px] mx-auto px-5 sm:px-8 lg:px-10 py-4 sm:py-5 flex items-center justify-between h-20">
        {/* Left: Logo + Wordmark */}
        <a href="/" className="flex items-center gap-3 text-gray-900">
          <Logo />
          <span className="font-sans font-bold text-xl tracking-tight">Aetheris</span>
        </a>

        {/* Right: CTA Buttons */}
        <div className="flex items-center gap-3">
          <a 
            href="/login/" 
            className="text-[13px] font-medium text-gray-700 hover:text-gray-900 px-3 py-2 transition-colors"
          >
            Sign in
          </a>
          <a 
            href="/signup/" 
            className="bg-gray-900 text-white text-[13px] font-medium px-4 sm:px-5 py-2 rounded-full hover:bg-gray-800 transition-all hover:scale-[1.02] shadow-sm text-center"
          >
            Get started
          </a>
        </div>
      </div>
    </nav>
  );
}
