# Personalized Fashion Recommendation System (Deep Learning + Full Stack)

Portfolio-grade fashion platform inspired by premium e-commerce UX (Zara/ASOS style), with a real deep learning recommendation backend.

## Tech Stack

- Frontend: React + Vite + Tailwind CSS + Framer Motion
- Backend: FastAPI
- Deep Learning: TensorFlow (MobileNetV2 transfer learning + neural metadata projection)

## Project Structure

- `frontend/` - premium UI with auth, onboarding, dashboard, AI insights, wishlist, profile
- `backend/` - FastAPI endpoints (`/login`, `/signup`, `/recommend`, `/save-item`)
- `model/` - optional training pipeline for ranker fine-tuning

## Deep Learning Pipeline

1. Load Kaggle fashion dataset (`fashion.csv`) and images.
2. Extract image embeddings using `MobileNetV2` (pretrained CNN).
3. Encode metadata (`category`, `color`, `style`) and project via dense neural net.
4. Fuse image + metadata embeddings into a hybrid vector.
5. Build user embedding from profile preferences and saved history.
6. Rank items using cosine similarity and return scored recommendations with AI reasons.

## Dataset Setup

Required dataset:
[Fashion and Color Recommendation Dataset](https://www.kaggle.com/datasets/suryaprabha19/fashion-and-color-recommendation-dataset)

Place files like:

- `backend/data/fashion.csv`
- `backend/data/images/...`

If your filenames/columns differ slightly, the backend uses flexible column matching for id/category/color/style/image.

## Run Backend

```bash
cd backend
## Use Python 3.11 or 3.12 (TensorFlow compatibility)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# JSON mode (no PostgreSQL needed): keep DATABASE_URL unset in backend/.env
uvicorn app.main:app --reload
```

Backend runs on `http://127.0.0.1:8000`.

Default environment variables (recommended for no-DB local run):

- Create `backend/.env`:
  - `JWT_SECRET=dev-secret-change-me`
  - `FASHION_DATASET_CSV=c:/Fashion web/backend/data/fashion.csv`
  - `FASHION_IMAGE_ROOT=c:/Fashion web/backend/data/images`
  - Do not set `DATABASE_URL` to stay in JSON storage mode.

Optional environment variables:

- `FASHION_DATASET_CSV` (default: `backend/data/fashion.csv`)
- `FASHION_IMAGE_ROOT` (default: `backend/data/images`)
- `JWT_SECRET`
- `DATABASE_URL` (PostgreSQL URL; only set this if you want PostgreSQL mode)
- `STRIPE_SECRET_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

## Run Frontend

```bash
cd frontend
npm install
# Create frontend/.env with VITE_API_URL=http://127.0.0.1:8000
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`.

Optional:

- set `VITE_API_URL` in a `.env` file inside `frontend/` if backend host differs.

## API Endpoints

- `POST /signup`
- `POST /login`
- `POST /recommend`
- `POST /save-item`
- `GET /saved/{user_id}`
- `POST /payments/stripe/create-intent`
- `POST /payments/razorpay/create-order`
- `POST /payments/razorpay/verify`
- `GET /robots.txt`
- `GET /sitemap.xml`
- `GET /ssr/products/{product_id}`

## Notes

- `model/train_recommender.py` provides an optional deeper training path for learning a user-item ranker.
- Current recommender already uses real deep neural components (CNN + dense embedding model) in production inference.
