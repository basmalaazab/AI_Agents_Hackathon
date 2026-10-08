import React, { useEffect, useState } from "react";
import { Check, Copy, MailPlus, RefreshCw, ShieldCheck, Trash2, UserRound, Users } from "lucide-react";
import { createInvitation, fetchTeam, removeTeamMember, revokeInvitation, updateTeamRole, type AuthUser, type TeamSnapshot } from "../services/auth";

export const TeamPanel: React.FC<{ user: AuthUser }> = ({ user }) => {
  const [team, setTeam] = useState<TeamSnapshot>({ members: [], invitations: [] });
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"manager" | "viewer">("viewer");
  const [inviteUrl, setInviteUrl] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const canManage = user.role === "business_owner" || user.role === "manager";

  async function refresh() {
    try { setTeam(await fetchTeam()); setError(""); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load your company team."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, []);

  async function invite(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice(""); setInviteUrl("");
    try {
      const result = await createInvitation(email, role);
      setInviteUrl(result.invitation_url); setEmailSent(result.email_sent); setEmail("");
      setNotice(result.email_sent ? `Invitation email sent to ${result.email}.` : `Invitation created for ${result.email}. Copy the secure link and send it to them.`);
      await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Could not create invitation."); }
    finally { setBusy(false); }
  }

  async function copyLink() {
    try { await navigator.clipboard.writeText(inviteUrl); setCopied(true); setTimeout(() => setCopied(false), 1800); }
    catch { setError("Could not copy automatically. Select and copy the invitation link."); }
  }

  async function perform(action: () => Promise<unknown>, message: string) {
    setError(""); setNotice("");
    try { await action(); setNotice(message); await refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not update team access."); }
  }

  return <section className="team-page" aria-labelledby="team-heading">
    <div className="team-intro glass-card">
      <div className="team-icon"><Users size={21} /></div>
      <div><div className="team-eyebrow">COMPANY WORKSPACE</div><h2 id="team-heading">People &amp; access</h2><p>Invite colleagues to work with <strong>{user.business_name}</strong> data.</p></div>
      <span className="team-role-chip"><ShieldCheck size={14} /> {user.role.replaceAll("_", " ")}</span>
    </div>

    {error && <div className="team-feedback team-feedback-error" role="alert">{error}</div>}
    {notice && <div className="team-feedback team-feedback-success" role="status">{notice}</div>}

    <div className="team-grid">
      <div className="glass-card team-card">
        <div className="team-card-heading"><div><h3>Members</h3><p>{team.members.length} people can access this workspace</p></div><button className="btn btn-secondary" onClick={() => void refresh()} aria-label="Refresh team"><RefreshCw size={15} /></button></div>
        <div className="team-member-list">
          {loading ? <div className="team-empty">Loading company members…</div> : team.members.map(member => <div className="team-person" key={member.id}>
            <div className="team-avatar"><UserRound size={17} /></div>
            <div className="team-person-info"><strong>{member.full_name || member.email.split("@")[0]}{member.is_current_user ? " (you)" : ""}</strong><span>{member.email}</span></div>
            {canManage && member.role !== "business_owner" && !member.is_current_user ? <>
              <select aria-label={`Role for ${member.email}`} value={member.role} onChange={e => void perform(() => updateTeamRole(member.id, e.target.value as "manager" | "viewer"), "Member role updated.")}>
                <option value="manager">Manager</option><option value="viewer">Viewer</option>
              </select>
              <button className="team-icon-button danger" aria-label={`Remove ${member.email}`} onClick={() => { if (window.confirm(`Remove ${member.email} from this workspace?`)) void perform(() => removeTeamMember(member.id), "Member removed."); }}><Trash2 size={15} /></button>
            </> : <span className={`team-role-pill ${member.role === "viewer" ? "viewer" : "manager"}`}>{member.role.replaceAll("_", " ")}</span>}
          </div>)}
          {!loading && team.members.length === 0 && <div className="team-empty">No members yet.</div>}
        </div>
      </div>

      <div className="glass-card team-card">
        <div className="team-card-heading"><div><h3>Invite someone</h3><p>They’ll join this company workspace.</p></div><div className="team-invite-icon"><MailPlus size={18} /></div></div>
        {canManage ? <form className="team-invite-form" onSubmit={invite}>
          <label>Email address<input type="email" required autoComplete="off" placeholder="teammate@company.com" value={email} onChange={e => setEmail(e.target.value)} /></label>
          <label>Workspace role<select value={role} onChange={e => setRole(e.target.value as "manager" | "viewer")}><option value="viewer">Viewer — can explore data</option><option value="manager">Manager — can manage sources and invites</option></select></label>
          <p className="team-help">Invitations expire after 7 days. A manager can invite and manage members; a viewer has read-only access.</p>
          <button className="btn btn-primary team-invite-submit" disabled={busy || !email.trim()}><MailPlus size={16} />{busy ? "Creating invitation…" : "Create invitation"}</button>
          {inviteUrl && <div className="team-link-box"><span>{inviteUrl}</span><button type="button" onClick={() => void copyLink()} aria-label="Copy invitation link">{copied ? <Check size={16} /> : <Copy size={16} />}</button><small>{emailSent ? "Email sent. You can also copy this link." : "No email service is configured. Copy the link and send it to the invitee."}</small></div>}
        </form> : <div className="team-viewer-note"><ShieldCheck size={18} /><span>You have viewer access. Ask a company manager to invite or manage members.</span></div>}
      </div>
    </div>

    {canManage && team.invitations.length > 0 && <div className="glass-card team-card team-pending-card"><div className="team-card-heading"><div><h3>Pending invitations</h3><p>Open invitations expire 7 days after creation.</p></div></div>
      {team.invitations.map(item => <div className="team-person" key={item.id}><div className="team-avatar"><MailPlus size={16} /></div><div className="team-person-info"><strong>{item.email}</strong><span>{item.expired ? "Expired" : `Expires ${new Date(item.expires_at).toLocaleDateString()}`}</span></div><span className={`team-role-pill ${item.role}`}>{item.role}</span><button className="team-icon-button danger" aria-label={`Revoke invite for ${item.email}`} onClick={() => void perform(() => revokeInvitation(item.id), "Invitation revoked.")}><Trash2 size={15} /></button></div>)}
    </div>}
  </section>;
};
