import type { StudentAnswer } from "../api/client";

type StudentChatPageProps = {
  question: string;
  answer: StudentAnswer | null;
  loading: boolean;
  error: string | null;
  onQuestionChange: (value: string) => void;
  onAsk: () => void;
};

export function StudentChatPage({
  question,
  answer,
  loading,
  error,
  onQuestionChange,
  onAsk,
}: StudentChatPageProps) {
  return (
    <section className="space-y-4">
      <header>
        <h2 className="text-2xl font-semibold text-ink">Technology Student</h2>
        <p className="mt-1 text-sm text-graphite">
          Answers are generated from approved retrieved knowledge and include citations when supported.
        </p>
      </header>
      <div className="rounded-md border border-slate-200 bg-white p-4">
        <label className="block text-sm font-medium text-ink" htmlFor="question">Question</label>
        <textarea
          id="question"
          className="mt-2 min-h-28 w-full rounded-md border border-slate-300 p-3 text-sm"
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
        />
        <button
          className="mt-3 rounded-md bg-signal px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400"
          type="button"
          disabled={loading || question.trim().length < 3}
          onClick={onAsk}
        >
          {loading ? "Asking..." : "Ask"}
        </button>
      </div>
      {error ? <p role="alert" className="text-sm font-medium text-amber-700">{error}</p> : null}
      {answer ? (
        <article className="rounded-md border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="rounded-md border border-slate-200 px-3 py-1">{answer.evidence_status}</span>
            <span className="rounded-md border border-slate-200 px-3 py-1">
              Confidence {Math.round(answer.confidence * 100)}%
            </span>
          </div>
          <p className="mt-4 whitespace-pre-wrap text-ink">{answer.answer}</p>
          {answer.limitations.length > 0 ? (
            <ul className="mt-4 list-disc pl-5 text-sm text-graphite">
              {answer.limitations.map((item) => <li key={item}>{item}</li>)}
            </ul>
          ) : null}
          <div className="mt-4 space-y-2">
            <h3 className="text-sm font-semibold text-ink">Citations</h3>
            {answer.sources.length === 0 ? <p className="text-sm text-graphite">No citations available.</p> : null}
            {answer.sources.map((source) => (
              <p key={`${source.source_id}-${source.document_id}`} className="text-sm text-graphite">
                {source.title} · {source.section ?? "section unavailable"} · score {source.relevance_score}
              </p>
            ))}
          </div>
        </article>
      ) : null}
    </section>
  );
}
