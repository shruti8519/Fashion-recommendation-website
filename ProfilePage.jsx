import { useState } from "react";
import toast from "react-hot-toast";
import TopNav from "../components/TopNav";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export default function ProfilePage() {
  const { session, login } = useAuth();
  const [name, setName] = useState(session.user.profile?.name || "");
  const [phone, setPhone] = useState(session.user.profile?.phone || "");

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="mx-auto max-w-4xl px-4 py-8 md:px-6">
        <h1 className="mb-5 text-3xl font-semibold">Profile</h1>
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <p className="mb-2">Email: {session.user.email}</p>
          <div className="mb-3 grid gap-3 md:grid-cols-2">
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" className="rounded-lg border border-slate-300 px-3 py-2" />
            <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone number" className="rounded-lg border border-slate-300 px-3 py-2" />
          </div>
          <p className="mb-2">Styles: {(session.user.profile?.preferred_styles || []).join(", ") || "None"}</p>
          <p className="mb-5">Colors: {(session.user.profile?.preferred_colors || []).join(", ") || "None"}</p>
          <button
            className="rounded-xl bg-brand-500 px-5 py-2 text-white"
            onClick={async () => {
              const updated = await api.updateUser(session.user.id, { name, phone });
              login({ ...session, user: updated.user });
              toast.success("Profile updated");
            }}
          >
            Save Profile
          </button>
        </div>
      </section>
    </main>
  );
}
