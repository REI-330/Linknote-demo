import { useEffect, useMemo, useRef, useState } from "react";
import { Download } from "lucide-react";
import { Transformer } from "markmap-lib";
import { Markmap } from "markmap-view";

type MarkmapViewProps = {
  markdown: string;
  exportFilename?: string;
  onExportSvgChange?: (svgMarkup: string | null) => void;
};

function serializeSvg(svg: SVGSVGElement) {
  const clone = svg.cloneNode(true) as SVGSVGElement;

  if (!clone.getAttribute("xmlns")) {
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  }

  if (!clone.getAttribute("viewBox")) {
    const width = svg.viewBox.baseVal.width || svg.clientWidth || 1200;
    const height = svg.viewBox.baseVal.height || svg.clientHeight || 720;
    clone.setAttribute("viewBox", `0 0 ${width} ${height}`);
  }

  return new XMLSerializer().serializeToString(clone);
}

function downloadSvg(filename: string, svgMarkup: string) {
  const blob = new Blob([svgMarkup], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();

  window.setTimeout(() => URL.revokeObjectURL(url), 30000);
}

export function MarkmapView({
  markdown,
  exportFilename = "mindmap.svg",
  onExportSvgChange,
}: MarkmapViewProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const markmapRef = useRef<Markmap | null>(null);
  const [isReady, setIsReady] = useState(false);

  const transformed = useMemo(() => {
    const transformer = new Transformer();
    return transformer.transform(markdown);
  }, [markdown]);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) {
      return;
    }

    if (!markmapRef.current) {
      markmapRef.current = Markmap.create(svg);
    }

    markmapRef.current.setData(transformed.root);
    markmapRef.current.fit();

    const frame = window.requestAnimationFrame(() => {
      const liveSvg = svgRef.current;
      if (!liveSvg) {
        setIsReady(false);
        onExportSvgChange?.(null);
        return;
      }

      const hasGraph = Boolean(liveSvg.querySelector("g"));
      setIsReady(hasGraph);
      onExportSvgChange?.(hasGraph ? serializeSvg(liveSvg) : null);
    });

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [onExportSvgChange, transformed]);

  useEffect(() => {
    return () => {
      onExportSvgChange?.(null);
    };
  }, [onExportSvgChange]);

  function handleExport() {
    const liveSvg = svgRef.current;
    if (!liveSvg) {
      window.alert("思维导图尚未准备完成，请稍后再试。");
      return;
    }

    const svgMarkup = serializeSvg(liveSvg);
    if (!svgMarkup.includes("<svg")) {
      window.alert("思维导图导出失败，请重试。");
      return;
    }

    downloadSvg(exportFilename, svgMarkup);
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-end">
        <button
          type="button"
          className="ln-action-button px-4 py-2 text-sm"
          disabled={!isReady}
          onClick={handleExport}
        >
          <Download className="h-4 w-4" />
          导出导图
        </button>
      </div>

      <div className="overflow-hidden rounded-[1.4rem] border border-border/45 bg-[linear-gradient(180deg,rgba(243,248,253,0.92),rgba(255,255,255,0.96))] p-4 shadow-[0_26px_60px_-40px_rgba(19,49,94,0.22)]">
        <div className="overflow-auto rounded-[1rem] bg-white/86">
          <svg
            ref={svgRef}
            data-markmap-export="true"
            className="min-h-[32rem] min-w-[960px]"
          />
        </div>
      </div>
    </section>
  );
}
