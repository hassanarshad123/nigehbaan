export default function LegalLoading() {
  return (
    <div className="min-h-screen bg-[#0F172A] pt-16 px-4">
      <div className="mx-auto max-w-screen-xl">
        {/* Title */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="skeleton h-8 w-48 mb-2" />
            <div className="skeleton h-4 w-96" />
          </div>
          <div className="skeleton h-9 w-36 rounded-md" />
        </div>

        {/* Filter panel */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 mb-6">
          <div className="grid grid-cols-2 gap-3 sm:flex sm:flex-wrap sm:gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i}>
                <div className="skeleton h-3 w-12 mb-1" />
                <div className="skeleton h-9 w-full sm:w-40 rounded-md" />
              </div>
            ))}
          </div>
        </div>

        {/* Table skeleton */}
        <div className="hidden sm:block rounded-lg border border-[#334155] bg-[#1E293B] overflow-hidden">
          <div className="skeleton h-11 w-full" />
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex gap-4 px-4 py-3 border-b border-[#334155]/30">
              <div className="skeleton h-5 w-32 rounded" />
              <div className="skeleton h-5 w-24 rounded" />
              <div className="skeleton h-5 w-20 rounded" />
              <div className="skeleton h-5 w-16 rounded" />
              <div className="skeleton h-5 w-20 rounded-full" />
              <div className="skeleton h-5 w-16 rounded" />
            </div>
          ))}
        </div>

        {/* Mobile card skeleton */}
        <div className="sm:hidden space-y-2">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="skeleton h-28 rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
