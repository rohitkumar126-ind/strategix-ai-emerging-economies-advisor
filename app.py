from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
from google import genai
import markdown
import re
import pandas as pd

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

# Load real per-capita income data (recent years sheet = second sheet in the file) once when the app starts
income_df = pd.read_excel('data/per_capita_income.xls.XLSX', sheet_name=1, header=None, skiprows=5)
income_df = income_df.iloc[:, 1:]
income_df.columns = ['State', '2017-18', '2018-19', '2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']
income_df['State'] = income_df['State'].astype(str).str.strip()

CITY_TO_STATE = {
    'bangalore': 'karnataka', 'bengaluru': 'karnataka', 'mysuru': 'karnataka',
    'mumbai': 'maharashtra', 'pune': 'maharashtra', 'nagpur': 'maharashtra',
    'delhi': 'delhi', 'new delhi': 'delhi', 'gurugram': 'haryana', 'gurgaon': 'haryana',
    'patna': 'bihar', 'motihari': 'bihar', 'gaya': 'bihar', 'muzaffarpur': 'bihar', 'siwan': 'bihar',
    'lucknow': 'uttar pradesh', 'kanpur': 'uttar pradesh', 'varanasi': 'uttar pradesh', 'noida': 'uttar pradesh',
    'chennai': 'tamil nadu', 'coimbatore': 'tamil nadu',
    'hyderabad': 'telangana', 'kolkata': 'west bengal',
    'ahmedabad': 'gujarat', 'surat': 'gujarat',
    'jaipur': 'rajasthan', 'ranchi': 'jharkhand', 'bhopal': 'madhya pradesh', 'indore': 'madhya pradesh',
}

def get_state_income_data(region_name):
    """Look up real per-capita income data for a given state or city name."""
    search_term = region_name.strip().lower()
    search_term = CITY_TO_STATE.get(search_term, search_term)

    for state_name in income_df['State'].dropna().unique():
        if search_term in state_name.lower() or state_name.lower() in search_term:
            row = income_df[income_df['State'] == state_name].iloc[0]
            latest_col = income_df.columns[-1]
            prev_col = income_df.columns[-2]
            return f"Per Capita Net State Domestic Product for {state_name} — Latest available year ({latest_col}): ₹{row[latest_col]}, Previous year ({prev_col}): ₹{row[prev_col]} (Source: RBI Handbook of Statistics on Indian States)"

    return "No official per-capita income data found for this exact region — analysis based on general market knowledge."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    industry = request.form['industry']
    region = request.form['region']
    objective = request.form['objective']

    real_data_context = get_state_income_data(region)

    prompt = f"""
    You are Strategix AI — Market Entry & Business Strategy Advisor for Emerging Markets.

    A company wants to {objective} in the {industry} industry, targeting {region}, India.

    REAL DATA CONTEXT (use this actual figure in your analysis, cite it explicitly):
    {real_data_context}

    Provide a structured strategy report with this exact format (include the emojis exactly as shown in each heading):

    **To:** Executive Leadership Team  
    **From:** Strategix AI — Market Entry & Business Strategy Advisor for Emerging Markets  
    **Subject:** Market Entry Strategy for {region} ({industry})

    ## 📊 1. Market Attractiveness (Score out of 10)
    [analysis — reference the real per-capita income figure provided above where relevant]
    **💡 Tactical Tip:** [one practical, actionable tip specific to this section]

    ## 🏁 2. Competitive Landscape
    [analysis]
    **💡 Tactical Tip:** [one practical, actionable tip]

    ## 💰 3. Pricing Recommendation
    [analysis, use a markdown table]
    **💡 Tactical Tip:** [one practical, actionable tip]

    ## 🚚 4. Entry-Mode Suggestion
    [analysis]
    **💡 Tactical Tip:** [one practical, actionable tip]

    ## ⚠️ 5. Key Risk Factors
    [analysis with mitigation]
    **💡 Tactical Tip:** [one practical, actionable tip]

    ## 🗓️ 6. 90-Day Go-to-Market Action Plan
    [a practical, phased roadmap, use a markdown table with columns: Phase, Timeline, Key Actions]
    **💡 Tactical Tip:** [one practical, actionable tip]

    Keep it concise, practical, and specific to the Indian market context. Use only standard Markdown tables, never ASCII box characters. Do not use asterisk bullet points (*) — use proper Markdown bullets with a dash (-) instead.
    """

    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )

    raw_html = markdown.markdown(response.text, extensions=['tables'])

    parts = re.split(r'(?=<h2>)', raw_html)
    header_block = parts[0]
    sections = parts[1:]

    sections_html = ""
    for section in sections:
        css_class = "section-card wide" if "<table" in section else "section-card"
        sections_html += f'<div class="{css_class}">{section}</div>'

    styled_page = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Strategix AI Report</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background: #eef1f8;
                min-height: 100vh;
                color: #1a1a2e;
            }}
            .top-header {{
                background: #1a1a2e;
                padding: 30px 40px;
                text-align: center;
            }}
            .top-header h1 {{
                font-size: 26px;
                color: white;
                letter-spacing: 1px;
            }}
            .top-header p {{
                color: #a0a0c0;
                margin-top: 6px;
                font-size: 14px;
            }}
            .data-badge {{
                display: inline-block;
                background: #22c55e;
                color: white;
                font-size: 12px;
                padding: 4px 12px;
                border-radius: 20px;
                margin-top: 10px;
            }}
            .content-wrap {{
                width: 100%;
                padding: 30px 5%;
            }}
            .header-block {{
                background: white;
                padding: 22px 28px;
                border-radius: 12px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06);
                font-size: 14px;
                color: #444;
            }}
            .header-block p {{ margin-bottom: 6px; line-height: 1.8; }}
            .header-block strong {{ color: #1a1a2e; }}
            .grid-sections {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }}
            .section-card {{
                background: white;
                border-radius: 14px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.07);
                overflow: hidden;
            }}
            .section-card.wide {{
                grid-column: 1 / -1;
            }}
            .section-card h2 {{
                color: white;
                background: linear-gradient(90deg, #4a4ae0, #7b6cf6);
                font-size: 16px;
                margin: 0;
                padding: 16px 22px;
            }}
            .section-card p {{
                padding: 0 22px;
                margin: 16px 0;
                line-height: 1.75;
                color: #333;
                font-size: 14.5px;
            }}
            .section-card ul {{
                padding: 0 22px 0 42px;
                margin: 10px 0;
                color: #333;
                font-size: 14.5px;
                line-height: 1.7;
            }}
            .section-card p:last-child {{ padding-bottom: 22px; }}
            .section-card strong {{ color: #4a4ae0; }}
            .section-card table {{
                border-collapse: collapse;
                width: calc(100% - 44px);
                margin: 15px 22px;
                font-size: 14px;
            }}
            .section-card th, .section-card td {{
                padding: 12px 14px;
                text-align: left;
                border-bottom: 1px solid #eee;
                white-space: normal;
                word-break: normal;
            }}
            .section-card th {{
                background-color: #1a1a2e;
                color: white;
            }}
            .section-card tr:nth-child(even) {{ background-color: #f6f6fc; }}
            a.back-link {{
                display: inline-block;
                margin-top: 25px;
                padding: 12px 24px;
                background: #1a1a2e;
                color: white;
                text-decoration: none;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
            }}
            a.back-link:hover {{ background: #4a4ae0; }}
        </style>
    </head>
    <body>
        <div class="top-header">
            <h1>STRATEGIX AI</h1>
            <p>Market Entry & Business Strategy Advisor for Emerging Economies</p>
            <div class="data-badge">✓ Grounded in RBI Official Data</div>
        </div>
        <div class="content-wrap">
            <div class="header-block">{header_block}</div>
            <div class="grid-sections">
                {sections_html}
            </div>
            <a class="back-link" href="/">← Generate Another Report</a>
        </div>
    </body>
    </html>
    """

    return styled_page

if __name__ == '__main__':
    app.run(debug=True)