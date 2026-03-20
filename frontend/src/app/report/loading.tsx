export default function ReportLoading() {
  return (
    <div className="min-h-screen bg-[#0F172A] pt-16 px-4">
      <div className="mx-auto max-w-screen-2xl">
        {/* Title */}
        <div className="mb-8 text-center">
          <div className="skeleton h-8 w-48 mx-auto mb-2" />
          <div className="skeleton h-4 w-80 mx-auto" />
        </div>

        {/* Safety banner skeleton */}
        <div className="mx-auto max-w-2xl mb-8">
          <div className="skeleton h-20 rounded-lg" />
        </div>

        {/* Privacy line */}
        <div className="mx-auto max-w-2xl mb-6">
          <div className="skeleton h-4 w-72" />
        </div>

        {/* Form area skeleton */}
        <div className="mx-auto max-w-2xl">
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6">
            {/* Step indicator */}
            <div className="flex justify-center gap-2 mb-6">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="skeleton h-2 w-12 rounded-full" />
              ))}
            </div>
            {/* Form fields */}
            <div className="space-y-4">
              <div className="skeleton h-10 w-full rounded-md" />
              <div className="skeleton h-10 w-full rounded-md" />
              <div className="skeleton h-24 w-full rounded-md" />
              <div className="skeleton h-10 w-32 rounded-md" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
