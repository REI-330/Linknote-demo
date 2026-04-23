type ProviderLogoProps = {
  name: string;
  size?: number;
};

type LogoPreset = {
  label: string;
  className: string;
};

const logoPresets: Record<string, LogoPreset> = {
  openai: { label: "OA", className: "provider-logo-mark provider-logo-mark--openai" },
  deepseek: { label: "DS", className: "provider-logo-mark provider-logo-mark--deepseek" },
  qwen: { label: "Q", className: "provider-logo-mark provider-logo-mark--qwen" },
  claude: { label: "CL", className: "provider-logo-mark provider-logo-mark--claude" },
  gemini: { label: "✦", className: "provider-logo-mark provider-logo-mark--gemini" },
  groq: { label: "G", className: "provider-logo-mark provider-logo-mark--groq" },
  ollama: { label: "OL", className: "provider-logo-mark provider-logo-mark--ollama" },
  custom: { label: "AI", className: "provider-logo-mark provider-logo-mark--custom" },
};

function normalizeName(name: string) {
  const clean = name.trim().toLowerCase();
  if (clean === "openai") {
    return "openai";
  }
  if (clean === "deepseek") {
    return "deepseek";
  }
  if (clean === "qwen") {
    return "qwen";
  }
  if (clean === "claude") {
    return "claude";
  }
  if (clean === "gemini" || clean === "gemini openai compatible") {
    return "gemini";
  }
  if (clean === "groq") {
    return "groq";
  }
  if (clean === "ollama") {
    return "ollama";
  }
  return "custom";
}

export function ProviderLogo({ name, size = 24 }: ProviderLogoProps) {
  const preset = logoPresets[normalizeName(name)] ?? logoPresets.custom;
  return (
    <span
      className={preset.className}
      style={{ width: size, height: size, fontSize: Math.max(11, Math.round(size * 0.48)) }}
      aria-hidden="true"
    >
      {preset.label}
    </span>
  );
}
