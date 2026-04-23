import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownArticleProps = {
  markdown: string;
};

export function MarkdownArticle({ markdown }: MarkdownArticleProps) {
  return (
    <div className="markdown-article">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children, ...props }) => (
            <h1 className="markdown-h1" {...props}>
              {children}
            </h1>
          ),
          h2: ({ children, ...props }) => (
            <h2 className="markdown-h2" {...props}>
              {children}
            </h2>
          ),
          h3: ({ children, ...props }) => (
            <h3 className="markdown-h3" {...props}>
              {children}
            </h3>
          ),
          a: ({ children, href, ...props }) => {
            const firstChild = Array.isArray(children) ? children[0] : children;
            const text = typeof firstChild === "string" ? firstChild : "";
            const isOriginLink = text.startsWith("原片 @");

            if (isOriginLink) {
              return (
                <span className="origin-link">
                  <a href={href} target="_blank" rel="noreferrer" {...props}>
                    {children}
                  </a>
                </span>
              );
            }

            return (
              <a href={href} target="_blank" rel="noreferrer" {...props}>
                {children}
              </a>
            );
          },
          ul: ({ children, ...props }) => (
            <ul className="markdown-list" {...props}>
              {children}
            </ul>
          ),
          ol: ({ children, ...props }) => (
            <ol className="markdown-list markdown-list-ordered" {...props}>
              {children}
            </ol>
          ),
          li: ({ children, ...props }) => (
            <li className="markdown-list-item" {...props}>
              {children}
            </li>
          ),
          img: ({ alt, src, ...props }) => (
            <img className="markdown-image" src={src ?? ""} alt={alt ?? ""} loading="lazy" {...props} />
          ),
          code({ inline, className, children, ...props }) {
            if (inline) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            }
            return (
              <pre className="markdown-code-block">
                <code className={className} {...props}>
                  {children}
                </code>
              </pre>
            );
          }
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
