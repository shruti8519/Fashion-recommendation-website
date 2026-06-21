import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import TopNav from "../components/TopNav";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

const emptyProduct = {
  name: "",
  category: "Clothing Items",
  brand: "",
  price: 999,
  rating: 4.2,
  description: "",
  image: "https://picsum.photos/seed/admin-product/600/700",
  stock: 20,
};

export default function AdminPage() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(emptyProduct);

  const load = async () => {
    const [p, o, u] = await Promise.all([api.adminProducts(), api.adminOrders(), api.adminUsers()]);
    setProducts(p.items || []);
    setOrders(o.items || []);
    setUsers(u.items || []);
  };

  useEffect(() => {
    if ((session?.user?.role || "user") !== "admin") {
      toast.error("Admin access only");
      navigate("/dashboard");
      return;
    }
    load().catch(() => toast.error("Failed to load admin data"));
  }, [navigate, session?.user?.role]);

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="mx-auto max-w-7xl space-y-8 px-4 py-8 md:px-6">
        <h1 className="text-3xl font-semibold">Admin Panel</h1>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-lg font-semibold">Add Product</h2>
          <div className="grid gap-2 md:grid-cols-3">
            {Object.keys(emptyProduct).map((key) => (
              <input key={key} className="rounded-lg border border-slate-300 px-3 py-2" value={form[key]} onChange={(e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))} placeholder={key} />
            ))}
            <button className="rounded-lg bg-brand-500 px-4 py-2 text-white" onClick={() => api.adminCreateProduct({ ...form, price: Number(form.price), rating: Number(form.rating), stock: Number(form.stock) }).then(load)}>
              Add
            </button>
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-lg font-semibold">Orders ({orders.length})</h2>
            {orders.slice(0, 8).map((o) => <p key={o.id} className="mb-1 text-sm">{o.id.slice(0, 8)} - Rs.{o.total} - {o.status}</p>)}
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-lg font-semibold">Users ({users.length})</h2>
            {users.slice(0, 8).map((u) => <p key={u.id} className="mb-1 text-sm">{u.email}</p>)}
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-lg font-semibold">Manage Products ({products.length})</h2>
          <div className="grid gap-2">
            {products.slice(0, 20).map((p) => (
              <div key={p.id} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2">
                <p className="text-sm">{p.name}</p>
                <button className="text-sm text-rose-600" onClick={() => api.adminDeleteProduct(p.id).then(load)}>Delete</button>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
