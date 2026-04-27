import { ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

interface VideoBannerProps {
  title: string;
  uploader?: string;
  platform?: string;
  coverUrl?: string;
  videoUrl?: string;
  className?: string;
}

const platformLabel: Record<string, string> = {
  bilibili: "哔哩哔哩",
  youtube: "YouTube",
  douyin: "抖音",
  xiaohongshu: "小红书",
};

export function VideoBanner({
  title,
  uploader = "",
  platform = "",
  coverUrl = "",
  videoUrl = "",
  className,
}: VideoBannerProps) {
  const resolvedPlatform = platformLabel[platform] || platform || "";

  return (
    <div
      className={cn(
        "relative flex items-center gap-5 min-h-[120px] rounded-xl overflow-hidden text-white p-5",
        "bg-gradient-to-br from-[#6B7E99] to-[#8FA3BD]",
        "dark:from-[#283B61] dark:to-[#2A5CAA]",
        className
      )}
    >
      {/* Backdrop image */}
      <div className="absolute inset-0 overflow-hidden">
        {coverUrl ? (
          <img
            src={coverUrl}
            alt=""
            className="w-full h-full object-cover opacity-20 dark:opacity-15"
          />
        ) : (
          <div className="w-full h-full bg-black/10" />
        )}
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-center gap-5 w-full">
        {coverUrl ? (
          <img
            src={coverUrl}
            alt={title}
            className="w-36 h-20 rounded-lg object-cover border border-white/20 shrink-0 shadow-sm"
          />
        ) : null}
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold truncate leading-snug" title={title}>
            {title}
          </h3>
          <div className="flex flex-wrap items-center gap-2 mt-2 text-sm text-white/80">
            {uploader ? <span>{uploader}</span> : null}
            {uploader && resolvedPlatform ? (
              <span className="opacity-50">·</span>
            ) : null}
            {resolvedPlatform ? <span>{resolvedPlatform}</span> : null}
          </div>
        </div>
        {videoUrl ? (
          <a
            href={videoUrl}
            target="_blank"
            rel="noreferrer"
            className="relative z-10 shrink-0 inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 text-white text-sm transition-colors whitespace-nowrap font-medium shadow-sm"
          >
            打开原片
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : null}
      </div>
    </div>
  );
}
