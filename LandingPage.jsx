import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import TopNav from "../components/TopNav";
import ProductCard from "../components/ProductCard";
import { api } from "../api";

export default function LandingPage() {
  const [featured, setFeatured] = useState([]);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    api.products({ limit: 8, sort: "popularity" }).then((res) => setFeatured(res.items || []));
    api.categories().then((res) => setCategories(res.items || []));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="bg-brand-500">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-14 text-white md:grid-cols-2 md:px-6">
          <div>
            <p className="mb-2 text-sm uppercase tracking-widest text-rose-100">New season arrivals</p>
            <h1 className="text-4xl font-bold leading-tight md:text-5xl">Shop Dresses, Makeup, Footwear & Accessories</h1>
            <p className="mt-4 max-w-lg text-brand-100">A modern marketplace inspired by premium shopping experiences with wishlist, cart, secure checkout, and personalized picks.</p>
            <div className="mt-6 flex gap-3">
              <Link to="/products" className="rounded-lg bg-white px-5 py-3 font-medium text-brand-500">Shop Now</Link>
              <Link to="/auth" className="rounded-lg border border-white px-5 py-3 font-medium">Login / Signup</Link>
            </div>
          </div>
          <img src="https://images.unsplash.com/photo-1483985988355-763728e1935b?w=900&auto=format&fit=crop&q=80" alt="Fashion banner" className="h-72 w-full rounded-2xl object-cover shadow-xl md:h-96" />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-10 md:px-6">
        <h2 className="mb-5 text-2xl font-semibold">Shop by Category</h2>
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          {categories.map((category) => (
            <Link key={category.name} to={`/products?category=${encodeURIComponent(category.name)}`} className="rounded-xl border border-slate-200 bg-white p-4 transition hover:border-brand-500">
              <p className="font-semibold text-slate-800">{category.name}</p>
              <p className="text-sm text-slate-500">{category.count} products</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-12 md:px-6">
        <h2 className="mb-5 text-2xl font-semibold">Featured Products</h2>
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          {featured.map((item) => (
            <ProductCard key={item.id} product={item} onAddToCart={() => {}} onWishlist={() => {}} />
          ))}
        </div>
      </section>
    </main>
  );
}
