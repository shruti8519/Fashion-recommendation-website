import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PRODUCT_IMAGE_FALLBACK, resolveImageUrl } from "../api";

export default function ProductCard({ product, onAddToCart, onWishlist }) {
  const primary = resolveImageUrl(product.image);
  const [imgSrc, setImgSrc] = useState(primary);

  useEffect(() => {
    setImgSrc(resolveImageUrl(product.image));
  }, [product.id, product.image]);

  return (
    <article className="group flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-sm ring-1 ring-black/[0.03] transition duration-200 hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md">
      <Link to={`/products/${product.id}`} className="relative block shrink-0 overflow-hidden bg-slate-100">
        <div className="aspect-[4/5] w-full">
          <img
            src={imgSrc}
            alt={product.name}
            loading="lazy"
            decoding="async"
            className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
            onError={() => setImgSrc(PRODUCT_IMAGE_FALLBACK)}
          />
        </div>
      </Link>
      <div className="flex min-h-0 flex-1 flex-col p-4 pt-3">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-600">{product.category}</p>
        <Link
          to={`/products/${product.id}`}
          className="mt-1 line-clamp-2 min-h-[2.5rem] text-sm font-semibold leading-snug text-slate-900 transition hover:text-brand-600"
        >
          {product.name}
        </Link>
        <p className="mt-1 truncate text-xs text-slate-500">{product.brand}</p>
        <div className="mt-auto flex flex-wrap items-baseline gap-x-2 gap-y-1 pt-3">
          <p className="text-base font-bold text-slate-900">Rs.{product.price}</p>
          <p className="text-xs text-slate-400 line-through">Rs.{product.original_price}</p>
          <p className="text-xs font-semibold text-rose-500">{product.discount_percent}% off</p>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => onAddToCart(product.id)}
            className="rounded-lg bg-brand-500 px-3 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-1"
          >
            Add to Cart
          </button>
          <button
            type="button"
            onClick={() => onWishlist(product.id)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
          >
            Wishlist
          </button>
        </div>
      </div>
    </article>
  );
}
