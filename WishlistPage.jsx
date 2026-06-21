import { useEffect, useState } from "react";
import TopNav from "../components/TopNav";
import { useAuth } from "../context/AuthContext";
import { api, resolveImageUrl } from "../api";

export default function WishlistPage() {
  const { session } = useAuth();
  const [savedProducts, setSavedProducts] = useState([]);

  useEffect(() => {
    Promise.all([api.saved(session.user.id), api.products({ limit: 200 })]).then(([savedRes, productRes]) => {
      const ids = new Set(savedRes.saved || []);
      setSavedProducts((productRes.items || []).filter((x) => ids.has(String(x.id))));
    });
  }, [session.user.id]);

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="mx-auto max-w-6xl px-4 py-8 md:px-6">
        <h1 className="mb-5 text-3xl font-semibold">Your Wishlist</h1>
        {savedProducts.length === 0 ? (
          <p className="text-slate-500">No items saved yet.</p>
        ) : (
          <div className="grid gap-3">
            {savedProducts.map((item) => (
              <div key={item.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3">
                <div className="flex items-center gap-3">
                  <img src={resolveImageUrl(item.image)} alt={item.name} className="h-16 w-16 rounded-lg object-cover" />
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-slate-500">Rs.{item.price}</p>
                  </div>
                </div>
                <button className="text-sm text-rose-600" onClick={() => api.unsave(session.user.id, item.id).then(() => setSavedProducts((prev) => prev.filter((x) => x.id !== item.id)))}>
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
