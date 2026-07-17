import { useEffect, useState } from "react";

import { approveReview, fetchPendingReviews, type ReviewItem } from "../api/client";
import { StatusBadge } from "./StatusBadge";

export function HumanReviewQueuePage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchPendingReviews()
      .then((result) => {
        if (active) {
          setReviews(result);
        }
      })
      .catch(() => {
        if (active) {
          setError("Review queue is unavailable.");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleApprove(reviewId: string) {
    setError(null);
    try {
      const updated = await approveReview(reviewId);
      setReviews((current) => current.map((item) => (item.review_id === reviewId ? updated : item)));
    } catch {
      setError("The review action was rejected.");
    }
  }

  return (
    <section className="space-y-4">
      <header>
        <h2 className="text-2xl font-semibold text-ink">Human Review Queue</h2>
        <p className="mt-1 text-sm text-graphite">Generated examples are not training-ready until a reviewer approves them.</p>
      </header>
      {loading ? <p aria-label="Loading review queue" className="text-sm text-graphite">Loading review queue...</p> : null}
      {error ? <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {!loading && !error && reviews.length === 0 ? <p className="text-sm text-graphite">No pending reviews.</p> : null}
      <div className="space-y-3">
        {reviews.map((review) => (
          <article key={review.review_id} className="rounded-md border border-slate-200 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-ink">{review.review_id}</h3>
                <p className="text-sm text-graphite">Candidate: {review.candidate_id}</p>
                <p className="text-sm text-graphite">Question: {review.question_id}</p>
              </div>
              <StatusBadge label={review.status} tone={review.status === "approved" ? "healthy" : "warning"} />
            </div>
            <button
              type="button"
              className="mt-3 rounded-md border border-signal bg-signal px-3 py-2 text-sm font-medium text-white"
              onClick={() => void handleApprove(review.review_id)}
            >
              Approve
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
