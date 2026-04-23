import type { ReactNode } from "react";

export function FormSection({
  title,
  hint,
  children
}: {
  title: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <section className="bn-form-section">
      <div className="bn-form-section-head">
        <h3>{title}</h3>
        {hint ? <span>{hint}</span> : null}
      </div>
      {children}
    </section>
  );
}

export function ToggleField({
  label,
  checked,
  onChange,
  disabled = false
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className={`bn-toggle ${disabled ? "is-disabled" : ""}`}>
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

export function SettingsSectionFrame({
  title,
  subtitle,
  action,
  children
}: {
  title: string;
  subtitle: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="bn-settings-content">
      <header className="bn-settings-content-head">
        <div>
          <p className="bn-section-tag">Settings</p>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        {action ?? null}
      </header>
      {children}
    </section>
  );
}
