import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_preview():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "merged_data_for_bi.csv")
    
    if not os.path.exists(file_path):
        return

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Use a clean style
    plt.style.use('ggplot')
    
    fig, ax1 = plt.subplots(figsize=(12, 6))

    color1 = '#2980B9' # Blue for GSCPI
    ax1.set_xlabel('Date', fontweight='bold')
    ax1.set_ylabel('Supply Chain Pressure (GSCPI)', color=color1, fontweight='bold')
    ax1.plot(df['date'], df['gscpi'], color=color1, linewidth=2.5, label='GSCPI')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Fill under the curve
    ax1.fill_between(df['date'], df['gscpi'], color=color1, alpha=0.1)

    ax2 = ax1.twinx()
    color2 = '#C0392B' # Red for Inflation
    ax2.set_ylabel('US CPI Inflation YoY (%)', color=color2, fontweight='bold')
    ax2.plot(df['date'], df['cpi_yoy'], color=color2, linewidth=2.5, linestyle='--', label='CPI YoY')
    ax2.tick_params(axis='y', labelcolor=color2)

    plt.title('Global Supply Chain Disruptions vs. US Inflation', fontsize=16, fontweight='bold', pad=20)
    
    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')
    
    fig.tight_layout()
    plt.savefig(os.path.join(base_dir, 'preview.png'), dpi=300, bbox_inches='tight')

if __name__ == "__main__":
    generate_preview()
