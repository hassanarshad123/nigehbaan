export default function ScrapersLoading() {
  return (
    <div className="min-h-screen bg-[#0F172A] pt-16 px-4">
      <div className="mx-auto max-w-screen-2xl">
        {/* Title */}
        <div className="mb-6">
          <div className="skeleton h-8 w-48 mb-2" />
          <div className="skeleton h-4 w-80" />
        </div>

        {/* KPI cards */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-24 rounded-lg" />
          ))}
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 mb-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-8 w-20 rounded-md" />
          ))}
        </div>

        {/* Table skeleton */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] overflow-hidden">
          <div className="skeleton h-10 w-full" />
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="flex gap-4 px-4 py-3 border-b border-[#334155]/30">
              <div className="skeleton h-5 w-20 rounded-full" />
              <div className="skeleton h-5 flex-1 rounded" />
              <div className="skeleton h-5 w-24 rounded" />
              <div className="skeleton h-5 w-16 rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
