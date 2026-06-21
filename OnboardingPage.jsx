import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

const styles = ["Streetwear", "Minimal", "Formal", "Casual", "Athleisure", "Vintage"];
const colors = ["Black", "White", "Blue", "Red", "Green", "Beige", "Brown"];

export default function OnboardingPage() {
  const [pickedStyles, setPickedStyles] = useState([]);
  const [pickedColors, setPickedColors] = useState([]);
  const [budget, setBudget] = useState(100);
  const { session, login } = useAuth();
  const navigate = useNavigate();

  const toggle = (list, setList, v) => setList(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  const finish = () => {
    api.updateUser(session.user.id, { preferred_styles: pickedStyles, preferred_colors: pickedColors, budget }).then((res) => {
      login({ ...session, user: res.user });
      navigate("/dashboard");
    });
  };

  return (
    <main className="mx-auto min-h-screen max-w-4xl p-8">
      <h1 className="mb-6 text-3xl font-semibold">Set Your Fashion DNA</h1>
      <section className="mb-8">
        <h2 className="mb-3 text-lg font-medium">Preferred Styles</h2>
        <div className="flex flex-wrap gap-2">
          {styles.map((s) => (
            <button key={s} onClick={() => toggle(pickedStyles, setPickedStyles, s)} className={`rounded-full border px-4 py-2 ${pickedStyles.includes(s) ? "bg-brand-500 text-white" : ""}`}>
              {s}
            </button>
          ))}
        </div>
      </section>
      <section className="mb-8">
        <h2 className="mb-3 text-lg font-medium">Colors</h2>
        <div className="flex flex-wrap gap-2">
          {colors.map((c) => (
            <button key={c} onClick={() => toggle(pickedColors, setPickedColors, c)} className={`rounded-full border px-4 py-2 ${pickedColors.includes(c) ? "bg-slate-900 text-white" : ""}`}>
              {c}
            </button>
          ))}
        </div>
      </section>
      <section className="mb-8">
        <h2 className="mb-3 text-lg font-medium">Budget (${budget})</h2>
        <input type="range" min="20" max="500" value={budget} onChange={(e) => setBudget(Number(e.target.value))} className="w-full" />
      </section>
      <button onClick={finish} className="rounded-xl bg-brand-500 px-6 py-3 text-white">
        Continue to Dashboard
      </button>
    </main>
  );
}
