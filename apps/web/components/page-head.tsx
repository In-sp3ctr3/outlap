import type { ReactNode } from "react";

export function PageHead({
  title,
  detail,
  action,
}: {
  title: string;
  detail: string;
  action?: ReactNode;
}) {
  return (
    <header className="page-head">
      <div>
        <h1>{title}</h1>
        <p>{detail}</p>
      </div>
      {action}
    </header>
  );
}
