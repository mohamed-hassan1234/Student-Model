import { useEffect, useState } from "react";

import {
  askTechnologyStudent,
  fetchCurriculum,
  fetchSources,
  fetchSystemStatus,
  type CurriculumTopic,
  type Source,
  type StudentAnswer,
  type SystemStatus,
} from "./api/client";
import { CurriculumPage } from "./components/CurriculumPage";
import { SourcesPage } from "./components/SourcesPage";
import { StudentChatPage } from "./components/StudentChatPage";
import { SystemStatusPage } from "./components/SystemStatusPage";

type View = "status" | "sources" | "student" | "curriculum";

export function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [topics, setTopics] = useState<CurriculumTopic[]>([]);
  const [view, setView] = useState<View>("status");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<StudentAnswer | null>(null);
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadStatus() {
      try {
        const [result, sourceResult, curriculumResult] = await Promise.all([
          fetchSystemStatus(),
          fetchSources().catch(() => []),
          fetchCurriculum().catch(() => []),
        ]);
        if (active) {
          setStatus(result);
          setSources(sourceResult);
          setTopics(curriculumResult);
          setError(null);
        }
      } catch {
        if (active) {
          setStatus(null);
          setError("The API status endpoint could not be reached.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadStatus();
    return () => {
      active = false;
    };
  }, []);

  async function handleAsk() {
    setAsking(true);
    setError(null);
    try {
      setAnswer(await askTechnologyStudent(question));
    } catch {
      setAnswer(null);
      setError("The Technology Student could not answer right now.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-6xl px-5 py-6 sm:px-8">
        <header className="mb-6 border-b border-slate-200 pb-5">
          <p className="text-sm font-semibold uppercase tracking-wide text-signal">DevMind AI</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">Technology Student v0.1</h1>
          <nav className="mt-4 flex flex-wrap gap-2" aria-label="Primary">
            {(["status", "sources", "student", "curriculum"] as View[]).map((item) => (
              <button
                key={item}
                type="button"
                className={`rounded-md border px-3 py-2 text-sm font-medium ${
                  view === item ? "border-signal bg-signal text-white" : "border-slate-200 bg-white text-graphite"
                }`}
                onClick={() => setView(item)}
              >
                {item}
              </button>
            ))}
          </nav>
        </header>
        {view === "status" ? <SystemStatusPage status={status} loading={loading} error={error} embedded /> : null}
        {view === "sources" ? <SourcesPage sources={sources} loading={loading} error={error} /> : null}
        {view === "student" ? (
          <StudentChatPage
            question={question}
            answer={answer}
            loading={asking}
            error={error}
            onQuestionChange={setQuestion}
            onAsk={handleAsk}
          />
        ) : null}
        {view === "curriculum" ? <CurriculumPage topics={topics} /> : null}
      </div>
    </main>
  );
}
