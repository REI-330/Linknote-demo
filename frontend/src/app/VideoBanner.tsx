interface VideoBannerProps {
  title: string;
  uploader?: string;
  platform?: string;
  coverUrl?: string;
  videoUrl?: string;
}

const platformLabel: Record<string, string> = {
  bilibili: "哔哩哔哩",
  youtube: "YouTube",
  douyin: "抖音",
  xiaohongshu: "小红书"
};

export function VideoBanner({ title, uploader = "", platform = "", coverUrl = "", videoUrl = "" }: VideoBannerProps) {
  const resolvedPlatform = platformLabel[platform] || platform || "";

  return (
    <div className="video-banner">
      <div className="video-banner-backdrop">
        {coverUrl ? <img src={coverUrl} alt="" /> : <div className="video-banner-fallback" />}
      </div>
      <div className="video-banner-content">
        {coverUrl ? <img className="video-banner-cover" src={coverUrl} alt={title} /> : null}
        <div className="video-banner-copy">
          <h3 title={title}>{title}</h3>
          <p>
            {uploader ? <span>{uploader}</span> : null}
            {uploader && resolvedPlatform ? <span className="video-banner-dot">·</span> : null}
            {resolvedPlatform ? <span>{resolvedPlatform}</span> : null}
          </p>
        </div>
        {videoUrl ? (
          <a className="video-banner-link" href={videoUrl} target="_blank" rel="noreferrer">
            打开原片
          </a>
        ) : null}
      </div>
    </div>
  );
}
