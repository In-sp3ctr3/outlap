"use client";

import { CheckCircle2, FileUp, Play, TableProperties } from "lucide-react";
import { useMemo, useState } from "react";

import { StateNotice } from "@/components/state-notice";
import { StatusBadge } from "@/components/status";
import type { ImportPreview, ImportTemplateType, ImportValidationMessage } from "@/lib/api";
import { confirmImport, previewImport } from "@/lib/api";

const TEMPLATE_LABELS: Record<ImportTemplateType, string> = {
  team_state: "Team state",
  team_slots: "Team slots",
  market_prices: "Market prices",
  fantasy_scores: "Fantasy scores",
  league_table: "League table",
  chips_state: "Chips state",
  season_totals: "Season totals",
  transfer_history_optional: "Transfer history",
  rival_team_slots: "Rival team slots",
};

const TEMPLATE_HEADERS: Record<ImportTemplateType, string> = {
  team_state:
    "season,event_id,slot,team_name,cost_cap_millions,budget_used_millions,budget_remaining_millions,free_transfers,transfer_penalty_points,total_points,source_note\n",
  team_slots:
    "season,event_id,slot,asset_id,asset_type,display_name,constructor_name,boost_multiplier,source_note\n",
  market_prices:
    "season,event_id,asset_id,asset_type,display_name,constructor_name,price_millions,ownership_pct,selected_by_pct,source_note\n",
  fantasy_scores:
    "season,event_id,asset_id,asset_type,display_name,official_fantasy_points,source_note\n",
  league_table:
    "season,event_id,league_id,league_name,rank,entry_name,manager_name,total_points,round_points,source_note\n",
  chips_state: "season,event_id,slot,chip_name,status,used_event_id,source_note\n",
  season_totals:
    "season,event_id,slot,team_name,total_points,overall_rank,league_rank,source_note\n",
  transfer_history_optional:
    "season,event_id,slot,transfer_number,out_asset_id,out_display_name,in_asset_id,in_display_name,penalty_points,chip_active,source_note\n",
  rival_team_slots:
    "season,event_id,league_id,entry_name,rank,asset_id,asset_type,display_name,constructor_name,source_note\n",
};

export function ImportWizard({ onImported }: { onImported: () => Promise<void> }) {
  const [templateType, setTemplateType] = useState<ImportTemplateType>("market_prices");
  const [rawText, setRawText] = useState(TEMPLATE_HEADERS.market_prices);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const columns = useMemo(() => Object.keys(preview?.rows[0] ?? {}).slice(0, 8), [preview]);

  async function runPreview() {
    setBusy(true);
    try {
      setError(null);
      setMessage(null);
      setPreview(await previewImport({ templateType, rawText }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to preview import");
    } finally {
      setBusy(false);
    }
  }

  async function runConfirm() {
    if (!preview) return;
    setBusy(true);
    try {
      setError(null);
      const result = await confirmImport(preview, rawText);
      setMessage(result.message);
      await onImported();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to confirm import");
    } finally {
      setBusy(false);
    }
  }

  async function handleFile(file: File | null) {
    if (!file) return;
    setRawText(await file.text());
    setPreview(null);
  }

  return (
    <section className="panel import-wizard" aria-labelledby="import-wizard-title">
      <div className="page-head">
        <div>
          <h2 id="import-wizard-title">Manual CSV import</h2>
          <p>Paste spreadsheet data, preview normalized rows, then write a local DuckDB snapshot.</p>
        </div>
        <StatusBadge status={preview?.importable ? "real_current" : "missing"} label={preview?.importable ? "Preview ready" : "Needs preview"} />
      </div>
      <div className="grid two">
        <label className="field">
          Template
          <select
            className="select"
            value={templateType}
            onChange={(event) => {
              const next = event.target.value as ImportTemplateType;
              setTemplateType(next);
              setRawText(TEMPLATE_HEADERS[next]);
              setPreview(null);
            }}
          >
            {(Object.keys(TEMPLATE_LABELS) as ImportTemplateType[]).map((template) => (
              <option key={template} value={template}>
                {TEMPLATE_LABELS[template]}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          Upload CSV or TSV
          <span className="file-input">
            <FileUp size={16} aria-hidden="true" />
            <input
              accept=".csv,.tsv,.txt,text/csv,text/tab-separated-values"
              type="file"
              onChange={(event) => void handleFile(event.target.files?.[0] ?? null)}
            />
          </span>
        </label>
      </div>
      <label className="field">
        CSV text
        <textarea
          className="textarea"
          placeholder="Paste real exported rows below the header, or upload a CSV/TSV file."
          rows={9}
          value={rawText}
          onChange={(event) => {
            setRawText(event.target.value);
            setPreview(null);
          }}
        />
      </label>
      <div className="button-row">
        <button className="button secondary" type="button" disabled={busy} onClick={runPreview}>
          <TableProperties size={16} aria-hidden="true" />
          Preview import
        </button>
        <button className="button" type="button" disabled={busy || !preview?.importable} onClick={runConfirm}>
          <Play size={16} aria-hidden="true" />
          Confirm import
        </button>
      </div>
      {error ? <StateNotice tone="error" title="Import failed">{error}</StateNotice> : null}
      {message ? (
        <div className="empty success" role="status">
          <CheckCircle2 size={16} aria-hidden="true" />
          {message}
        </div>
      ) : null}
      {preview ? (
        <div className="import-preview">
          <ValidationMessageList messages={preview.messages} />
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.slice(0, 8).map((row, index) => (
                  <tr key={index}>
                    {columns.map((column) => (
                      <td key={column}>{String(row[column] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function ValidationMessageList({ messages }: { messages: ImportValidationMessage[] }) {
  if (messages.length === 0) {
    return <StateNotice tone="info" title="No validation messages" />;
  }
  return (
    <div className="validation-list">
      {messages.map((message, index) => (
        <div className={`validation-message ${message.severity}`} key={`${message.column}-${index}`}>
          <StatusBadge status={message.severity === "error" ? "error" : "partial"} label={message.severity} />
          <span>
            {message.rowNumber ? `Row ${message.rowNumber}: ` : ""}
            {message.column ? `${message.column} · ` : ""}
            {message.message}
          </span>
        </div>
      ))}
    </div>
  );
}
