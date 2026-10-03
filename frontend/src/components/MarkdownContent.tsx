import { lazy, Suspense } from "react";

const ReactMarkdown = lazy(async () => {
  const [{ default: Markdown }, { default: remarkGfm }] = await Promise.all([
    import("react-markdown"),
    import("remark-gfm"),
  ]);

  return {
    default: ({ children }: { children: string }) => (
      <Markdown remarkPlugins={[remarkGfm]}>{children}</Markdown>
    ),
  };
});

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