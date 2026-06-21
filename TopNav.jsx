import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function TopNav() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();
  const role = session?.user?.role || "user";

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 md:px-6">
        <Link to="/" className="text-xl font-semibold tracking-wide text-brand-500">
          FashionHub
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/products">Products</Link>
          <Link to="/cart">Cart</Link>
          <Link to="/wishlist">Wishlist</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/profile">Profile</Link>
          {role === "admin" && <Link to="/admin">Admin</Link>}
          {session ? (
            <button
              type="button"
              className="rounded-lg bg-slate-900 px-3 py-1.5 text-white"
              onClick={() => {
                logout();
                navigate("/auth");
              }}
            >
              Logout
            </button>
          ) : (
            <Link to="/auth" className="rounded-lg bg-brand-500 px-3 py-1.5 text-white">
              Login
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
