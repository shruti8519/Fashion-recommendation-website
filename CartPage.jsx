import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import TopNav from "../components/TopNav";
import { api, resolveImageUrl } from "../api";
import { useAuth } from "../context/AuthContext";

export default function CartPage() {
  const { session } = useAuth();
  const [cart, setCart] = useState({ items: [], subtotal: 0, shipping: 0, total: 0 });

  const fetchCart = async () => {
    const res = await api.cart(session.user.id);
    setCart(res);
  };

  useEffect(() => {
    fetchCart();
  }, [session.user.id]);

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="mx-auto max-w-6xl px-4 py-8 md:px-6">
        <h1 className="mb-5 text-3xl font-semibold">Shopping Cart</h1>
        <div className="grid gap-5 md:grid-cols-3">
          <div className="space-y-3 md:col-span-2">
            {cart.items.map((item) => (
              <div key={item.product.id} className="flex gap-3 rounded-xl border border-slate-200 bg-white p-3">
                <img src={resolveImageUrl(item.product.image)} alt={item.product.name} className="h-24 w-24 rounded-lg object-cover" />
                <div className="flex-1">
                  <p className="font-medium">{item.product.name}</p>
                  <p className="text-sm text-slate-500">Rs.{item.product.price} each</p>
                  <div className="mt-2 flex items-center gap-2">
                    <button className="rounded border px-2 py-1" onClick={() => api.updateCart({ user_id: session.user.id, product_id: item.product.id, quantity: Math.max(1, item.quantity - 1) }).then(fetchCart)}>-</button>
                    <span>{item.quantity}</span>
                    <button className="rounded border px-2 py-1" onClick={() => api.updateCart({ user_id: session.user.id, product_id: item.product.id, quantity: item.quantity + 1 }).then(fetchCart)}>+</button>
                    <button className="ml-3 text-sm text-rose-600" onClick={() => api.removeFromCart({ user_id: session.user.id, product_id: item.product.id }).then(fetchCart)}>Remove</button>
                  </div>
                </div>
                <p className="font-semibold">Rs.{item.line_total}</p>
              </div>
            ))}
            {cart.items.length === 0 && <p className="rounded-xl border border-slate-200 bg-white p-6 text-slate-500">Your cart is empty.</p>}
          </div>
          <aside className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="mb-3 text-lg font-semibold">Price Details</h3>
            <p className="mb-1 text-sm">Subtotal: Rs.{cart.subtotal}</p>
            <p className="mb-1 text-sm">Shipping: Rs.{cart.shipping}</p>
            <p className="mb-4 text-lg font-semibold">Total: Rs.{cart.total}</p>
            <Link to="/checkout" className="block rounded-lg bg-brand-500 px-4 py-2 text-center font-medium text-white">Proceed to Checkout</Link>
          </aside>
        </div>
      </section>
    </main>
  );
}
