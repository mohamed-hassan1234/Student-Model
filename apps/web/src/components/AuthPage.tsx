import type { FormEvent } from "react";

import type { PublicUser } from "../api/client";

type AuthPageProps = {
  user: PublicUser | null;
  email: string;
  passwordValue: string;
  loading: boolean;
  error: string | null;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onLogin: () => void;
  onLogout: () => void;
};

export function AuthPage({
  user,
  email,
  passwordValue,
  loading,
  error,
  onEmailChange,
  onPasswordChange,
  onLogin,
  onLogout,
}: AuthPageProps) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onLogin();
  }

  if (user) {
    return (
      <section className="rounded-md border border-slate-200 bg-white p-5">
        <h2 className="text-xl font-semibold text-ink">Authenticated User</h2>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="font-medium text-graphite">Email</dt>
            <dd className="text-ink">{user.email}</dd>
          </div>
          <div>
            <dt className="font-medium text-graphite">Roles</dt>
            <dd className="text-ink">{user.roles.join(", ")}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="font-medium text-graphite">Permissions</dt>
            <dd className="mt-1 flex flex-wrap gap-2">
              {user.permissions.map((permission) => (
                <span key={permission} className="rounded bg-slate-100 px-2 py-1 text-xs text-graphite">
                  {permission}
                </span>
              ))}
            </dd>
          </div>
        </dl>
        <button className="mt-5 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white" onClick={onLogout} type="button">
          Sign out
        </button>
      </section>
    );
  }

  return (
    <section className="rounded-md border border-slate-200 bg-white p-5">
      <h2 className="text-xl font-semibold text-ink">Sign In</h2>
      <form className="mt-4 grid gap-3 sm:max-w-md" onSubmit={submit}>
        <label className="text-sm font-medium text-graphite">
          Email
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-ink"
            type="email"
            value={email}
            onChange={(event) => onEmailChange(event.target.value)}
          />
        </label>
        <label className="text-sm font-medium text-graphite">
          Password
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-ink"
            type="password"
            value={passwordValue}
            onChange={(event) => onPasswordChange(event.target.value)}
          />
        </label>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button className="rounded-md bg-signal px-4 py-2 text-sm font-semibold text-white" disabled={loading} type="submit">
          {loading ? "Signing in" : "Sign in"}
        </button>
      </form>
    </section>
  );
}
