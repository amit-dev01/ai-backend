import React, { useRef, useState, useEffect } from 'react';

export default function ScaledDashboard({ children }) {
  const containerRef = useRef(null);
  const innerRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [height, setHeight] = useState(0);

  useEffect(() => {
    if (!containerRef.current || !innerRef.current) return;

    const updateScale = () => {
      if (!containerRef.current || !innerRef.current) return;
      const containerWidth = containerRef.current.clientWidth;
      const designWidth = 896; // Design width of dashboard mockup
      const currentScale = Math.min(containerWidth / designWidth, 1);
      setScale(currentScale);
      setHeight(innerRef.current.offsetHeight * currentScale);
    };

    const observer = new ResizeObserver(updateScale);
    observer.observe(containerRef.current);
    
    // Initial run
    updateScale();

    // Window resize listener as fallback
    window.addEventListener('resize', updateScale);

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', updateScale);
    };
  }, []);

  return (
    <div 
      ref={containerRef} 
      className="w-full relative overflow-hidden" 
      style={{ height: height ? `${height}px` : 'auto' }}
    >
      <div 
        ref={innerRef}
        className="absolute top-0 left-0"
        style={{
          width: '896px',
          transform: `scale(${scale})`,
          transformOrigin: 'top left',
        }}
      >
        {children}
      </div>
    </div>
  );
}
