const examples = [
  "Compare YOLOv5, YOLOv8 and YOLO11 for small object detection.",
  "What machine learning models perform best for house price prediction?",
  "Compare CNN and Vision Transformers for image classification.",
];

function ExampleQueries() {
  return (
    <section className="examples">
      <div className="examples-title">TRY AN EXAMPLE</div>

      {examples.map((example, index) => (
        <button className="example-item" key={example}>
          <span className="example-number">
            0{index + 1}
          </span>

          <span className="example-text">
            {example}
          </span>

          <span className="example-arrow">↗</span>
        </button>
      ))}
    </section>
  );
}

export default ExampleQueries;