export default function ReportTrackLoading() {
  return (
    <div className="min-h-screen bg-[#0F172A] pt-24 px-4">
      <div className="mx-auto max-w-lg">
        {/* Back link */}
        <div className="mb-6">
          <div className="skeleton h-4 w-28" />
        </div>

        {/* Title */}
        <div className="text-center mb-8">
          <div className="skeleton h-10 w-10 rounded-full mx-auto mb-3" />
          <div className="skeleton h-8 w-52 mx-auto mb-2" />
          <div className="skeleton h-4 w-72 mx-auto" />
        </div>

        {/* Search form skeleton */}
        <div className="flex gap-2 mb-8">
          <div className="skeleton h-11 flex-1 rounded-md" />
          <div className="skeleton h-11 w-24 rounded-md" />
        </div>
      </div>
    </div>
  );
}
