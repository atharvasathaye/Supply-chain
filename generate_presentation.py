import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def create_presentation():
    # Load the user's provided template
    template_path = r"C:\Users\athar\OneDrive - MSFT\Documents\UIUC SEM 3\ABR\Salud Revenue Partners x BIG.pptx"
    
    try:
        prs = Presentation(template_path)
    except Exception as e:
        print(f"Could not load template: {e}")
        prs = Presentation() # fallback

    # Use the first available layout (usually the master theme background)
    layout = prs.slide_layouts[0]

    def add_slide_with_content(title_text, bullet_points):
        slide = prs.slides.add_slide(layout)
        
        # We delete default placeholders from this layout to ensure a clean slate 
        # while keeping the template's background/theme
        for sp in slide.shapes:
            sp.element.getparent().remove(sp.element)
        
        # Add Title Box
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(1))
        tf = title_box.text_frame
        p = tf.add_paragraph()
        p.text = title_text
        p.font.size = Pt(36)
        p.font.bold = True
        
        # Add Content Box
        body_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(9), Inches(5))
        tf_body = body_box.text_frame
        tf_body.word_wrap = True
        
        for pt in bullet_points:
            p = tf_body.add_paragraph()
            p.text = pt
            p.font.size = Pt(24)
            p.space_after = Pt(14)
            
    # Slide 1: Title
    add_slide_with_content("Supply Chain Pressure vs. Inflation", ["A Predictive Machine Learning Analysis", "Ready for Client Presentation"])

    # Slide 2: Introduction
    add_slide_with_content("Introduction & Business Goal", [
        "The global economy is highly interconnected.",
        "Goal: Prove that supply chain bottlenecks act as a leading indicator for consumer inflation.",
        "Data Sources: Federal Reserve (CPI) and NY Fed (Global Supply Chain Pressure Index).",
        "Deliverables: Data pipeline, statistical proofs, and an interactive ML dashboard."
    ])

    # Slide 3: Background & Analogy
    add_slide_with_content("Background: The 'Traffic Jam' Analogy", [
        "When an accident occurs (supply chain shock), traffic doesn't stop immediately miles back.",
        "It takes time for the ripple effect to hit the cars behind (the consumers).",
        "In economics, a shipping delay takes 1-6 months to cause price hikes in retail stores.",
        "This delay creates a window where we can predict future inflation before it happens."
    ])

    # Slide 4: Methodology
    add_slide_with_content("Methodology & Architecture", [
        "1. Automated Data Engineering Pipeline: Fetches live data via APIs.",
        "2. Statistical Proof (Granger Causality): Confirmed GSCPI changes precede CPI changes.",
        "3. Machine Learning Forecasting (VAR Model): Predicts inflation 6 months out.",
        "4. MLOps: Dockerized Streamlit app with GitHub Actions for automated updates."
    ])

    # Slide 5: Conclusion
    add_slide_with_content("Conclusion & Business Impact", [
        "Physical goods (Vehicles, Food) react violently to supply shocks.",
        "Business Impact: Companies can adjust pricing strategies months before inflation hits their P&L.",
        "This architecture demonstrates full-stack data capabilities from engineering to machine learning."
    ])

    # Save
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "Project_Presentation_Client_Ready.pptx")
    prs.save(output_path)
    print(f"Presentation saved to {output_path}")

if __name__ == '__main__':
    create_presentation()
