import { useState, useEffect, useRef } from "react";

interface AudioVisualizerProps {
  isActive: boolean;
  barCount?: number;
  height?: number;
  variant?: "bars" | "waveform";
}

export function AudioVisualizer({
  isActive,
  barCount = 24,
  height = 40,
  variant = "bars",
}: AudioVisualizerProps) {
  const [levels, setLevels] = useState<number[]>(
    Array(barCount).fill(0)
  );
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isActive) {
      setLevels(Array(barCount).fill(0));
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      return;
    }

    let lastTime = 0;
    const animate = (time: number) => {
      if (time - lastTime > 60) {
        lastTime = time;
        setLevels((prev) =>
          prev.map((_, i) => {
            const center = barCount / 2;
            const distFromCenter = Math.abs(i - center) / center;
            const baseAmplitude = 1 - distFromCenter * 0.5;
            const noise = Math.random() * 0.6 + 0.2;
            const wave =
              Math.sin(time * 0.003 + i * 0.4) * 0.3 + 0.5;
            return Math.min(1, baseAmplitude * noise * wave);
          })
        );
      }
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [isActive, barCount]);

  if (variant === "waveform") {
    return (
      <div className="flex items-center gap-[1px]" style={{ height }}>
        {levels.map((level, i) => {
          const h = Math.max(2, level * height);
          return (
            <div
              key={i}
              className="rounded-full transition-all duration-75"
              style={{
                width: 2,
                height: h,
                backgroundColor: `rgba(39, 116, 174, ${0.4 + level * 0.6})`,
              }}
            />
          );
        })}
      </div>
    );
  }

  return (
    <div
      className="flex items-end gap-[2px]"
      style={{ height }}
    >
      {levels.map((level, i) => {
        const barHeight = Math.max(2, level * height);
        const intensity = level;
        return (
          <div
            key={i}
            className="rounded-t-sm transition-all duration-75"
            style={{
              width: Math.max(2, Math.floor(100 / barCount) - 1),
              height: barHeight,
              background: `linear-gradient(to top, #2774AE, ${
                intensity > 0.7
                  ? "#FFD100"
                  : intensity > 0.4
                  ? "#3a8fd4"
                  : "#2774AE"
              })`,
              opacity: isActive ? 0.5 + intensity * 0.5 : 0.15,
            }}
          />
        );
      })}
    </div>
  );
}
