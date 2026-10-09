import React from "react";
import { Users, Target } from "lucide-react";
import type { RFMSegment } from "../types/analytics";

export const RFMSegmentsPanel: React.FC<{ segments?: RFMSegment[]; isLoading: boolean }> = ({ segments, isLoading }) => (
  <section className="glass-card rfm-panel" aria-labelledby="rfm-title">
    <div className="rfm-heading">
      <span className="overview-action-icon"><Target size={17} /></span>
      <div><h3 id="rfm-title">Customer segments</h3><p>Group customers by purchase recency, frequency, and value.</p></div>
    </div>
    {isLoading ? <p className="rfm-empty">Loading customer segments…</p> : !segments?.length ? (
      <p className="rfm-empty">Not enough customer purchase history to build segments yet.</p>
    ) : <div className="rfm-grid">{segments.map((segment) => (
      <article className="rfm-segment" key={segment.id}>
        <div><strong>{segment.name}</strong><span className="rfm-count"><Users size={13} /> {segment.count}</span></div>
        <p>{segment.strategy}</p>
        <small>{segment.percentage}% of customers</small>
      </article>
    ))}</div>}
  </section>
);
