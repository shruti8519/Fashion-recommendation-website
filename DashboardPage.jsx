import { useEffect, useState } from "react";
import TopNav from "../components/TopNav";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function DashboardPage() {
  const { session } = useAuth();
  const [orders, setOrders] = useState([]);
  const [reco, setReco] = useState([]);

  useEffect(() => {
    api.orders(session.user.id).then((res) => setOrders(res.items || []));
    api.recommend({ user_id: session.user.id, top_k: 6 }).then((res) => setReco(res.items || []));
  }, [session.user.id]);

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="mx-auto max-w-7xl px-4 py-8 md:px-6">
        <h1 className="mb-1 text-3xl font-semibold">Welcome back</h1>
        <p className="mb-6 text-sm text-slate-500">{session.user.email}</p>
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-lg font-semibold">Order History</h2>
            {orders.length === 0 ? <p className="text-sm text-slate-500">No orders yet.</p> : orders.map((x) => <p key={x.id} className="mb-1 text-sm">{x.id.slice(0, 10)} - Rs.{x.total} - {x.status}</p>)}
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-lg font-semibold">AI Recommendations</h2>
            {reco.length === 0 ? <p className="text-sm text-slate-500">No recommendations.</p> : reco.map((x) => <p key={x.item_id} className="mb-1 text-sm">{x.category} - {x.color} ({Math.round(x.score * 100)}%)</p>)}
          </div>
        </div>
      </section>
    </main>
  );
}
