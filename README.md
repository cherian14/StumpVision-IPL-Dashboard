# StumpVision-IPL-Dashboard
An interactive IPL analytics dashboard powered by Python &amp; Streamlit, uncovering player performance with advanced metrics beyond the scorecard.

# 🏏 StumpVision: The Ultimate IPL Analytics Dashboard

Ever argued about who the *real* MVP of the IPL is? StumpVision settles the debate with data, going beyond basic scores and averages to deliver deep, actionable insights into player and team performance. This interactive dashboard, built with Python and Streamlit, is a one-stop-shop for fans, analysts, and recruiters looking to see data science in action.

![Dashboard Demo GIF](URL_TO_YOUR_SCREENSHOT_OR_GIF_HERE) 
*(Pro-tip: Record a short GIF of you using the dashboard and upload it to the repository to place here. It dramatically increases engagement!)*

## ✨ Key Features & Advanced Metrics

This isn't just another scorecard. StumpVision uses robust feature engineering to calculate metrics that tell the true story:

*   📊 **Interactive Visualizations:** All charts and graphs are powered by Plotly for a dynamic, user-friendly experience.
*   👑 **True Performance Metrics:**
    *   **True Average & True Strike Rate:** Normalizes a batsman's performance against the difficulty of the match, revealing who truly excels under pressure.
    *   **Combined Bowling Rate (CBR):** A single, powerful metric derived from the harmonic mean of a bowler's average, economy, and strike rate.
*   🔬 **Player Deep-Dive:** Select any player from IPL history to see a comprehensive breakdown of their batting and bowling statistics.
*   ♟️ **Phase-Wise Analysis:** Analyze team and player performance across the three critical phases of a T20 match: the **Powerplay**, **Middle Overs**, and **Death Overs**.
*   🏆 **Team Analytics:** View overall win percentages, head-to-head stats, and the impact of the coin toss on match outcomes.

## 🛠️ Tech Stack

This project showcases a modern data science workflow using industry-standard tools:

*   **Language:** Python
*   **Data Manipulation & Analysis:** Pandas, NumPy
*   **Interactive Dashboard:** Streamlit
*   **Data Visualization:** Plotly Express
*   **Machine Learning (for potential future prediction features):** Scikit-learn

## 🚀 Getting Started

You can run this dashboard on your local machine in just a few steps.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/[Your-GitHub-Username]/StumpVision-IPL-Dashboard.git
    cd StumpVision-IPL-Dashboard
    ```

2.  **Create a virtual environment & install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
    *(Note: You will need to create a `requirements.txt` file by running `pip freeze > requirements.txt` in your terminal.)*

3.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

Your browser should automatically open with the dashboard running!
