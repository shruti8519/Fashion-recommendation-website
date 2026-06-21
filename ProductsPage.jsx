import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import TopNav from "../components/TopNav";
import ProductCard from "../components/ProductCard";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

const PRICE_MAX_OPTIONS = [
  { value: 2000, label: "Up to ₹2,000" },
  { value: 3500, label: "Up to ₹3,500" },
  { value: 5000, label: "Up to ₹5,000" },
  { value: 999999, label: "Any price" },
];

function Spinner() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16" role="status" aria-live="polite">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      <p className="text-sm text-slate-500">Loading products…</p>
    </div>
  );
}

export default function ProductsPage() {
  const { session } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState([]);
  const [brandOptions, setBrandOptions] = useState([]);

  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const [category, setCategory] = useState(() => searchParams.get("category") || "");
  const [brand, setBrand] = useState("");
  const [sort, setSort] = useState("popularity");
  const [minRating, setMinRating] = useState(0);
  const [minPrice, setMinPrice] = useState(0);
  const [maxPrice, setMaxPrice] = useState(5000);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Debounce search text only; empty query applies immediately.
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setDebouncedQuery("");
      return;
    }
    const t = window.setTimeout(() => setDebouncedQuery(query), 400);
    return () => window.clearTimeout(t);
  }, [query]);

  useEffect(() => {
    setCategory(searchParams.get("category") || "");
  }, [searchParams]);

  const setCategoryFromUi = useCallback(
    (value) => {
      setCategory(value);
      const next = new URLSearchParams(searchParams);
      if (value) next.set("category", value);
      else next.delete("category");
      setSearchParams(next, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.products({
        query: debouncedQuery.trim(),
        category,
        brand,
        sort,
        min_rating: minRating,
        min_price: minPrice,
        max_price: maxPrice,
        limit: 100,
      });
      setProducts(res.items || []);
      setTotal(typeof res.total === "number" ? res.total : (res.items || []).length);
    } catch (e) {
      const msg = e?.message || "Failed to load products. Check that the API is running.";
      setError(msg);
      setProducts([]);
      setTotal(0);
      toast.error("Could not load products");
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, category, brand, sort, minRating, minPrice, maxPrice]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  useEffect(() => {
    api.categories().then((res) => setCategories(res.items || [])).catch(() => {});
    api.brands().then((res) => setBrandOptions(res.items || [])).catch(() => {});
  }, []);

  const applySearchNow = () => {
    setDebouncedQuery(query);
  };

  const clearFilters = useCallback(() => {
    setQuery("");
    setDebouncedQuery("");
    setCategory("");
    setBrand("");
    setSort("popularity");
    setMinRating(0);
    setMinPrice(0);
    setMaxPrice(5000);
    const next = new URLSearchParams(searchParams);
    next.delete("category");
    setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams]);

  const activeFiltersCount = useMemo(() => {
    let n = 0;
    if (debouncedQuery.trim()) n += 1;
    if (category) n += 1;
    if (brand) n += 1;
    if (minRating > 0) n += 1;
    if (minPrice > 0) n += 1;
    if (maxPrice < 999999) n += 1;
    if (sort !== "popularity") n += 1;
    return n;
  }, [debouncedQuery, category, brand, minRating, minPrice, maxPrice, sort]);

  const empty = !loading && !error && products.length === 0;

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="mx-auto max-w-7xl px-4 py-6 sm:py-8 md:px-6 lg:px-8">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">All Products</h1>
            <p className="mt-1 text-sm text-slate-500">
              {loading ? "Updating…" : `${total} product${total === 1 ? "" : "s"} match your filters`}
            </p>
          </div>
          {activeFiltersCount > 0 && (
            <button
              type="button"
              onClick={clearFilters}
              className="self-start rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 sm:self-auto"
            >
              Clear filters ({activeFiltersCount})
            </button>
          )}
        </div>

        <div className="mb-8 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            <div className="min-w-0 sm:col-span-2 xl:col-span-2">
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Search</label>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none ring-brand-500/30 transition focus:border-brand-500 focus:ring-2"
                placeholder="Name, brand, or category…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    applySearchNow();
                  }
                }}
              />
            </div>
            <div className="min-w-0">
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Category</label>
              <select
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                value={category}
                onChange={(e) => setCategoryFromUi(e.target.value)}
              >
                <option value="">All categories</option>
                {categories.map((x) => (
                  <option key={x.name} value={x.name}>
                    {x.name} ({x.count})
                  </option>
                ))}
              </select>
            </div>
            <div className="min-w-0">
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Brand</label>
              <select
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
              >
                <option value="">All brands</option>
                {brandOptions.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
            </div>
            <div className="min-w-0">
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Sort</label>
              <select
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                value={sort}
                onChange={(e) => setSort(e.target.value)}
              >
                <option value="popularity">Popularity</option>
                <option value="low_to_high">Price: Low → High</option>
                <option value="high_to_low">Price: High → Low</option>
                <option value="newest">Newest</option>
              </select>
            </div>
            <div className="min-w-0">
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Min rating</label>
              <select
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                value={minRating}
                onChange={(e) => setMinRating(Number(e.target.value))}
              >
                <option value={0}>All ratings</option>
                <option value={3}>3+ stars</option>
                <option value={4}>4+ stars</option>
                <option value={4.5}>4.5+ stars</option>
              </select>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="min-w-0">
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Min price (₹)</label>
              <input
                type="number"
                min={0}
                step={100}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                value={minPrice || ""}
                placeholder="0"
                onChange={(e) => setMinPrice(Math.max(0, Number(e.target.value) || 0))}
              />
            </div>
            <div className="min-w-0">
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Max price</label>
              <select
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                value={maxPrice}
                onChange={(e) => setMaxPrice(Number(e.target.value))}
              >
                {PRICE_MAX_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-2">
              <button
                type="button"
                onClick={applySearchNow}
                className="rounded-lg bg-brand-500 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
              >
                Search now
              </button>
              <button
                type="button"
                onClick={() => loadProducts()}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div
            className="mb-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
            role="alert"
          >
            <p className="font-medium">Something went wrong</p>
            <p className="mt-1 text-rose-700">{error}</p>
          </div>
        )}

        {loading && <Spinner />}

        {empty && (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white px-6 py-14 text-center">
            <p className="text-lg font-medium text-slate-800">No products found</p>
            <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
              Try a different search term, clear a filter, or widen your price range.
            </p>
            <button
              type="button"
              onClick={clearFilters}
              className="mt-6 rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-600"
            >
              Reset all filters
            </button>
          </div>
        )}

        {!loading && !empty && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((item) => (
              <ProductCard
                key={item.id}
                product={item}
                onAddToCart={async (productId) => {
                  if (!session?.user?.id) {
                    toast.error("Please login first");
                    return;
                  }
                  await api.addToCart({ user_id: session.user.id, product_id: productId, quantity: 1 });
                  toast.success("Added to cart");
                }}
                onWishlist={async (productId) => {
                  if (!session?.user?.id) {
                    toast.error("Please login first");
                    return;
                  }
                  await api.saveItem({ user_id: session.user.id, item_id: productId });
                  toast.success("Added to wishlist");
                }}
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
