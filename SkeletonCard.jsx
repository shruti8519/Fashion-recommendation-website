export default function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
      <div className="mb-3 h-40 rounded-xl bg-slate-300/70 dark:bg-slate-700/70" />
      <div className="mb-2 h-4 w-2/3 rounded bg-slate-300/70 dark:bg-slate-700/70" />
      <div className="h-4 w-1/2 rounded bg-slate-300/70 dark:bg-slate-700/70" />
    </div>
  );
}
