function resolveBaseUrl() {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") return "http://127.0.0.1:8000";
  return `http://${host}:8000`;
}

const BASE_URL = resolveBaseUrl();

export const PRODUCT_IMAGE_FALLBACK =
  "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=640&h=800&fit=crop&q=82&auto=format";

export function resolveImageUrl(imagePath) {
  if (!imagePath) return PRODUCT_IMAGE_FALLBACK;
  if (String(imagePath).startsWith("http")) return imagePath;
  return `${BASE_URL}${imagePath}`;
}

async function request(path, method = "GET", body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  let res;
  const rawSession = localStorage.getItem("fashion-session");
  const token = rawSession ? JSON.parse(rawSession)?.token : null;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch {
    throw new Error(`Cannot reach backend at ${BASE_URL}`);
  } finally {
    clearTimeout(timeout);
  }

  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  signup: (body) => request("/signup", "POST", body),
  login: (body) => request("/login", "POST", body),
  forgotPassword: (body) => request("/forgot-password", "POST", body),
  updateUser: (userId, body) => request(`/users/${userId}`, "PUT", body),

  categories: () => request("/categories"),
  brands: () => request("/brands"),
  products: (params) => {
    const search = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
    });
    return request(`/products${search.toString() ? `?${search.toString()}` : ""}`);
  },
  productDetail: (productId) => request(`/products/${productId}`),
  addReview: (productId, body) => request(`/products/${productId}/reviews`, "POST", body),

  cart: (userId) => request(`/cart/${userId}`),
  addToCart: (body) => request("/cart/add", "POST", body),
  updateCart: (body) => request("/cart/update", "POST", body),
  removeFromCart: (body) => request("/cart/remove", "POST", body),
  checkout: (body) => request("/checkout", "POST", body),
  orders: (userId) => request(`/orders/${userId}`),

  recommend: (body) => request("/recommend", "POST", body),
  saveItem: (body) => request("/save-item", "POST", body),
  saved: (userId) => request(`/saved/${userId}`),
  unsave: (userId, itemId) => request(`/saved/${userId}/${itemId}`, "DELETE"),

  adminProducts: () => request("/admin/products"),
  adminOrders: () => request("/admin/orders"),
  adminUsers: () => request("/admin/users"),
  adminCreateProduct: (body) => request("/admin/products", "POST", body),
  adminDeleteProduct: (productId) => request(`/admin/products/${productId}`, "DELETE"),
  createStripeIntent: (body) => request("/payments/stripe/create-intent", "POST", body),
  confirmStripePayment: (paymentIntentId) => request(`/payments/stripe/confirm/${paymentIntentId}`, "POST"),
  createRazorpayOrder: (body) => request("/payments/razorpay/create-order", "POST", body),
  verifyRazorpayPayment: (body) => request("/payments/razorpay/verify", "POST", body),
};
