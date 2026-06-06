import type { ReactNode } from "react";

type NoticeTone = "empty" | "error" | "info" | "loading";

export function StateNotice({
  tone,
  title,
  children,
}: {
  tone: NoticeTone;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className={tone} role={tone === "error" ? "alert" : "status"}>
      <strong>{title}</strong>
      {children ? <p>{children}</p> : null}
    </div>
  );
}
