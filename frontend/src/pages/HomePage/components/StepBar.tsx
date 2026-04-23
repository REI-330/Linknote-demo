type Step = {
  label: string;
  key: string;
};

interface StepBarProps {
  steps: Step[];
  currentStep: string;
}

export default function StepBar({ steps, currentStep }: StepBarProps) {
  const activeIndex = Math.max(
    0,
    steps.findIndex((step) => step.key === currentStep)
  );

  return (
    <div className="bn-stepbar">
      {steps.map((step, index) => {
        const isActive = index <= activeIndex;
        const isLast = index === steps.length - 1;

        return (
          <div key={step.key} className="bn-stepbar-item">
            <div className={isActive ? "bn-stepbar-dot active" : "bn-stepbar-dot"}>{index + 1}</div>
            <div className="bn-stepbar-label">{step.label}</div>
            {!isLast ? <div className={isActive ? "bn-stepbar-line active" : "bn-stepbar-line"} /> : null}
          </div>
        );
      })}
    </div>
  );
}
