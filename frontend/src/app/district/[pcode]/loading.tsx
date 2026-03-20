export default function DistrictLoading() {
  return (
    <div className="min-h-screen bg-[#0F172A] pt-16 px-4">
      <div className="mx-auto max-w-screen-xl">
        {/* Back link */}
        <div className="skeleton h-5 w-28 mb-6" />

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <div className="skeleton h-8 w-48 mb-2" />
            <div className="skeleton h-6 w-32" />
          </div>
          <div className="skeleton h-36 w-36 rounded-full" />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 mb-8">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="skeleton h-20 rounded-lg" />
          ))}
        </div>

        {/* Map & Timeline */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="skeleton h-64 rounded-lg" />
          <div className="skeleton h-64 rounded-lg" />
        </div>
      </div>
    </div>
  );
}
