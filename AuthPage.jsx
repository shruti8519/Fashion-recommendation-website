import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function AuthPage() {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!email.includes("@") || password.length < 6) {
      toast.error("Enter valid email and password (min 6 chars)");
      return;
    }
    setLoading(true);
    try {
      const payload = isSignup
        ? await api.signup({ email, password, preferred_styles: [], preferred_colors: [] })
        : await api.login({ email, password });
      login(payload);
      toast.success("Welcome to FashionHub");
      navigate(isSignup ? "/onboarding" : "/dashboard");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h2 className="mb-6 text-3xl font-semibold">{isSignup ? "Create Account" : "Login"}</h2>
        <div className="space-y-4">
          <input className="w-full rounded-xl border border-slate-300 p-3" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="w-full rounded-xl border border-slate-300 p-3" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button disabled={loading} className="w-full rounded-xl bg-brand-500 py-3 font-medium">
            {loading ? "Please wait..." : isSignup ? "Sign up" : "Login"}
          </button>
          <button type="button" className="text-left text-sm text-slate-500 underline" onClick={async () => {
            if (!email.includes("@")) return toast.error("Enter email first");
            const res = await api.forgotPassword({ email });
            toast.success(res.message);
          }}>Forgot password?</button>
        </div>
        <button type="button" onClick={() => setIsSignup(!isSignup)} className="mt-4 text-sm text-slate-600">
          {isSignup ? "Already have account? Login" : "No account? Sign up"}
        </button>
      </form>
    </main>
  );
}
