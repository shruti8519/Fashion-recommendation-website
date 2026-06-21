import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import toast from "react-hot-toast";
import TopNav from "../components/TopNav";
import { api, resolveImageUrl } from "../api";
import { useAuth } from "../context/AuthContext";

export default function ProductDetailPage() {
  const { productId } = useParams();
  const { session } = useAuth();
  const [data, setData] = useState(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  useEffect(() => {
    setData(null);
    let cancelled = false;
    api
      .productDetail(productId)
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch(() => {
        if (!cancelled) setData({ error: true });
      });
    return () => {
      cancelled = true;
    };
  }, [productId]);

  if (!data) return <p className="p-6">Loading...</p>;
  if (data.error) return <p className="p-6 text-red-600">Product not found.</p>;
  const { product, reviews } = data;

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="mx-auto grid max-w-7xl gap-8 px-4 py-8 md:grid-cols-2 md:px-6">
        <div className="space-y-3">
          <img src={resolveImageUrl(product.gallery[0])} alt={product.name} className="h-[430px] w-full rounded-2xl object-cover" />
          <div className="grid grid-cols-3 gap-2">
            {product.gallery.map((img, i) => <img key={`${img}-${i}`} src={resolveImageUrl(img)} alt="preview" className="h-28 w-full rounded-xl object-cover" />)}
          </div>
        </div>
        <div>
          <p className="text-sm font-medium text-brand-500">{product.brand}</p>
          <h1 className="text-3xl font-semibold">{product.name}</h1>
          <p className="mt-2 text-sm text-slate-500">{product.description}</p>
          <div className="mt-5 flex items-end gap-3">
            <p className="text-3xl font-bold text-slate-900">Rs.{product.price}</p>
            <p className="text-lg text-slate-400 line-through">Rs.{product.original_price}</p>
          </div>
          <p className="mt-2 text-sm text-slate-600">Rating: {product.rating} / 5</p>
          <div className="mt-6 flex gap-3">
            <button
              className="rounded-lg bg-brand-500 px-5 py-3 font-medium text-white"
              onClick={async () => {
                if (!session?.user?.id) return toast.error("Login first");
                await api.addToCart({ user_id: session.user.id, product_id: product.id, quantity: 1 });
                toast.success("Added to cart");
              }}
            >
              Add to Cart
            </button>
            <button
              className="rounded-lg border border-slate-300 px-5 py-3"
              onClick={async () => {
                if (!session?.user?.id) return toast.error("Login first");
                await api.saveItem({ user_id: session.user.id, item_id: product.id });
                toast.success("Added to wishlist");
              }}
            >
              Wishlist
            </button>
          </div>
          <div className="mt-8 rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="mb-3 font-semibold">Write a review</h3>
            <div className="grid gap-2 md:grid-cols-4">
              <select className="rounded-lg border border-slate-300 px-3 py-2" value={rating} onChange={(e) => setRating(Number(e.target.value))}>
                {[5, 4, 3, 2, 1].map((x) => <option key={x} value={x}>{x} star</option>)}
              </select>
              <input className="rounded-lg border border-slate-300 px-3 py-2 md:col-span-2" placeholder="Share your experience" value={comment} onChange={(e) => setComment(e.target.value)} />
              <button
                className="rounded-lg bg-slate-900 px-4 py-2 text-white"
                onClick={async () => {
                  if (!session?.user?.id) return toast.error("Login first");
                  await api.addReview(product.id, { user_id: session.user.id, product_id: product.id, rating, comment });
                  toast.success("Review submitted");
                  setComment("");
                  setData(await api.productDetail(productId));
                }}
              >
                Submit
              </button>
            </div>
          </div>
          <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="mb-3 font-semibold">Recent Reviews</h3>
            {reviews.length === 0 ? <p className="text-sm text-slate-500">No reviews yet.</p> : reviews.map((r) => <p key={r.id} className="mb-2 text-sm text-slate-700">{r.rating}★ - {r.comment}</p>)}
          </div>
        </div>
      </section>
    </main>
  );
}
