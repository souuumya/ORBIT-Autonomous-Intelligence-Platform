export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-100">
      <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-8 py-6">
        <h2 className="text-2xl font-semibold">Not found</h2>
        <p className="mt-2 text-slate-400">The requested page could not be found.</p>
      </div>
    </div>
  );
}
