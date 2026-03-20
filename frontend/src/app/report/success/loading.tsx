export default function ReportSuccessLoading() {
  return (
    <div className="min-h-screen bg-[#0F172A] pt-24 px-4">
      <div className="mx-auto max-w-lg text-center">
        {/* Icon */}
        <div className="mb-6 flex justify-center">
          <div className="skeleton h-20 w-20 rounded-full" />
        </div>

        {/* Title */}
        <div className="skeleton h-8 w-48 mx-auto mb-2" />
        <div className="skeleton h-4 w-72 mx-auto mb-6" />

        {/* Reference card */}
        <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 mb-8">
          <div className="skeleton h-3 w-28 mx-auto mb-2" />
          <div className="skeleton h-7 w-44 mx-auto mb-2" />
          <div className="skeleton h-3 w-52 mx-auto" />
        </div>

        {/* Actions */}
        <div className="flex justify-center gap-3">
          <div className="skeleton h-10 w-40 rounded-md" />
          <div className="skeleton h-10 w-36 rounded-md" />
        </div>
      </div>
    </div>
  );
}
