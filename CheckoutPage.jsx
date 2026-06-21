import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import TopNav from "../components/TopNav";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

const initialForm = {
  full_name: "",
  phone: "",
  address_line1: "",
  address_line2: "",
  city: "",
  state: "",
  postal_code: "",
  payment_method: "COD",
};

export default function CheckoutPage() {
  const { session } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [paymentReference, setPaymentReference] = useState("");

  const initiateStripe = async () => {
    const intent = await api.createStripeIntent({ amount: 150000, currency: "inr" });
    await api.confirmStripePayment(intent.payment_intent_id);
    setPaymentReference(intent.payment_intent_id);
    toast.success("Stripe payment confirmed");
  };

  const initiateRazorpay = async () => {
    const order = await api.createRazorpayOrder({ amount: 150000, currency: "INR" });
    const fakePayment = `pay_${order.order_id.slice(-10)}`;
    await api.verifyRazorpayPayment({
      razorpay_order_id: order.order_id,
      razorpay_payment_id: fakePayment,
      razorpay_signature: "demo-signature",
    }).catch(() => {
      setPaymentReference(fakePayment);
      toast.success("Razorpay sandbox payment reference generated");
    });
    setPaymentReference(fakePayment);
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <TopNav />
      <section className="mx-auto max-w-3xl px-4 py-8 md:px-6">
        <h1 className="mb-5 text-3xl font-semibold">Checkout</h1>
        <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-2">
          {Object.keys(initialForm).filter((field) => field !== "payment_method").map((field) => (
            <input
              key={field}
              className={`rounded-lg border border-slate-300 px-3 py-2 ${field.includes("address") ? "md:col-span-2" : ""}`}
              placeholder={field.replaceAll("_", " ")}
              value={form[field]}
              onChange={(e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))}
            />
          ))}
          <select className="rounded-lg border border-slate-300 px-3 py-2 md:col-span-2" value={form.payment_method} onChange={(e) => setForm((prev) => ({ ...prev, payment_method: e.target.value }))}>
            <option value="COD">Cash on Delivery</option>
            <option value="STRIPE">Stripe</option>
            <option value="RAZORPAY">Razorpay</option>
          </select>
          {form.payment_method === "STRIPE" && (
            <button type="button" className="rounded-lg border border-slate-300 px-4 py-2 md:col-span-2" onClick={initiateStripe}>
              Pay with Stripe (sandbox)
            </button>
          )}
          {form.payment_method === "RAZORPAY" && (
            <button type="button" className="rounded-lg border border-slate-300 px-4 py-2 md:col-span-2" onClick={initiateRazorpay}>
              Pay with Razorpay (sandbox)
            </button>
          )}
          <button
            className="mt-2 rounded-lg bg-brand-500 px-4 py-2 font-medium text-white md:col-span-2"
            onClick={async () => {
              await api.checkout({ user_id: session.user.id, ...form, payment_reference: paymentReference || null });
              toast.success("Order placed successfully");
              navigate("/dashboard");
            }}
          >
            Place Order
          </button>
        </div>
      </section>
    </main>
  );
}
