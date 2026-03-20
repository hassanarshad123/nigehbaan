export default function HomeLoading() {
  return (
    <div className="relative h-screen w-screen overflow-hidden bg-[#0F172A]">
      {/* Map placeholder with pulse */}
      <div className="absolute inset-0 skeleton opacity-30" />

      {/* Header skeleton */}
      <div className="absolute top-0 left-0 right-0 z-10 h-12 bg-glass border-b border-[#334155]/50">
        <div className="mx-auto flex h-12 max-w-screen-2xl items-center justify-between px-4">
          <div className="skeleton h-5 w-28 rounded" />
          <div className="hidden md:flex items-center gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="skeleton h-6 w-16 rounded" />
            ))}
          </div>
          <div className="skeleton h-8 w-8 rounded" />
        </div>
      </div>

      {/* Search bar skeleton */}
      <div className="absolute top-16 left-1/2 -translate-x-1/2 z-10 w-80">
        <div className="skeleton h-10 rounded-lg" />
      </div>

      {/* Layer controls skeleton */}
      <div className="absolute top-16 right-2 z-10">
        <div className="skeleton h-10 w-10 rounded-lg" />
      </div>

      {/* Bottom controls skeleton */}
      <div className="absolute bottom-4 left-2 right-2 z-10">
        <div className="flex flex-col items-center gap-2">
          <div className="skeleton h-12 w-96 max-w-full rounded-lg" />
          <div className="skeleton h-16 w-64 rounded-lg self-start" />
        </div>
      </div>

      {/* Center loading indicator */}
      <div className="absolute inset-0 flex items-center justify-center z-10">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 rounded-full border-2 border-[#06B6D4]/30 border-t-[#06B6D4] animate-spin" />
          <p className="text-sm text-[#94A3B8]">Loading map data...</p>
        </div>
      </div>
    </div>
  );
}
