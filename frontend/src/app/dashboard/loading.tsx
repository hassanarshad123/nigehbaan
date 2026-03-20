export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-[#0F172A] pt-16 px-4">
      <div className="mx-auto max-w-screen-2xl">
        {/* Title skeleton */}
        <div className="mb-6">
          <div className="skeleton h-8 w-64 mb-2" />
          <div className="skeleton h-4 w-96" />
        </div>

        {/* Filter skeleton */}
        <div className="skeleton h-20 w-full rounded-lg mb-6" />

        {/* KPI cards skeleton */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-28 rounded-lg" />
          ))}
        </div>

        {/* Charts skeleton */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-72 rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
