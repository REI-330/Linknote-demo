import { useEffect, useRef } from "react";
import { Transformer } from "markmap-lib";
import { Markmap } from "markmap-view";

const transformer = new Transformer();

interface MarkmapViewProps {
  markdown: string;
}

export function MarkmapView({ markdown }: MarkmapViewProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) {
      return;
    }
    const { root } = transformer.transform(markdown || "# 空笔记");
    const markmap = Markmap.create(svg);
    markmap.setData(root);
    markmap.fit();
    return () => {
      svg.innerHTML = "";
    };
  }, [markdown]);

  return <svg ref={svgRef} className="markmap-canvas" />;
}
