from pptx import Presentation
import os

def create_presentation():
    # Use the default, clean PowerPoint template
    prs = Presentation()

    # Title Slide (Layout 0)
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Supply Chain Pressure vs. Inflation"
    subtitle.text = "A Predictive Machine Learning Analysis\nBy Atharva Sathaye"

    # Bullet Slide Layout (Layout 1)
    bullet_slide_layout = prs.slide_layouts[1]

    # Slide 1: Introduction
    slide = prs.slides.add_slide(bullet_slide_layout)
    title_shape = slide.shapes.title
    body_shape = slide.placeholders[1]
    title_shape.text = "Introduction & Goal"
    tf = body_shape.text_frame
    tf.text = "The modern global economy is highly interconnected."
    p = tf.add_paragraph()
    p.text = "Goal: Investigate if supply chain bottlenecks act as a leading indicator for consumer inflation."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Data Sources: Federal Reserve (CPI) and NY Fed (GSCPI)."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Deliverables: Data pipeline, statistical proofs, and an interactive ML dashboard."
    p.level = 1

    # Slide 2: Background Research & Analogy
    slide = prs.slides.add_slide(bullet_slide_layout)
    title_shape = slide.shapes.title
    body_shape = slide.placeholders[1]
    title_shape.text = "Background & Analogy"
    tf = body_shape.text_frame
    tf.text = "Analogy: A traffic jam on a highway."
    p = tf.add_paragraph()
    p.text = "When an accident occurs (supply chain shock), traffic doesn't stop immediately miles back."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "It takes time for the ripple effect to hit the cars behind (the consumers)."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "A shipping delay takes 1-6 months to cause price hikes in US stores."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "This delay creates a window to predict future inflation."
    p.level = 1

    # Slide 3: Methodology
    slide = prs.slides.add_slide(bullet_slide_layout)
    title_shape = slide.shapes.title
    body_shape = slide.placeholders[1]
    title_shape.text = "Methodology & Architecture"
    tf = body_shape.text_frame
    tf.text = "1. Automated Data Engineering Pipeline"
    p = tf.add_paragraph()
    p.text = "Python scripts fetch live data via APIs and normalize dates."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "2. Statistical Proof (Granger Causality)"
    p = tf.add_paragraph()
    p.text = "Statistically proved that GSCPI changes precede CPI changes (p-values < 0.05)."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "3. ML Forecasting (VAR Model)"
    p = tf.add_paragraph()
    p.text = "Vector Autoregression predicts inflation 6 months into the future."
    p.level = 1

    # Slide 4: Conclusion
    slide = prs.slides.add_slide(bullet_slide_layout)
    title_shape = slide.shapes.title
    body_shape = slide.placeholders[1]
    title_shape.text = "Conclusion & Impact"
    tf = body_shape.text_frame
    tf.text = "Supply chains are mathematical predictors of inflation."
    p = tf.add_paragraph()
    p.text = "Physical goods (Vehicles, Food) react violently to supply shocks."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Business Impact:"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "Companies can adjust pricing strategies months before inflation hits their P&L."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Demonstrates full-stack data capabilities from engineering to machine learning."
    p.level = 1

    # Save
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "Supply_Chain_Presentation.pptx")
    prs.save(output_path)
    print(f"Presentation saved to {output_path}")

if __name__ == '__main__':
    create_presentation()
