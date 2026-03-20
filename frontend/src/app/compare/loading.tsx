export default function CompareLoading() {
  return (
    <div className="min-h-screen bg-[#0F172A] pt-16 px-4">
      <div className="mx-auto max-w-screen-xl">
        {/* Title */}
        <div className="mb-6">
          <div className="skeleton h-8 w-56 mb-2" />
          <div className="skeleton h-4 w-80" />
        </div>

        {/* Selector panel */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 mb-6">
          <div className="skeleton h-3 w-40 mb-2" />
          <div className="skeleton h-10 w-full rounded-md" />
        </div>

        {/* Empty area placeholder */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="skeleton h-10 w-10 rounded-full" />
            <div className="skeleton h-4 w-48" />
            <div className="skeleton h-3 w-72" />
          </div>
        </div>
      </div>
    </div>
  );
}
