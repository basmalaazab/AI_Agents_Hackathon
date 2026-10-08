import React, { useEffect, useState } from "react";
import { ArrowRight, BarChart3, Building2, CircleAlert, Eye, EyeOff, LockKeyhole, Mail, ShieldCheck, UserRound } from "lucide-react";
import { acceptInvitation, getInvitationPreview, login, signup, type AuthUser } from "../services/auth";

export const AuthScreen: React.FC<{ onAuthenticated: (user: AuthUser) => void }> = ({ onAuthenticated }) => {
  const [inviteToken] = useState(() => new URLSearchParams(window.location.search).get("invite"));
  const [mode, setMode] = useState<"login" | "signup">(inviteToken ? "signup" : "login");
  const [invite, setInvite] = useState<{ email: string; role: string; business_name: string } | null>(null);
  const [business, setBusiness] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!inviteToken) return;
    getInvitationPreview(inviteToken).then(preview => {
      setInvite(preview);
      setEmail(preview.email);
    }).catch(err => setError(err instanceof Error ? err.message : "This invitation is invalid or expired."));
  }, [inviteToken]);

  function switchMode(nextMode: "login" | "signup") {
    setMode(nextMode);
    setError("");
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = inviteToken
        ? await acceptInvitation(inviteToken, password, name)
        : mode === "login"
          ? await login(email, password)
          : await signup({ business_name: business, full_name: name, email, password });
      if (inviteToken) window.history.replaceState({}, "", window.location.pathname);
      onAuthenticated(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-glow auth-glow-one" aria-hidden="true" />
      <div className="auth-glow auth-glow-two" aria-hidden="true" />
      <section className="auth-shell" aria-label="Clearview BI account access">
        <aside className="auth-showcase">
          <div className="auth-brand">
            <span className="auth-brand-icon"><BarChart3 size={23} strokeWidth={2.5} /></span>
            <span>Clearview<span className="auth-brand-light"> BI</span></span>
          </div>

          <div className="auth-showcase-copy">
            <span className="auth-eyebrow"><span className="auth-eyebrow-dot" /> BUSINESS INTELLIGENCE</span>
            <h1>See your business<br /><em>more clearly.</em></h1>
            <p>Bring your business data together and find the signals that help you make your next move.</p>
          </div>

          <div className="auth-visual" aria-hidden="true">
            <div className="auth-visual-top"><span>Business overview</span><span className="auth-live-dot" />
              <div className="auth-visual-bars"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>
              <div className="auth-visual-line"><span /><span /><span /></div>
              <div className="auth-visual-labels"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span></div>
            </div>
            <div className="auth-visual-note"><span className="auth-note-icon"><TrendingUpIcon /></span><span><strong>One clear view</strong><small>Your data, organized in one place</small></span><ArrowRight size={15} /></div>
          </div>

          <div className="auth-showcase-foot"><ShieldCheck size={15} /> Your company data stays in its own workspace</div>
        </aside>

        <div className="auth-form-side">
          <div className="auth-mobile-brand"><span className="auth-brand-icon"><BarChart3 size={21} /></span><strong>Clearview BI</strong></div>
          <div className="auth-form-heading">
            <span className="auth-form-kicker">{inviteToken ? "COMPANY INVITATION" : mode === "login" ? "YOUR WORKSPACE IS READY" : "GET STARTED"}</span>
            <h2>{inviteToken ? invite ? `Join ${invite.business_name}` : "Accept your invitation" : mode === "login" ? "Welcome back" : "Create your account"}</h2>
            <p>{inviteToken ? invite ? `You’re invited as a ${invite.role}. Create a password to join your team.` : "Verify your invitation to continue." : mode === "login" ? "Sign in to continue to your business dashboard." : "Set up a private workspace for your company."}</p>
          </div>

          {!inviteToken && <div className="auth-mode-switch" role="tablist" aria-label="Account action">
            <button type="button" role="tab" aria-selected={mode === "login"} className={mode === "login" ? "selected" : ""} onClick={() => switchMode("login")}>Sign in</button>
            <button type="button" role="tab" aria-selected={mode === "signup"} className={mode === "signup" ? "selected" : ""} onClick={() => switchMode("signup")}>Create account</button>
          </div>}

          <form onSubmit={submit} className="auth-form" noValidate={false}>
            {mode === "signup" && !inviteToken && <>
              <label className="auth-field"><span>Company name</span><div className="auth-input-wrap"><Building2 size={17} /><input autoFocus required minLength={2} maxLength={160} autoComplete="organization" placeholder="e.g. Acme Studio" value={business} onChange={e => setBusiness(e.target.value)} /></div></label>
            </>}
            {(mode === "signup" || inviteToken) && <>
              <label className="auth-field"><span>Your name <small>Optional</small></span><div className="auth-input-wrap"><UserRound size={17} /><input autoComplete="name" placeholder="How should we address you?" value={name} onChange={e => setName(e.target.value)} /></div></label>
            </>}
            {(!inviteToken || invite) && <label className="auth-field"><span>Work email</span><div className="auth-input-wrap"><Mail size={17} /><input type="email" required readOnly={Boolean(inviteToken)} autoComplete="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} /></div></label>}
            <label className="auth-field"><span>Password{mode === "signup" && <small>At least 8 characters</small>}</span><div className="auth-input-wrap"><LockKeyhole size={17} /><input type={showPassword ? "text" : "password"} required minLength={mode === "signup" ? 8 : 1} autoComplete={mode === "login" ? "current-password" : "new-password"} placeholder={mode === "login" ? "Enter your password" : "Create a strong password"} value={password} onChange={e => setPassword(e.target.value)} /><button type="button" className="auth-password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>

            {error && <div className="auth-error" role="alert"><CircleAlert size={17} /><span>{error}</span></div>}

              <button className="auth-submit" type="submit" disabled={busy || Boolean(inviteToken && !invite)}>
              <span>{busy ? (mode === "login" ? "Signing you in…" : "Creating your workspace…") : inviteToken ? "Join company workspace" : mode === "login" ? "Sign in to Clearview" : "Create company workspace"}</span>
              {!busy && <ArrowRight size={18} />}
              {busy && <span className="auth-spinner" aria-hidden="true" />}
            </button>
          </form>

          <div className="auth-form-foot"><LockKeyhole size={14} /><span>Protected sign in · Your data is private to your company</span></div>
        </div>
      </section>
      <p className="auth-copyright">CLEARVIEW BI <span>·</span> BUSINESS INSIGHTS FOR EVERY TEAM</p>
    </main>
  );
};

const TrendingUpIcon = () => <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6" /></svg>;
