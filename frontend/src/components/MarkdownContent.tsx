import { lazy, Suspense } from "react";

const ReactMarkdown = lazy(() => import("react-markdown"));

interface MarkdownContentProps {
  content: string;
}

export const MarkdownContent: React.FC<MarkdownContentProps> = ({ content }) => (
  <div className="markdown-content">
    <Suspense fallback={<span className="markdown-pending" role="status">Formatting answer…</span>}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </Suspense>
  </div>
);